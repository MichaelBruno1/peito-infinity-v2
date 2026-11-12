# 🏋️‍♂️ Peito Infinity — Documentação de Arquitetura e Especificação (SDD)

Bem-vindo à documentação oficial do **Peito Infinity**, elaborada integralmente no padrão **Spec-Driven Development (SDD)**.

> [!NOTE]
> Este repositório contém tanto a **Documentação Completa no Padrão Spec-Driven Development (SDD)** quanto a **Implementação Full-Stack Containerizada** validada ponta a ponta.

---

## 🚀 Como Executar na Rede Doméstica (Docker)

```bash
docker compose up -d --build
```

* **Aplicação Web Responsiva (Mobile & Desktop):** `http://localhost:3000` (ou `http://<IP-DA-MAQUINA-NA-LAN>:3000`)
* **API FastAPI & Documentação Swagger:** `http://localhost:8000/docs`
* **Executar Testes Automatizados (`pytest`):**
  ```bash
  docker exec peito-backend python -m pytest -v
  ```

---

## 📌 Visão Executiva do Sistema

O **Peito Infinity** é uma aplicação web responsiva (otimizada para navegadores **Mobile** e **Desktop**) projetada para execução em **rede doméstica e privada (LAN)**, sem necessidade de autenticação ou login. Seu objetivo é montar e gerenciar treinos personalizados de academia por meio de um **Agente LLM Especialista**, utilizando um banco de dados **PostgreSQL** populado inicialmente a partir do guia definitivo de exercícios de musculação.

### Stack Tecnológica Definida
* **Containerização & Orquestração:** Docker & Docker Compose
* **Banco de Dados:** PostgreSQL 16 (única fonte de dados para os treinos após o seed inicial)
* **Back-end (Python):** FastAPI + SQLAlchemy 2.0 + Alembic + Pydantic v2
* **Agente de IA (LLM):** Orquestrador Python com *Structured Outputs* (LangChain / PydanticAI compatível com OpenAI, Google Gemini ou Ollama)
* **Front-end (JavaScript):** React 18 + Vite + Tailwind CSS + TanStack Query + Nginx (Reverse Proxy)

---

## 📚 Índice da Especificação (Spec-Driven Development)

| Ordem | Documento de Especificação | Descrição do Conteúdo |
| :---: | :--- | :--- |
| **00** | [00-constitution-and-vision.md](file:///c:/projetos/peito-infinity-v2/specs/00-constitution-and-vision.md) | **Constituição do Projeto e Visão:** Princípios arquiteturais inegociáveis, justificativa da stack tecnológica e glossário do domínio (Ubiquitous Language). |
| **01** | [01-product-requirements-prd.md](file:///c:/projetos/peito-infinity-v2/specs/01-product-requirements-prd.md) | **Requisitos de Produto (PRD):** Escopo, Requisitos Funcionais (`RF-01` a `RF-13`), Requisitos Não-Funcionais (`RNF-01` a `RNF-06`), Regras de Negócio (`RN-01` a `RN-05`) e User Stories com Critérios de Aceite em Gherkin. |
| **02** | [02-system-architecture.md](file:///c:/projetos/peito-infinity-v2/specs/02-system-architecture.md) | **Arquitetura de Sistema e Docker:** Diagramas C4 (Contexto, Containers e Componentes), topologia de rede doméstica sem login, diagramas de sequência e matriz de containers Docker. |
| **03** | [03-data-model-and-seed-spec.md](file:///c:/projetos/peito-infinity-v2/specs/03-data-model-and-seed-spec.md) | **Modelo de Dados e Carga Inicial (Seed):** Diagrama Entidade-Relacionamento (DER), dicionário de dados detalhado do PostgreSQL e especificação da importação inicial única do arquivo Markdown. |
| **04** | [04-api-contracts-spec.md](file:///c:/projetos/peito-infinity-v2/specs/04-api-contracts-spec.md) | **Contratos da API RESTful:** Endpoints FastAPI, payloads de Request/Response para perfis, exclusão prévia de exercícios, geração completa do zero e regeneração de dia específico. |
| **05** | [05-llm-agent-workout-spec.md](file:///c:/projetos/peito-infinity-v2/specs/05-llm-agent-workout-spec.md) | **Especificação do Agente LLM Especialista:** Matriz fisiológica (Emagrecimento, Hipertrofia, Força), regras biomecânicas, regra do cardio apenas por tempo (`"40 min de cardio"`), prompts e guardrails pós-geração. |
| **06** | [06-ui-ux-responsive-spec.md](file:///c:/projetos/peito-infinity-v2/specs/06-ui-ux-responsive-spec.md) | **Interface Responsiva (UI/UX):** Breakpoints Mobile e Desktop, fluxograma de estados de tela, criação/edição de perfil sem autenticação, modal pré-geração de exclusão de exercícios e painel diário. |
| **07** | [07-verification-and-implementation-plan.md](file:///c:/projetos/peito-infinity-v2/specs/07-verification-and-implementation-plan.md) | **Plano de Verificação e Roadmap:** Matriz de rastreabilidade de requisitos (RTM), cenários de teste automatizados e fases de implementação SDD. |
| **08** | [08-implementation-agent-prompt.md](file:///c:/projetos/peito-infinity-v2/specs/08-implementation-agent-prompt.md) | **Prompt de Execução SDD:** Prompt completo e estruturado para instruir um Agente Especialista a implementar o projeto do zero ao deploy Docker. |
| **Seed** | [guia-exercicios-seed.md](file:///c:/projetos/peito-infinity-v2/specs/data/guia-exercicios-seed.md) | **Artefato de Dados Inicial:** Guia com os 9 grupos musculares, 89 exercícios classificados por complexidade/eficiência e dicas do especialista para a carga inicial do PostgreSQL. |
