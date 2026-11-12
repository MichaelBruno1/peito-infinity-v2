# 00. Constituição do Projeto e Visão Geral (SDD Constitution)

**Projeto:** Peito Infinity  
**Metodologia:** Spec-Driven Development (SDD)  
**Versão da Especificação:** 2.0.0  
**Status:** Especificação Aprovada (Fase 0 — Sem Código)  

---

## 1. Visão do Produto

O **Peito Infinity** é uma aplicação web responsiva (Mobile-First e Desktop) projetada para montar, personalizar e gerenciar treinos de academia sob medida por meio de um **Agente LLM Especialista em Prescrição de Treinos**.

O sistema foi concebido para operar exclusivamente em uma **rede doméstica e privada (LAN / Homelab)**. Por essa razão, prioriza a fricção zero: **não possui autenticação, senhas ou fluxos de login**. Os moradores ou membros da rede criam e selecionam seus perfis diretamente na tela inicial do aplicativo, ajustam suas métricas corporais e objetivos a qualquer momento, filtram exercícios indesejados e geram planos de treinamento semanais completos ou regeneram treinos de dias específicos sob demanda.

---

## 2. Princípios Inegociáveis (Constituição Arquitetural)

No paradigma **Spec-Driven Development (SDD)**, todas as decisões de implementação futura devem obedecer estritamente às diretrizes constitucionais abaixo:

1. **Zero Autenticação (Fricção Zero em Rede Local):**
   - O sistema não deve implementar telas de login, registro de credenciais, tokens JWT, sessões autenticadas ou OAuth.
   - O acesso aos perfis ocorre por seleção direta na interface (*Profile Switcher* estilo Netflix / apps domésticos).
2. **Banco de Dados como Única Fonte da Verdade (Single Source of Truth):**
   - O arquivo [guia-exercicios-seed.md](file:///c:/projetos/peito-infinity-v2/specs/data/guia-exercicios-seed.md) é utilizado **exclusivamente na primeira execução (bootstrap/seed)** para popular o banco de dados PostgreSQL.
   - Após a carga inicial, toda listagem de exercícios na UI, filtragem de exclusões e montagem de contexto para o Agente LLM deve consultar **exclusivamente o banco de dados PostgreSQL**.
3. **Filtragem Determinística Pré-LLM de Exercícios Excluídos:**
   - Antes de cada geração de treino (completa ou diária), o usuário visualiza o catálogo de exercícios e pode excluir/desmarcar qualquer exercício que não deseje realizar.
   - Os exercícios excluídos devem ser removidos **antes** de compor o *prompt* do Agente LLM e validados após a resposta do LLM, garantindo 0% de chance de um exercício banido aparecer no treino prescrito.
4. **Regra Estrita para Exercícios Cardiovasculares:**
   - Exercícios cardiovasculares não pertencem à tabela de séries/repetições/carga de musculação tradicional; eles devem ser exibidos e prescritos no treino informando **apenas o tempo de duração**, no formato padronizado: `"{X} min de cardio"` (exemplo: `"40 min de cardio"`).
5. **Mutabilidade Total de Perfil e Regeneração Ilimitada:**
   - Todos os atributos do perfil são editáveis a qualquer momento.
   - O usuário pode gerar um novo treino quantas vezes quiser, escolhendo entre:
     - **Regeneração Total:** Gerar todo o plano semanal do zero.
     - **Regeneração Diária:** Gerar novamente apenas o treino de um dia específico da semana, preservando os demais dias.
6. **Responsividade Universal (Mobile & Desktop):**
   - A interface web deve ser 100% funcional e ergonômica tanto em smartphones (para consulta rápida durante o treino ou no Wi-Fi residencial) quanto em navegadores desktop/tablet.
7. **Containerização Integral via Docker:**
   - Todo o ecossistema (Banco de Dados, Back-end Python, Front-end JavaScript) deve ser orquestrado via Docker e Docker Compose, permitindo inicialização com comando único na rede doméstica.

---

## 3. Stack Tecnológica Oficial (Padrão de Mercado)

Para atender ao requisito de utilizar os **frameworks mais populares do mercado** em Python, JavaScript, PostgreSQL e Docker, a arquitetura adota a seguinte stack padronizada:

| Camada | Tecnologia / Framework | Justificativa Técnica |
| :--- | :--- | :--- |
| **Front-end (JavaScript)** | **React 18+ (Vite)** | Biblioteca JavaScript mais popular do mercado para interfaces de usuário modernas e reativas, empacotada com Vite para alta performance. |
| **Estilização & UI Responsiva** | **Tailwind CSS + Lucide Icons** | Framework CSS utility-first líder de mercado para design responsivo (*Mobile-First* e *Desktop*) com componentes acessíveis. |
| **Gerenciamento de Estado / HTTP** | **TanStack Query (React Query) + Axios/Fetch** | Padrão de mercado para sincronização de estado assíncrono, cache e mutações REST no React. |
| **Back-end (Python)** | **FastAPI (Python 3.12+)** | Framework web Python mais popular para APIs REST modernas e integração com IA/LLMs, com alta performance assíncrona e validação nativa via **Pydantic v2**. |
| **ORM & Migrações** | **SQLAlchemy 2.0 + Alembic** | ORM padrão ouro do ecossistema Python com suporte a tipagem moderna e controle versionado de schema no PostgreSQL. |
| **Orquestração de IA / Agente LLM** | **LangChain / PydanticAI (OpenAI / Gemini / Ollama SDK)** | Abstração para agentes especialistas com suporte nativo a **Structured Outputs** (garantia de retorno JSON validado por schema Pydantic). |
| **Banco de Dados Relacional** | **PostgreSQL 16 (Alpine)** | SGBD relacional open-source mais robusto e popular do mercado, com suporte a integridade referencial e tipos JSONB/Arrays quando necessário. |
| **Infraestrutura & Rede** | **Docker & Docker Compose + Nginx** | Empacotamento padronizado em containers isolados, com Nginx servindo o bundle estático do React e atuando como *reverse proxy* para a API FastAPI na LAN. |

---

## 4. Glossário do Domínio

| Termo | Definição no Sistema |
| :--- | :--- |
| **Perfil de Usuário (`Profile`)** | Entidade que representa um praticante na rede doméstica (Nome, Peso, Altura, Nível de Condicionamento, Objetivo, Tempo Disponível por Dia em minutos e Dias de Treino por Semana). |
| **Catálogo de Exercícios (`Exercise`)** | Base de 89 exercícios de musculação importados do arquivo Markdown de seed para o PostgreSQL, contendo Grupo Muscular, Nome Popular, Músculo Principal, Músculos Secundários, Complexidade (`BAIXA`, `MEDIA`, `ALTA`) e Nota de Eficiência (`0.0` a `10.0`). |
| **Lista de Exclusão (`Excluded Exercises`)** | Conjunto de exercícios desmarcados pelo usuário na etapa pré-geração que o Agente LLM está proibido de incluir no treino. |
| **Plano de Treino (`WorkoutPlan`)** | Conjunto estruturado de dias de treino (de 1 a $N$ dias conforme configurado no perfil) gerado pelo Agente LLM para um Perfil de Usuário. |
| **Dia de Treino (`WorkoutDay`)** | Sessão individual dentro do Plano Semanal (ex: "Dia 1 — Treino A: Peito, Ombros e Tríceps"), contendo os exercícios prescritos de musculação e a prescrição de cardio em minutos. |
| **Prescrição de Cardio (`CardioPrescription`)** | Indicação exclusiva de tempo em minutos de atividade aeróbica na sessão (ex: `"40 min de cardio"`), sem séries, repetições ou carga. |
| **Seed Inicial (`Database Seeding`)** | Processo automatizado executado no boot do back-end que verifica se a tabela `exercises` está vazia e, em caso afirmativo, faz o *parse* e inserção dos dados do arquivo Markdown original. |

---

## 5. Estrutura da Documentação SDD

Este repositório segue a organização modular do Spec-Driven Development:

1. [00-constitution-and-vision.md](file:///c:/projetos/peito-infinity-v2/specs/00-constitution-and-vision.md) — Constituição, Princípios e Stack Tecnológica.
2. [01-product-requirements-prd.md](file:///c:/projetos/peito-infinity-v2/specs/01-product-requirements-prd.md) — Requisitos Funcionais, Não-Funcionais, Regras de Negócio e User Stories (Gherkin).
3. [02-system-architecture.md](file:///c:/projetos/peito-infinity-v2/specs/02-system-architecture.md) — Arquitetura de Sistema, Diagramas C4/Mermaid, Docker e Rede Local.
4. [03-data-model-and-seed-spec.md](file:///c:/projetos/peito-infinity-v2/specs/03-data-model-and-seed-spec.md) — Modelagem de Dados PostgreSQL, DER, Dicionário de Dados e Especificação de Seed.
5. [04-api-contracts-spec.md](file:///c:/projetos/peito-infinity-v2/specs/04-api-contracts-spec.md) — Contratos RESTful (FastAPI), Schemas JSON e Códigos de Retorno.
6. [05-llm-agent-workout-spec.md](file:///c:/projetos/peito-infinity-v2/specs/05-llm-agent-workout-spec.md) — Especificação do Agente LLM Especialista em Treinos, Prompts e Regras Biomecânicas.
7. [06-ui-ux-responsive-spec.md](file:///c:/projetos/peito-infinity-v2/specs/06-ui-ux-responsive-spec.md) — Especificação de Interface Responsiva (Mobile & Desktop), Fluxos de Tela e Estados.
8. [07-verification-and-implementation-plan.md](file:///c:/projetos/peito-infinity-v2/specs/07-verification-and-implementation-plan.md) — Plano de Verificação, Testes de Aceitação e Roadmap de Implementação.
9. [guia-exercicios-seed.md](file:///c:/projetos/peito-infinity-v2/specs/data/guia-exercicios-seed.md) — Artefato de dados original para carga inicial do banco de dados.
