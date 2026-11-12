# 04. Especificação de Contratos da API RESTful (FastAPI)

**Projeto:** Peito Infinity  
**Documento:** Endpoints HTTP, Payloads JSON, Validações Pydantic e Tratamento de Erros  
**Status:** Especificação Base (SDD)  

---

## 1. Convenções Gerais da API

- **Base URL:** `/api/v1`
- **Formato de Dados:** `application/json` (UTF-8)
- **Autenticação:** **Nenhuma** (execução em rede doméstica e privada conforme requisito constitucional).
- **Documentação Automática:** Exposta nativamente pelo FastAPI em `/docs` (Swagger UI) e `/redoc`.
- **Identificadores:** Todos os recursos primários utilizam `UUID v4`.

---

## 2. Mapa de Endpoints

| Método | Rota | Resumo da Operação | Código Sucesso |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/health` | Verifica saúde da API, conexão com PostgreSQL e contagem de exercícios no banco. | `200 OK` |
| `GET` | `/api/v1/exercises` | Lista todos os exercícios cadastrados no banco PostgreSQL (agrupáveis por músculo). | `200 OK` |
| `GET` | `/api/v1/profiles` | Lista todos os perfis de usuário disponíveis na tela inicial. | `200 OK` |
| `POST` | `/api/v1/profiles` | Cria um novo perfil de usuário (sem autenticação). | `201 Created` |
| `GET` | `/api/v1/profiles/{profile_id}` | Obtém detalhes completos do perfil, IDs de exercícios excluídos e o treino ativo. | `200 OK` |
| `PUT` | `/api/v1/profiles/{profile_id}` | Edita os dados de um perfil existente. | `200 OK` |
| `DELETE` | `/api/v1/profiles/{profile_id}` | Remove um perfil e seus treinos associados. | `204 No Content` |
| `PUT` | `/api/v1/profiles/{profile_id}/excluded-exercises` | Atualiza a lista de exercícios excluídos pelo usuário. | `200 OK` |
| `POST` | `/api/v1/profiles/{profile_id}/workouts/generate-full` | Aciona o Agente LLM para gerar **todo o treinamento semanal do zero** (respeitando exclusões). | `201 Created` |
| `POST` | `/api/v1/profiles/{profile_id}/workouts/days/{day_number}/regenerate` | Aciona o Agente LLM para gerar **apenas um novo treino para aquele dia específico** (`day_number`). | `200 OK` |

---

## 3. Especificação Detalhada dos Contratos

### 3.1 Catálogo de Exercícios (Fonte: PostgreSQL)

#### `GET /api/v1/exercises`
Retorna os exercícios diretamente do banco PostgreSQL para exibição e para o modal pré-geração de exclusão de exercícios.

- **Query Parameters Opcionais:**
  - `muscle_group` (string): Filtra por grupo muscular específico.
  - `complexity` (`BAIXA` | `MEDIA` | `ALTA`): Filtra por complexidade.
  - `search` (string): Busca textual parcial em `popular_name` ou `primary_muscle`.

- **Response `200 OK`:**
```json
{
  "total": 89,
  "groups": [
    {
      "group_order": 1,
      "muscle_group": "Peitoral (Peito)",
      "exercises": [
        {
          "id": "b1a8c3e0-1111-4444-8888-000000000001",
          "popular_name": "Supino Reto com Halteres",
          "primary_muscle": "Peitoral Maior (Porção Esternal)",
          "secondary_muscles": "Tríceps, Deltoide Anterior",
          "complexity": "MEDIA",
          "efficiency_score": 9.8
        }
      ]
    }
  ]
}
```

---

### 3.2 Gerenciamento de Perfis de Usuário (Sem Autenticação)

#### `POST /api/v1/profiles` e `PUT /api/v1/profiles/{profile_id}`
Cria ou edita os dados do perfil diretamente pela interface do aplicativo.

- **Request Body (`ProfileCreateUpdateRequest`):**
```json
{
  "name": "Rodrigo Mendes",
  "weight_kg": 84.5,
  "height_cm": 179.0,
  "fitness_level": "INTERMEDIARIO",
  "goal": "HIPERTROFIA",
  "available_time_minutes": 60,
  "days_per_week": 4
}
```

- **Regras de Validação do Payload:**
  - `name`: String não vazia (`min_length=2`, `max_length=80`).
  - `weight_kg`: Float (`>= 25.0`, `<= 300.0`).
  - `height_cm`: Float (`>= 100.0`, `<= 250.0`).
  - `fitness_level`: Enum `["INICIANTE", "INTERMEDIARIO", "AVANCADO"]`.
  - `goal`: Enum `["EMAGRECIMENTO", "HIPERTROFIA", "FORCA"]`.
  - `available_time_minutes`: Integer (`>= 20`, `<= 240`).
  - `days_per_week`: Integer (`>= 1`, `<= 7`).

- **Response `201 Created` / `200 OK` (`ProfileResponse`):**
```json
{
  "id": "9f8e7d6c-5b4a-3210-fedc-ba9876543210",
  "name": "Rodrigo Mendes",
  "weight_kg": 84.5,
  "height_cm": 179.0,
  "bmi": 26.37,
  "fitness_level": "INTERMEDIARIO",
  "goal": "HIPERTROFIA",
  "available_time_minutes": 60,
  "days_per_week": 4,
  "excluded_exercise_ids": [],
  "has_active_workout": false,
  "created_at": "2026-11-11T20:00:00Z",
  "updated_at": "2026-11-11T20:00:00Z"
}
```

---

### 3.3 Geração de Treinamento Completo do Zero (Agente LLM)

#### `POST /api/v1/profiles/{profile_id}/workouts/generate-full`
Antes de chamar este endpoint, o front-end apresenta ao usuário o modal de exclusão de exercícios. O payload recebe a lista de exercícios que o usuário deseja excluir da montagem do treino.

- **Request Body (`GenerateFullWorkoutRequest`):**
```json
{
  "excluded_exercise_ids": [
    "b1a8c3e0-1111-4444-8888-000000000003",
    "b1a8c3e0-1111-4444-8888-000000000027"
  ]
}
```

- **Comportamento no Back-end:**
  1. Persiste `excluded_exercise_ids` na tabela `profile_excluded_exercises` para o perfil.
  2. Consulta no PostgreSQL todos os exercícios `WHERE id NOT IN (excluded_exercise_ids)`.
  3. Invoca o Agente LLM Especialista passando os dados atuais do perfil e os exercícios permitidos.
  4. Recebe o plano completo estruturado com exatamente `days_per_week` dias.
  5. Valida que nenhum exercício retornado pertence a `excluded_exercise_ids` e que `cardio_display_text` segue o padrão `"{X} min de cardio"`.
  6. Desativa planos anteriores do perfil (`is_active = FALSE`) e grava o novo plano como ativo (`is_active = TRUE`).

- **Response `201 Created` (`WorkoutPlanResponse`):**
```json
{
  "id": "c7d8e9f0-1234-5678-9abc-def012345678",
  "profile_id": "9f8e7d6c-5b4a-3210-fedc-ba9876543210",
  "split_name": "Upper / Lower (4 Dias - Foco Hipertrofia)",
  "specialist_notes": "Divisão Superior/Inferior ideal para 4 dias na semana e sessões de 60 minutos, priorizando multiarticulares de alta eficiência no início e isoladores guiados ao final.",
  "days_per_week_snapshot": 4,
  "time_minutes_snapshot": 60,
  "goal_snapshot": "HIPERTROFIA",
  "created_at": "2026-11-11T20:10:00Z",
  "updated_at": "2026-11-11T20:10:00Z",
  "days": [
    {
      "id": "d1000000-0000-4000-8000-000000000001",
      "day_number": 1,
      "day_title": "Dia 1 — Membros Superiores A (Foco Peito e Costas)",
      "target_muscles": "Peitoral, Dorsais, Deltoide Lateral, Bíceps e Tríceps",
      "estimated_duration_minutes": 60,
      "cardio_minutes": 15,
      "cardio_display_text": "15 min de cardio",
      "updated_at": "2026-11-11T20:10:00Z",
      "exercises": [
        {
          "execution_order": 1,
          "exercise_id": "b1a8c3e0-1111-4444-8888-000000000001",
          "popular_name": "Supino Reto com Halteres",
          "muscle_group": "Peitoral (Peito)",
          "primary_muscle": "Peitoral Maior (Porção Esternal)",
          "complexity": "MEDIA",
          "efficiency_score": 9.8,
          "sets": 4,
          "reps": "8 a 10",
          "rest_seconds": 90,
          "execution_notes": "Alongar bem na descida mantendo escápulas retraídas."
        },
        {
          "execution_order": 2,
          "exercise_id": "b1a8c3e0-1111-4444-8888-000000000018",
          "popular_name": "Remada Cavalinho (Barra T c/ Apoio no Peito)",
          "muscle_group": "Costas (Dorsais e Parte Superior das Costas)",
          "primary_muscle": "Trapézio Médio, Romboides, Dorsal",
          "complexity": "BAIXA",
          "efficiency_score": 9.8,
          "sets": 4,
          "reps": "8 a 12",
          "rest_seconds": 90,
          "execution_notes": "Focar na retração escapular no topo do movimento."
        }
      ]
    }
  ]
}
```

---

### 3.4 Regeneração de Treino de um Dia Específico (Agente LLM)

#### `POST /api/v1/profiles/{profile_id}/workouts/days/{day_number}/regenerate`
Permite que o usuário gere um novo treino **apenas para aquele dia específico** (`day_number` de `1` a `N`), mantendo os outros dias do treinamento intactos. Assim como na geração completa, recebe a lista revisada de exercícios excluídos.

- **Path Parameters:**
  - `profile_id` (`UUID`): ID do perfil.
  - `day_number` (`int`): Número do dia a ser regenerado (`1` a `7`).

- **Request Body (`RegenerateWorkoutDayRequest`):**
```json
{
  "excluded_exercise_ids": [
    "b1a8c3e0-1111-4444-8888-000000000001",
    "b1a8c3e0-1111-4444-8888-000000000003"
  ]
}
```

- **Comportamento no Back-end:**
  1. Atualiza a lista `profile_excluded_exercises` do perfil.
  2. Busca o plano de treino ativo (`is_active = TRUE`) e localiza o `workout_day` correspondente a `day_number`.
  3. Carrega o resumo dos demais dias do plano (para que o Agente LLM mantenha a mesma divisão muscular do dia regenerado e não duplique estímulos indevidos).
  4. Invoca o Agente LLM Especialista para gerar um **novo treino apenas para o `day_number`**, usando somente os exercícios permitidos do PostgreSQL e propondo variações em relação aos exercícios que estavam anteriormente naquele dia.
  5. Substitui os registros de `workout_day_exercises` e atualiza os campos de `workout_days` apenas para o `day_number` informado.
  6. Retorna o plano atualizado (`200 OK`).

---

## 4. Padronização de Erros da API

| Código HTTP | `error_code` | Cenário |
| :--- | :--- | :--- |
| `400 Bad Request` | `INSUFFICIENT_ALLOWED_EXERCISES` | Usuário excluiu quase todos os exercícios do banco, restando quantidade insuficiente para montar o treino. |
| `404 Not Found` | `PROFILE_NOT_FOUND` / `WORKOUT_DAY_NOT_FOUND` | Perfil ou dia de treino solicitado não existe. |
| `422 Unprocessable Entity` | `VALIDATION_ERROR` | Dados do perfil fora dos intervalos permitidos (ex: minutos `< 20` ou dias `> 7`). |
| `502 Bad Gateway` | `LLM_PROVIDER_ERROR` | Falha de comunicação ou timeout com o provedor de LLM configurado. |

- **Formato Padrão de Erro:**
```json
{
  "error_code": "INSUFFICIENT_ALLOWED_EXERCISES",
  "message": "Você excluiu exercícios demais em grupos musculares essenciais. Mantenha ao menos 2 exercícios por grupo muscular para gerar o treino.",
  "details": {}
}
```
