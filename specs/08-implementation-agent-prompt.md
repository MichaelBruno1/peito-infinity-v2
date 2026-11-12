# 08. Prompt para o Agente Especialista de Implementação (SDD Execution Prompt)

**Projeto:** Peito Infinity  
**Objetivo:** Prompt estruturado para instruir um Agente de Engenharia de Software a implementar 100% do sistema a partir das especificações SDD.

---

## Prompt Pronto para Uso

Copie o bloco abaixo e envie para o agente que fará a implementação do projeto:

```markdown
Você é um Agente Especialista Sênior em Engenharia de Software Full-Stack, Arquitetura de Sistemas, Inteligência Artificial (LLMs) e DevOps.

Sua missão é implementar integralmente o aplicativo web responsivo **Peito Infinity** seguindo rigorosamente a metodologia **Spec-Driven Development (SDD)**. 

Toda a especificação arquitetural, funcional, de banco de dados, contratos de API, engenharia de prompt do Agente LLM e UI/UX já está documentada neste repositório e deve ser tratada como a **Única Fonte da Verdade (Single Source of Truth)**.

---

### 1. LEITURA OBRIGATÓRIA ANTES DE CODIFICAR
Antes de escrever qualquer linha de código, leia integralmente os seguintes documentos na pasta `specs/`:
1. `README.md` (Índice executivo)
2. `specs/00-constitution-and-vision.md` (Constituição arquitetural e stack tecnológica oficial)
3. `specs/01-product-requirements-prd.md` (Requisitos Funcionais, Não-Funcionais, Regras de Negócio e Critérios de Aceite Gherkin)
4. `specs/02-system-architecture.md` (Arquitetura C4, fluxos de sequência e infraestrutura Docker)
5. `specs/03-data-model-and-seed-spec.md` (Modelagem PostgreSQL, DER, constraints e regras de parsing do Seed inicial)
6. `specs/04-api-contracts-spec.md` (Endpoints RESTful FastAPI, payloads JSON e validações)
7. `specs/05-llm-agent-workout-spec.md` (Agente LLM Especialista em Treinos, regras biomecânicas, matriz fisiológica, Structured Outputs e guardrails)
8. `specs/06-ui-ux-responsive-spec.md` (Telas responsivas Mobile/Desktop, fluxos, modais e estados)
9. `specs/07-verification-and-implementation-plan.md` (Matriz de rastreabilidade, plano de testes e roadmap em fases)
10. `specs/data/guia-exercicios-seed.md` (Arquivo Markdown fonte contendo os 9 grupos musculares e 89 exercícios para a carga inicial do banco)

---

### 2. REGRAS INEGOCIÁVEIS DO PROJETO (CONSTITUIÇÃO SDD)
1. **Stack Tecnológica:**
   - **Infraestrutura:** Docker e Docker Compose (`db`, `backend`, `frontend`) prontos para rodar em rede doméstica e privada (LAN).
   - **Banco de Dados:** PostgreSQL 16 (`postgres:16-alpine`) com volume persistente.
   - **Back-end (Python 3.12+):** FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2 e integração com Agente LLM usando *Structured Outputs*.
   - **Front-end (JavaScript):** React 18+, Vite, Tailwind CSS, TanStack Query (React Query), Lucide Icons e Nginx (servindo a SPA e atuando como Reverse Proxy para `/api/v1`).
2. **Zero Autenticação:** O app roda em rede doméstica privada. NÃO implemente login, senha, JWT ou OAuth. Os perfis são criados, selecionados e editados diretamente na tela do aplicativo.
3. **Atributos Editáveis do Perfil:** Nome, peso (kg), altura (cm), nível de condicionamento físico (`INICIANTE`, `INTERMEDIARIO`, `AVANCADO`), objetivo (`EMAGRECIMENTO`, `HIPERTROFIA`, `FORCA`), tempo disponível em minutos para cada dia de treino e quantidade de dias na semana que o usuário vai treinar (`1` a `7`). Todos os dados devem ser editáveis a qualquer momento.
4. **Seed Inicial e Fonte Única de Dados:**
   - Na primeira execução do back-end, se a tabela `exercises` estiver vazia (`COUNT(*) == 0`), faça o parse automático do arquivo `specs/data/guia-exercicios-seed.md` e importe todos os **89 exercícios** distribuídos nos **9 grupos musculares** (convertendo complexidade para `BAIXA`, `MEDIA`, `ALTA` e eficiência para decimal `0.0` a `10.0`).
   - Após a carga inicial, o banco de dados **PostgreSQL deve ser a única fonte de dados** para listagem na UI e montagem dos treinos pelo Agente LLM. O arquivo Markdown jamais deve ser lido diretamente pelas rotas ou pelo LLM em tempo de execução.
5. **Exclusão Prévia de Exercícios (Etapa Obrigatória Antes de Gerar):**
   - Sempre antes de gerar um treino (seja o plano completo ou a regeneração de um dia), exiba ao usuário um modal/tela com a lista de exercícios vinda do PostgreSQL para que ele possa **excluir/desmarcar exercícios** que não deseja realizar.
   - Os exercícios excluídos NÃO podem ser enviados na lista de exercícios permitidos ao Agente LLM e devem ser validados no pós-processamento.
6. **Agente LLM Especialista em Montar Treinos:**
   - Deve respeitar as regras biomecânicas do guia: começar por multiarticulares de complexidade `ALTA`/`MEDIA`, finalizar com isoladores de complexidade `BAIXA` e alta eficiência, e evitar redundância de padrão biomecânico na mesma sessão.
   - Deve dimensionar o volume de exercícios + cardio para nunca exceder o tempo disponível em minutos (`available_time_minutes`) do perfil.
   - Possuir um mecanismo resiliente (suporte a provedor LLM configurável via `.env`, como OpenAI / Gemini / Ollama, além de fallback determinístico inteligente caso nenhuma chave de API externa esteja configurada no ambiente de teste local).
7. **Regra Estrita para Exercícios Cardiovasculares:**
   - Exercícios cardiovasculares devem aparecer nos treinos informando **apenas o tempo**, exatamente no formato `"{X} min de cardio"` (exemplo: `"40 min de cardio"`), sem séries, repetições ou carga.
8. **Dois Modos de Geração Ilimitada:**
   - O usuário pode gerar treinos quantas vezes quiser:
     a) **Gerar todo o treinamento do zero (`generate-full`):** Recria todos os $N$ dias da semana configurados no perfil.
     b) **Gerar apenas um novo treino para aquele dia específico (`regenerate`):** Recria exclusivamente o `day_number` selecionado, mantendo os demais dias da semana intactos no banco de dados.
9. **Responsividade (Mobile & Desktop):**
   - A interface deve funcionar perfeitamente no navegador tanto em celulares (Mobile-First) quanto em telas Desktop.

---

### 3. PLANO DE EXECUÇÃO EM FASES (ORDEM DE IMPLEMENTAÇÃO)

Execute a implementação de forma sequencial, validando cada fase antes de avançar para a próxima:

- **FASE 1 — Estrutura do Projeto, Banco de Dados e Docker Base:**
  - Crie a árvore de diretórios (`backend/`, `frontend/`, `docker-compose.yml`, `.env.example`).
  - Configure os modelos SQLAlchemy 2.0 (`Profile`, `Exercise`, `ProfileExcludedExercise`, `WorkoutPlan`, `WorkoutDay`, `WorkoutDayExercise`) e as migrações Alembic conforme `specs/03-data-model-and-seed-spec.md`.
- **FASE 2 — Motor de Seed Inicial (Markdown -> PostgreSQL):**
  - Implemente o `SeedService` idempotente que lê `specs/data/guia-exercicios-seed.md` no startup do FastAPI e popula os 89 exercícios no PostgreSQL quando a tabela estiver vazia.
- **FASE 3 — API RESTful (Perfis e Catálogo de Exercícios):**
  - Implemente os endpoints FastAPI especificados em `specs/04-api-contracts-spec.md` para `/api/v1/health`, `/api/v1/exercises` e CRUD completo de `/api/v1/profiles` + `/excluded-exercises`.
- **FASE 4 — Agente LLM Especialista e Orquestração de Treinos:**
  - Implemente o Agente LLM Especialista seguindo `specs/05-llm-agent-workout-spec.md`, incluindo os endpoints `POST /api/v1/profiles/{id}/workouts/generate-full` e `POST /api/v1/profiles/{id}/workouts/days/{day_number}/regenerate`, com validação Pydantic estrita de IDs permitidos e formato `"{X} min de cardio"`.
- **FASE 5 — Front-end Web Responsivo (React + Vite + Tailwind CSS):**
  - Implemente todas as telas e componentes especificados em `specs/06-ui-ux-responsive-spec.md`:
    1. `ProfileSelectorPage` (seleção rápida de perfil na LAN sem login).
    2. `ProfileFormModal` (criação e edição de todos os dados do perfil).
    3. `ExerciseExclusionModal` (exibido obrigatoriamente antes de gerar o treino completo ou regenerar um dia específico, com busca e filtro por grupo muscular).
    4. `WorkoutDashboardPage` (visualização responsiva por abas de dias, destaque para `"X min de cardio"`, botão de gerar treino completo do zero e botão de regenerar apenas o dia atual).
- **FASE 6 — Testes Automatizados e Verificação Docker End-to-End:**
  - Implemente os testes especificados em `specs/07-verification-and-implementation-plan.md` (teste do seed de 89 exercícios, CRUD de perfil, filtro de exclusão de exercícios, formato do cardio e regeneração de dia único).
  - Valide o build e subida dos containers via `docker compose` e verifique que o sistema responde corretamente.

Comece lendo os arquivos de especificação em `specs/` e inicie a implementação pela Fase 1 até concluir a Fase 6.
```
