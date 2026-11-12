# 05. Especificação do Agente LLM Especialista em Montar Treinos

**Projeto:** Peito Infinity  
**Documento:** Arquitetura do Agente IA, Engenharia de Prompt, Matriz Fisiológica e Guardrails  
**Status:** Especificação Base (SDD)  

---

## 1. Papel e Identidade do Agente LLM

O **Agente LLM Especialista do Peito Infinity** é um módulo determinístico-assistido no back-end Python que atua como um **Treinador Especialista em Fisiologia do Exercício, Biomecânica e Musculação Baseada em Evidências**.

O agente **não inventa nomes de exercícios**: ele opera exclusivamente sobre o catálogo de exercícios recuperado do banco de dados **PostgreSQL** (após a filtragem estrita dos exercícios excluídos pelo usuário) e devolve uma estrutura JSON validada por schema (`Structured Outputs`).

---

## 2. Matriz de Prescrição Fisiológica do Agente

O Agente LLM utiliza os parâmetros do perfil do usuário para calibrar automaticamente volume, intensidade, descanso, divisão semanal (*split*) e tempo de cardio:

### 2.1 Parametrização por Objetivo (`goal`)

| Objetivo | Faixa de Repetições | Descanso entre Séries | Prioridade de Exercícios | Prescrição de Cardio (`"{X} min de cardio"`) |
| :--- | :--- | :--- | :--- | :--- |
| **`EMAGRECIMENTO`** | `10 a 15` reps | `45s a 75s` (maior densidade metabólica) | Multiarticulares de alto gasto energético + isoladores de alta eficiência | **Alta prioridade:** `20 min de cardio` a `45 min de cardio` por sessão (ex: `"40 min de cardio"`), ajustado ao tempo total disponível. |
| **`HIPERTROFIA`** | `6 a 12` reps (compostos) / `10 a 15` reps (isoladores) | `60s a 120s` | Exercícios com maior **Nota de Eficiência (`efficiency_score >= 9.0`)** e grande alongamento sob tensão | **Moderada:** `10 min de cardio` a `25 min de cardio` (ex: `"15 min de cardio"` ou `"20 min de cardio"`). |
| **`FORCA` (Treino de Força)** | `3 a 6` reps (principais) / `6 a 10` reps (acessórios) | `120s a 180s` (recuperação neural completa) | Compostos livres/guiados de complexidade `ALTA` e `MEDIA` no início + acessórios de suporte | **Baixa/Condicionamento Base:** `10 min de cardio` a `15 min de cardio` (ex: `"10 min de cardio"`). |

---

### 2.2 Parametrização por Nível de Condicionamento (`fitness_level`)

| Nível | Seleção de Complexidade (`complexity`) | Volume por Sessão (Séries Válidas) |
| :--- | :--- | :--- |
| **`INICIANTE`** | Prioriza `BAIXA` (🟢) e `MEDIA` (🟡). Limita exercícios de complexidade `ALTA` (🔴) a no máximo 1 por sessão (com foco pedagógico). | `10 a 14` séries totais na sessão (2 a 3 séries por exercício). |
| **`INTERMEDIARIO`** | Combina `ALTA` (🔴) e `MEDIA` (🟡) nos primeiros exercícios da sessão e finaliza com `BAIXA` (🟢). | `14 a 20` séries totais na sessão (3 a 4 séries por exercício). |
| **`AVANCADO`** | Aproveitamento total de multiarticulares de complexidade `ALTA` (🔴) e `MEDIA` (🟡) no início e finalizadores `BAIXA` (🟢) de altíssima eficiência levados próximos à falha. | `16 a 24` séries totais na sessão (3 a 4 séries por exercício, respeitando o tempo limite). |

---

### 2.3 Divisão Semanal Recomendada (*Workout Split*) por `days_per_week`

| Dias na Semana (`days_per_week`) | Divisão Recomendada pelo Especialista |
| :--- | :--- |
| **1 ou 2 dias** | **Full Body (Corpo Inteiro A / B):** Estimula todos os grandes grupos musculares em cada sessão. |
| **3 dias** | **Full Body 3x** (ideal para Iniciantes/Emagrecimento) ou **ABC (Push / Pull / Legs)** (Empurrar / Puxar / Pernas). |
| **4 dias** | **Upper / Lower 2x (Superior A / Inferior A / Superior B / Inferior B)** ou **ABCD**. |
| **5 dias** | **Upper / Lower + Push / Pull / Legs (ULPPL)** ou **ABCDE**. |
| **6 dias** | **Push / Pull / Legs 2x (ABC 2x)**. |
| **7 dias** | **Push / Pull / Legs 2x + 1 Dia de Core/Mobilidade e Cardio Dedicado**. |

---

### 2.4 Orçamento de Tempo da Sessão (`available_time_minutes`)

O Agente LLM calcula a duração total estimada (`estimated_duration_minutes`) para que **nunca exceda** `available_time_minutes`:
1. Reserva o tempo de cardio (`cardio_minutes`) adequado ao objetivo e ao tempo total disponível (ex: se o usuário tem `90 min` e objetivo `EMAGRECIMENTO`, pode alocar `40 min de cardio` e `50 min` de musculação; se tem `45 min` e objetivo `HIPERTROFIA`, pode alocar `10 min de cardio` e `35 min` de musculação).
2. Cada série de musculação consome aproximadamente `2.5 a 3.5 minutos` (incluindo execução, transição e descanso).
3. O número de exercícios de musculação por dia (tipicamente entre `4` e `8` exercícios) é dimensionado exatamente para caber nos minutos restantes:
   $$\text{Tempo Musculação} + \text{Tempo Cardio} \le \text{Tempo Disponível no Perfil}$$

---

## 3. Regras de Ordenação por Grupo Muscular e Biomecânica (Obrigatórias)

Em todas as gerações (completa ou diária), o Agente LLM e o validador pós-geração impõem quatro diretrizes auditáveis:

1. **Agrupamento Contíguo por Grupo Muscular (Zero Intercalação):**
   - Todos os exercícios de um mesmo grupo muscular devem ser executados em sequência contínua. Nunca intercalar grupos (ex: proibido prescrever Peito $\rightarrow$ Core $\rightarrow$ Peito).
2. **Hierarquia de Tamanho do Grupo Muscular (Maior $\rightarrow$ Menor $\rightarrow$ Core):**
   - Os blocos musculares de cada sessão devem seguir a ordem anatômica do maior para o menor grupo muscular:
     - **1º Bloco (Grandes Grupos):** `1. Peitoral (Peito)` | `2. Costas` | `3. Quadríceps` | `4. Posterior de Coxa e Glúteos`
     - **2º Bloco (Grupos Médios):** `5. Ombros (Deltoides) e Trapézio`
     - **3º Bloco (Grupos Menores):** `6. Bíceps e Antebraço` | `7. Tríceps` | `8. Panturrilhas e Tibial`
     - **4º Bloco (Core / Finalizador):** `9. Abdômen e Core`
3. **Ordem Neural Interna Dentro de Cada Grupo Muscular (Complexidade Decrescente):**
   - Dentro do bloco de cada grupo muscular, os exercícios devem ser ordenados por complexidade **Alta (🔴)** $\rightarrow$ **Média (🟡)** $\rightarrow$ **Baixa (🟢)** (finalizadores seguros de alta eficiência no fechamento daquele músculo), desempatando pela maior **Nota de Eficiência (`efficiency_score`)**.
4. **Regra de Anti-Redundância Biomecânica:**
   - É estritamente proibido incluir na mesma sessão exercícios com o mesmo padrão biomecânico e vetor de força (ex: nunca colocar *Supino Reto com Barra*, *Supino Reto com Halteres* e *Supino Máquina* no mesmo dia; variar sempre os ângulos).

---

## 4. Regra Estrita para Exercícios Cardiovasculares

Conforme requisito do sistema:
- Exercícios cardiovasculares **não** possuem séries, repetições, carga ou nome de aparelho específico imposto.
- Eles devem aparecer no treino informando **apenas o tempo**, exatamente no padrão:
  - Exemplo: `"40 min de cardio"`
  - Exemplo: `"20 min de cardio"`
- No contrato de saída do Agente LLM e no banco de dados (`workout_days`), o campo `cardio_minutes` armazena o inteiro (ex: `40`) e `cardio_display_text` armazena obrigatoriamente `"{cardio_minutes} min de cardio"` (ex: `"40 min de cardio"`).

---

## 5. Especificação dos Prompts do Agente LLM

### 5.1 System Prompt (Comum aos Dois Modos)

```markdown
Você é o Agente Especialista em Treinamento de Força, Hipertrofia e Condicionamento Físico do sistema Peito Infinity.
Sua função é montar treinos altamente eficientes, seguros e personalizados com base nos dados antropométricos e objetivos do usuário.

REGRAS INEGOCIÁVEIS:
1. FONTE ÚNICA DE EXERCÍCIOS: Você só pode escolher exercícios de musculação presentes na lista JSON `allowed_exercises` fornecida no prompt (oriunda do banco PostgreSQL e já filtrada sem os exercícios excluídos pelo usuário). Use exatamente o `exercise_id` correspondente.
2. ORDEM BIOMECÂNICA: Comece cada sessão pelos exercícios multiarticulares de complexidade ALTA ou MEDIA. Posicione os exercícios isoladores de complexidade BAIXA e alta eficiência na metade final do treino como finalizadores seguros.
3. ANTI-REDUNDÂNCIA: Nunca coloque dois exercícios com exatamente o mesmo ângulo e padrão biomecânico no mesmo dia (ex: dois supinos retos no mesmo dia). Varie os ângulos e estímulos.
4. REGRA DO CARDIO: Exercícios cardiovasculares devem ser informados APENAS pelo tempo em minutos no campo `cardio_minutes` e formatados exatamente como "{X} min de cardio" (exemplo: "40 min de cardio") no campo `cardio_display_text`.
5. LIMITE DE TEMPO: A soma do tempo estimado dos exercícios de musculação com o tempo de cardio (`cardio_minutes`) NÃO pode ultrapassar `available_time_minutes` do perfil do usuário.
```

---

### 5.2 Modo 1: Prompt de Geração do Treinamento Completo do Zero (`generate-full`)

**Entradas injetadas no User Prompt pelo Back-end:**
- Dados do Perfil (`name`, `weight_kg`, `height_cm`, `bmi`, `fitness_level`, `goal`, `available_time_minutes`, `days_per_week`).
- Catálogo `allowed_exercises`: Lista JSON contendo apenas os exercícios do PostgreSQL que **não foram excluídos** pelo usuário (`id`, `muscle_group`, `popular_name`, `primary_muscle`, `secondary_muscles`, `complexity`, `efficiency_score`).
- Instrução de saída: Gerar um plano completo contendo exatamente `days_per_week` dias (`day_number` de `1` até `days_per_week`).

---

### 5.3 Modo 2: Prompt de Regeneração de um Dia Específico (`regenerate-day`)

Quando o usuário solicita gerar novamente **apenas o treino de um dia específico** (`day_number`), o Agente LLM recebe:
- Dados do Perfil do usuário.
- Resumo do Plano Semanal Atual (quais músculos e exercícios estão nos *outros* dias da semana que **não** estão sendo alterados).
- O `day_number` alvo a ser regenerado, seu foco muscular atual (`target_muscles`) e a lista de exercícios que estavam anteriormente naquele dia (para que o Agente proponha uma variação inteligente e renovada, na medida do possível).
- Catálogo `allowed_exercises`: Exercícios do PostgreSQL já filtrados sem os `excluded_exercise_ids` informados pelo usuário no modal pré-geração.
- Instrução de saída: Retornar **exclusivamente** o novo objeto estruturado para o `day_number` solicitado.

---

## 6. Guardrails e Validação Pós-LLM (Back-end Python)

Antes de salvar a resposta do Agente LLM no PostgreSQL, o serviço Python executa um pipeline de verificação determinística:

1. **Verificação de Integridade de IDs (`Foreign Key Check`):** Todos os `exercise_id` retornados pelo LLM devem existir na tabela `exercises` do PostgreSQL.
2. **Verificação de Lista Negra (`Exclusion Check`):** Nenhum `exercise_id` retornado pode constar na lista `excluded_exercise_ids` enviada pelo usuário. Caso o LLM viole por alucinação, o back-end rejeita/corrige automaticamente com uma retentativa guiada (`max_retries = 2`).
3. **Normalização do Cardio (`Cardio Format Enforcer`):** O validador Pydantic garante que `cardio_display_text` seja sempre formatado como `f"{cardio_minutes} min de cardio"` (ex: `"40 min de cardio"`).
4. **Verificação de Contagem de Dias:** Na geração completa, `len(days)` deve ser exatamente igual a `profile.days_per_week`.
