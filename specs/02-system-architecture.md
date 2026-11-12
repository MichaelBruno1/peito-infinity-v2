# 02. Especificação de Arquitetura de Sistema e Infraestrutura Docker

**Projeto:** Peito Infinity  
**Documento:** Arquitetura C4, Topologia de Rede Privada, Fluxos de Sequência e Orquestração Docker  
**Status:** Especificação Base (SDD)  

---

## 1. Visão Geral da Arquitetura

O **Peito Infinity** adota uma arquitetura em **3 Camadas Containerizadas** (*Three-Tier Containerized Architecture*), executada integralmente dentro de uma rede local doméstica (LAN) sob orquestração do **Docker Compose**:

1. **Camada de Apresentação (Front-end Web Responsivo):** Single Page Application (SPA) desenvolvida em **JavaScript com React + Vite + Tailwind CSS**, servida em produção por um container **Nginx** que também atua como *Reverse Proxy* para encaminhar requisições `/api/*` ao back-end (eliminando problemas de CORS e expondo uma única porta na rede doméstica).
2. **Camada de Aplicação e Inteligência (Back-end API + Agente LLM):** Serviço em **Python com FastAPI**, estruturado segundo princípios de *Clean Architecture / Layered Architecture* (Routers -> Services/Use Cases -> LLM Agent Orchestrator -> Repositories -> SQLAlchemy ORM).
3. **Camada de Persistência (Banco de Dados):** Container **PostgreSQL 16** com volume persistente, atuando como única fonte de verdade para Perfis, Catálogo de Exercícios (populado via Seed inicial) e Planos/Dias de Treino.

---

## 2. Diagrama de Contexto e Topologia em Rede Doméstica (C4 Nível 1 & 2)

```mermaid
flowchart TB
    subgraph LAN["Rede Doméstica Privada (LAN / Wi-Fi - Sem Autenticação)"]
        Mobile["📱 Smartphone do Usuário\n(Navegador Mobile)"]
        Desktop["💻 Computador / Tablet\n(Navegador Desktop)"]

        subgraph DockerHost["Host Docker Doméstico (Docker Compose Network: peito_infinity_net)"]
            Frontend["🌐 Container: peito-frontend\nReact 18 + Vite + Tailwind CSS\nServido via Nginx (Porta 80 / 3000)"]
            Backend["⚙️ Container: peito-backend\nPython 3.12 + FastAPI + SQLAlchemy\nAgente LLM Especialista (Porta 8000)"]
            Postgres[("🐘 Container: peito-db\nPostgreSQL 16 Alpine\nVolume: postgres_data (Porta 5432)")]
            SeedFile["📄 Arquivo Seed Inicial\n(guia-exercicios-seed.md)\nLido apenas no 1º Boot"]
        end
    end

    LLMProvider["🧠 Provedor de LLM\n(API Externa OpenAI/Gemini/Anthropic\nou Ollama Local na LAN)"]

    Mobile -->|"HTTP (LAN IP:Porta)"| Frontend
    Desktop -->|"HTTP (LAN IP:Porta)"| Frontend
    Frontend -->|"Proxy Reverso /api/v1/*"| Backend
    Backend -->|"SQL / AsyncPG"| Postgres
    SeedFile -.->|"Importação Única (Se tabela vazia)"| Backend
    Backend <-->|"Prompt Estruturado + JSON Schema"| LLMProvider
```

---

## 3. Arquitetura Interna de Componentes (C4 Nível 3)

### 3.1 Componentes do Back-end (Python / FastAPI)

```mermaid
flowchart LR
    subgraph FastAPI_App["Aplicação Back-end (Python / FastAPI)"]
        direction TB
        Lifespan["Lifecycle / Bootstrap Hook\n(Migrações Alembic + Seed Inicial)"]
        
        subgraph API_Layer["Camada de Apresentação HTTP (Routers)"]
            ProfileRouter["Profile Router\n(/api/v1/profiles)"]
            ExerciseRouter["Exercise Router\n(/api/v1/exercises)"]
            WorkoutRouter["Workout Router\n(/api/v1/workouts)"]
        end

        subgraph Service_Layer["Camada de Domínio & Serviços"]
            SeedService["Markdown Seed Service\n(Parser de Tabelas MD)"]
            ProfileService["Profile Service\n(CRUD + Exclusões)"]
            ExerciseService["Exercise Service\n(Consulta ao Postgres)"]
            WorkoutService["Workout Orchestrator Service\n(Geração Total & Diária)"]
            LLMAgent["Agente LLM Especialista\n(Prompt Builder + Validador Pydantic)"]
        end

        subgraph Data_Layer["Camada de Persistência (Repositories / ORM)"]
            Repos["SQLAlchemy 2.0 Repositories\n(Profile, Exercise, WorkoutPlan, WorkoutDay)"]
        end
    end

    DB[("PostgreSQL 16")]

    Lifespan --> SeedService
    SeedService --> Repos
    ProfileRouter --> ProfileService
    ExerciseRouter --> ExerciseService
    WorkoutRouter --> WorkoutService
    WorkoutService --> ExerciseService
    WorkoutService --> LLMAgent
    ProfileService --> Repos
    ExerciseService --> Repos
    WorkoutService --> Repos
    Repos --> DB
```

### 3.2 Componentes do Front-end (JavaScript / React)

| Módulo / Diretório Lógico | Responsabilidade Arquitetural |
| :--- | :--- |
| **`pages/ProfileSelectorPage`** | Tela inicial sem login: exibe cards dos perfis cadastrados e botão de criar novo perfil. |
| **`pages/ProfileFormModal`** | Formulário de criação e edição de perfil (nome, peso, altura, condicionamento, objetivo, minutos/dia, dias/semana). |
| **`pages/WorkoutDashboardPage`** | Painel principal do perfil selecionado: resumo das métricas do usuário, abas para cada dia da semana (`Dia 1` .. `Dia N`), card de cardio em minutos e lista de exercícios do dia. |
| **`components/ExerciseExclusionModal`** | Modal obrigatório exibido **antes de gerar qualquer treino**: lista os exercícios vindos do PostgreSQL agrupados por músculo, permitindo desmarcar/excluir exercícios indesejados antes de chamar o Agente LLM. |
| **`services/apiClient`** | Cliente HTTP centralizado para comunicação com `/api/v1/*` gerenciado via TanStack Query. |

---

## 4. Fluxos de Sequência (Diagramas de Sequência)

### 4.1 Inicialização do Sistema e Importação Inicial (Seed)

Garante que o arquivo Markdown seja usado apenas na primeira execução e que o banco PostgreSQL seja a fonte oficial de dados para os treinos.

```mermaid
sequenceDiagram
    autonumber
    participant Docker as Docker Compose
    participant DB as PostgreSQL (peito-db)
    participant API as FastAPI (peito-backend)
    participant MD as guia-exercicios-seed.md

    Docker->>DB: Inicia container PostgreSQL + Healthcheck
    DB-->>Docker: Status: Healthy (pg_isready)
    Docker->>API: Inicia container Back-end
    API->>DB: Executa migrações de schema (Alembic)
    API->>DB: SELECT COUNT(*) FROM exercises
    alt Tabela exercises está vazia (Primeira Execução)
        DB-->>API: count = 0
        API->>MD: Lê arquivo Markdown de Seed
        API->>API: Faz parse dos 9 grupos musculares e 89 exercícios
        API->>DB: INSERT INTO exercises (89 registros em transação única)
        DB-->>API: Commit confirmado
    else Tabela exercises já possui dados (Execuções Subsequentes)
        DB-->>API: count = 89
        API->>API: Ignora arquivo Markdown (Usa Banco como Fonte Única)
    end
    API-->>Docker: Servidor FastAPI pronto na porta 8000
```

---

### 4.2 Fluxo de Geração de Treino (Completo do Zero ou Dia Específico) com Exclusão Prévia

```mermaid
sequenceDiagram
    autonumber
    actor User as Usuário (Mobile/Desktop)
    participant UI as Front-end (React)
    participant API as Back-end (FastAPI)
    participant DB as PostgreSQL
    participant LLM as Agente LLM Especialista

    User->>UI: Clica em "Gerar Treino Completo" OU "Regenerar Dia X"
    UI->>API: GET /api/v1/exercises
    API->>DB: SELECT * FROM exercises ORDER BY muscle_group, efficiency_score DESC
    DB-->>API: Lista dos 89 exercícios do banco
    API-->>UI: JSON de exercícios + exclusões salvas do perfil
    UI->>User: Exibe Modal: "Deseja excluir algum exercício antes de montar o treino?"
    User->>UI: Seleciona/desmarca exercícios que NÃO quer fazer e confirma
    
    alt Modo 1: Gerar Todo o Treinamento do Zero
        UI->>API: POST /api/v1/profiles/{id}/workouts/generate-full (excluded_exercise_ids)
        API->>DB: Atualiza preferências de exclusão do perfil
        API->>DB: SELECT * FROM exercises WHERE id NOT IN (excluded_exercise_ids)
        DB-->>API: Lista estrita de exercícios permitidos
        API->>LLM: Envia Perfil + Exercícios Permitidos + Regras Biomecânicas + Regra Cardio
        LLM-->>API: JSON Estruturado (Dias 1..N + Exercícios + "X min de cardio")
        API->>API: Valida se IDs existem no banco, não estão excluídos e formato do cardio
        API->>DB: Salva novo Plano de Treino completo e seus Dias
        DB-->>API: Plano persistido
        API-->>UI: 201 Created (Plano Completo Atualizado)
    else Modo 2: Gerar Novo Treino Apenas para o Dia Específico (Dia X)
        UI->>API: POST /api/v1/profiles/{id}/workouts/days/{day_number}/regenerate (excluded_exercise_ids)
        API->>DB: Carrega Perfil + Plano Atual (Dias 1..N) + Exercícios Permitidos (NOT IN excluídos)
        API->>LLM: Solicita recriação APENAS do Dia X (enviando contexto dos outros dias para evitar conflito)
        LLM-->>API: JSON Estruturado apenas do novo Dia X (Exercícios + "X min de cardio")
        API->>API: Valida exercícios permitidos e formato de cardio
        API->>DB: Atualiza exclusivamente os registros do Dia X no banco
        DB-->>API: Dia X atualizado (demais dias intactos)
        API-->>UI: 200 OK (Plano com Dia X regenerado)
    end

    UI-->>User: Renderiza treino atualizado na tela responsiva
```

---

## 5. Especificação da Infraestrutura Docker

Para garantir portabilidade absoluta e execução simples em qualquer máquina da rede doméstica, a arquitetura define três containers coordenados por `docker-compose`.

### 5.1 Matriz de Containers e Serviços

| Nome do Serviço | Imagem Base Recomendada | Porta Interna | Porta Exposta (LAN) | Dependências (`depends_on`) | Volumes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`db`** | `postgres:16-alpine` | `5432` | `5432` (opcional p/ debug) | Nenhuma | `postgres_data:/var/lib/postgresql/data` |
| **`backend`** | `python:3.12-slim` | `8000` | `8000` (Swagger/API) | `db` (`service_healthy`) | Leitura do arquivo seed embutido na imagem |
| **`frontend`** | Build: `node:20-alpine` -> Runtime: `nginx:stable-alpine` | `80` | `80` (ou `3000`) | `backend` (`service_started`) | Nenhum (artefatos estáticos compilados) |

### 5.2 Variáveis de Ambiente Especificadas (`.env.example`)

| Variável | Serviço Alvo | Descrição | Valor Padrão / Exemplo |
| :--- | :--- | :--- | :--- |
| `POSTGRES_USER` | `db`, `backend` | Usuário do banco PostgreSQL | `peito_user` |
| `POSTGRES_PASSWORD` | `db`, `backend` | Senha do banco PostgreSQL interno | `peito_secret_lan` |
| `POSTGRES_DB` | `db`, `backend` | Nome da base de dados | `peito_infinity` |
| `DATABASE_URL` | `backend` | String de conexão SQLAlchemy | `postgresql+psycopg://peito_user:peito_secret_lan@db:5432/peito_infinity` |
| `SEED_FILE_PATH` | `backend` | Caminho do arquivo Markdown para 1ª execução | `/app/seed/guia-exercicios-seed.md` |
| `LLM_PROVIDER` | `backend` | Provedor do Agente LLM (`openai`, `gemini`, `ollama`) | `openai` ou `gemini` |
| `LLM_MODEL` | `backend` | Modelo utilizado pelo Agente Especialista | `gpt-4o-mini` / `gemini-2.5-flash` |
| `LLM_API_KEY` | `backend` | Chave de API do provedor LLM (ou vazio se Ollama local) | `sk-...` |
| `VITE_API_BASE_URL` | `frontend` | Caminho base da API via Proxy Reverso Nginx | `/api/v1` |

### 5.3 Topologia de Rede Doméstica (Acesso Mobile e Desktop)
- O serviço `frontend` faz *bind* em `0.0.0.0:80` (ou `0.0.0.0:3000`) no computador/servidor doméstico onde o Docker está rodando.
- Qualquer celular ou computador conectado ao mesmo roteador Wi-Fi doméstico acessa `http://<IP-LOCAL-DO-HOST>:3000` (ex: `http://192.168.1.50:3000`) diretamente pelo navegador, sem configuração adicional e sem necessidade de login.
