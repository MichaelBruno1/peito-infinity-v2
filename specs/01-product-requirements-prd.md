# 01. Documento de Requisitos de Produto (PRD)

**Projeto:** Peito Infinity  
**Documento:** Especificação de Requisitos Funcionais, Não-Funcionais, Regras de Negócio e User Stories  
**Status:** Especificação Base (SDD)  

---

## 1. Escopo do Produto

O **Peito Infinity** resolve o problema de criação, adaptação e consulta de treinos personalizados de academia em ambiente residencial/doméstico. Qualquer usuário conectado à rede local pode abrir o navegador no celular ou computador, selecionar ou criar seu perfil sem precisar de login/senha, revisar quais exercícios não quer fazer, e acionar um Agente LLM Especialista que prescreve toda a programação semanal ou recria o treino de um único dia, respeitando rigorosamente o tempo disponível em minutos, o objetivo fisiológico, o nível de experiência e a base oficial de exercícios no PostgreSQL.

### 1.1 O que está no Escopo (In-Scope)
- Criação, listagem, seleção e edição completa de perfis de usuário sem autenticação.
- Importação automática (seed na 1ª execução) da tabela de exercícios do arquivo Markdown para o banco PostgreSQL.
- Uso exclusivo do PostgreSQL como fonte de dados para listagem e geração de treinos.
- Tela/modal pré-geração para visualização de todos os exercícios do banco e seleção de exercícios a serem **excluídos** da montagem do treino.
- Geração de treino completo (todos os dias da semana definidos no perfil) via Agente LLM especialista.
- Regeneração individual de um único dia de treino específico via Agente LLM especialista, mantendo os demais dias inalterados.
- Inclusão de exercícios cardiovasculares nos treinos informando **apenas o tempo** (ex: `40 min de cardio`).
- Interface web responsiva para navegadores Mobile (smartphones) e Desktop.
- Empacotamento completo em containers Docker (PostgreSQL, Back-end Python FastAPI, Front-end JavaScript React).

### 1.2 O que está Fora do Escopo (Out-of-Scope)
- Autenticação de usuários (login, senha, OAuth, recuperação de e-mail, controle de acesso por papéis/RBAC).
- Aplicativos nativos compilados para lojas (iOS App Store / Google Play) — o acesso é 100% via navegador web responsivo (podendo suportar manifesto PWA para atalho na tela inicial).
- Edição manual do arquivo Markdown após a carga inicial (o banco PostgreSQL passa a ser a única fonte de verdade).
- Prescrição de séries, repetições ou velocidade/inclinação para exercícios cardiovasculares (apenas o tempo em minutos deve ser informado).

---

## 2. Requisitos Funcionais (RF)

| ID | Requisito | Descrição Detalhada | Prioridade |
| :--- | :--- | :--- | :--- |
| **RF-01** | **Listagem e Seleção de Perfil sem Login** | Ao acessar o aplicativo, o usuário deve visualizar imediatamente os perfis cadastrados na rede doméstica para selecionar o seu com 1 clique, além de um botão para criar um novo perfil. | Alta |
| **RF-02** | **Criação de Perfil de Usuário** | O sistema deve permitir criar um perfil informando obrigatoriamente: **Nome**, **Peso (kg)**, **Altura (cm)**, **Nível de condicionamento físico** (`Iniciante`, `Intermediário`, `Avançado`), **Objetivo** (`Emagrecimento`, `Hipertrofia`, `Treino de Força`), **Tempo disponível por dia de treino (minutos)** e **Quantidade de dias na semana que irá treinar** (`1` a `7`). | Alta |
| **RF-03** | **Edição de Dados do Perfil** | Todos os dados de um perfil existente (nome, peso, altura, condicionamento, objetivo, tempo disponível em minutos e dias na semana) devem poder ser editados e salvos a qualquer momento. | Alta |
| **RF-04** | **Exclusão de Perfil** | O usuário deve poder remover um perfil (e seus respectivos treinos) caso deseje limpar perfis antigos, mediante confirmação simples em tela. | Média |
| **RF-05** | **Importação Inicial (Seed) do Catálogo de Exercícios** | Na primeira inicialização do sistema, o back-end deve ler o arquivo [guia-exercicios-seed.md](file:///c:/projetos/peito-infinity-v2/specs/data/guia-exercicios-seed.md) e importar todos os 89 exercícios (com grupo muscular, nome popular, músculo principal, músculos secundários, complexidade e nota de eficiência), além das diretrizes do especialista, para o banco de dados PostgreSQL. | Alta |
| **RF-06** | **Consulta de Exercícios Exclusivamente via Banco de Dados** | Toda exibição do catálogo de exercícios no front-end e toda injeção de exercícios no prompt do Agente LLM deve ter como origem exclusiva as tabelas do PostgreSQL. | Alta |
| **RF-07** | **Etapa Pré-Geração: Exclusão de Exercícios pelo Usuário** | Antes de disparar qualquer geração de treino (seja o treino completo ou o treino de um dia específico), o sistema deve exibir ao usuário a lista de exercícios agrupada por grupo muscular (com filtro de busca textual e seleção rápida) para que ele indique se quer **excluir algum exercício** da montagem. | Alta |
| **RF-08** | **Persistência das Preferências de Exclusão por Perfil** | A seleção de exercícios excluídos deve ficar salva no perfil do usuário como pré-seleção padrão para as próximas gerações, podendo ser alterada livremente no modal de pré-geração antes de confirmar cada novo treino. | Média |
| **RF-09** | **Geração de Treino Completo do Zero via Agente LLM** | O usuário deve poder solicitar a geração completa do seu plano de treinamento semanal (contendo exatamente $N$ dias de treino, onde $N$ é o número de dias na semana configurado no perfil). O Agente LLM especialista deve montar a divisão ideal e selecionar os exercícios permitidos do banco. | Alta |
| **RF-10** | **Regeneração de Treino de um Dia Específico via Agente LLM** | O usuário deve poder solicitar a geração de um novo treino **apenas para um dia específico** (ex: regenerar apenas o "Dia 2"), mantendo os outros dias do plano semanal inalterados. | Alta |
| **RF-11** | **Regra de Exibição e Prescrição de Cardio** | Exercícios cardiovasculares devem ser incluídos nos dias de treino pelo Agente LLM (conforme objetivo e tempo disponível) informando **apenas o tempo em minutos**, no formato `"X min de cardio"` (ex: `"40 min de cardio"`). | Alta |
| **RF-12** | **Visualização Detalhada do Treino por Dia** | A tela do perfil deve exibir o plano de treino organizado por abas/cards dos dias da semana (Dia 1 a Dia $N$). Em cada dia, devem ser listados os exercícios de musculação (ordem, nome, músculo principal, complexidade, séries, repetições, descanso estimado e observação técnica curta) e o bloco de cardio (`"X min de cardio"`). | Alta |
| **RF-13** | **Histórico / Substituição Ilimitada de Treinos** | O usuário pode gerar o treino completo ou regenerar um dia específico **quantas vezes quiser**, sem limite de requisições. | Alta |

---

## 3. Requisitos Não-Funcionais (RNF)

| ID | Categoria | Especificação |
| :--- | :--- | :--- |
| **RNF-01** | **Responsividade (Mobile & Desktop)** | A interface deve utilizar design responsivo fluido (*Mobile-First*), adaptando-se perfeitamente a telas desde `320px` (smartphones verticais na academia) até `1920px+` (monitores desktop), sem rolagem horizontal indevida e com alvos de toque mínimos de `44x44px` no mobile. |
| **RNF-02** | **Rede Doméstica e Privada (Zero Auth)** | O sistema deve rodar em rede local (`0.0.0.0` exposto na LAN doméstica via Docker) sem exigir autenticação, certificados externos complexos ou contas na nuvem para gerenciamento de usuários. |
| **RNF-03** | **Containerização (Docker)** | Toda a aplicação deve subir com um único comando `docker compose up -d --build`, contendo containers dedicados para `db` (PostgreSQL), `backend` (Python/FastAPI) e `frontend` (JavaScript/React + Nginx). |
| **RNF-04** | **Persistência de Dados** | Os dados do PostgreSQL devem ser persistidos em um Docker Named Volume (`postgres_data`), garantindo que perfis, treinos gerados e os exercícios importados no seed não sejam perdidos ao reiniciar os containers. |
| **RNF-05** | **Confiabilidade da Saída do LLM** | O Agente LLM deve utilizar *Structured Outputs* (JSON Schema / Pydantic) e validação pós-geração no back-end para garantir que: (a) apenas exercícios existentes no banco PostgreSQL sejam utilizados; (b) nenhum exercício da lista de exclusão do usuário apareça no treino; e (c) o cardio apareça estritamente no formato `"X min de cardio"`. |
| **RNF-06** | **Desempenho e Feedback Visual** | Operações CRUD (perfis e listagem de exercícios/treinos) devem responder em `< 200ms` na rede local. Durante a geração de treino pelo LLM (que pode levar de `3s` a `15s`), a UI deve exibir estados claros de carregamento (*skeletons* / mensagens de progresso do Agente Especialista). |

---

## 4. Regras de Negócio (RN)

### RN-01: Validação dos Atributos do Perfil
- **Nome:** Obrigatório, entre 2 e 80 caracteres.
- **Peso:** Obrigatório, numérico positivo entre `25.0 kg` e `300.0 kg`.
- **Altura:** Obrigatória, numérica positiva entre `100 cm` e `250 cm`.
- **Nível de Condicionamento Físico:** Enumeração estrita:
  - `INICIANTE` (Iniciante)
  - `INTERMEDIARIO` (Intermediário)
  - `AVANCADO` (Avançado)
- **Objetivo:** Enumeração estrita:
  - `EMAGRECIMENTO` (Emagrecimento)
  - `HIPERTROFIA` (Hipertrofia)
  - `FORCA` (Treino de Força)
- **Tempo Disponível por Dia:** Inteiro positivo entre `20` e `240` minutos.
- **Dias de Treino na Semana:** Inteiro entre `1` e `7` dias.

### RN-02: Fonte de Dados e Imutabilidade do Fluxo de Seed
- Na inicialização do container `backend`, o serviço verifica a tabela `exercises` no PostgreSQL.
- Se `COUNT(*) == 0`, o parser lê `specs/data/guia-exercicios-seed.md`, extrai os 89 exercícios distribuídos nas 9 categorias musculares, converte os ícones de complexidade (`🟢 Baixa` -> `BAIXA`, `🟡 Média` -> `MEDIA`, `🔴 Alta` -> `ALTA`) e a nota de eficiência (`9.8/10` -> `9.8`), e grava no PostgreSQL.
- Se `COUNT(*) > 0`, o arquivo Markdown é ignorado.
- Em tempo de execução, **nenhuma rota da API ou chamada do Agente LLM lê o arquivo Markdown**; tudo é consultado via SQL no PostgreSQL.

### RN-03: Ordenação por Blocos de Grupo Muscular (Maior -> Menor) e Complexidade Biomecânica
O Agente LLM Especialista deve obedecer às quatro regras de ouro de prescrição:
1. **Agrupamento Contíguo por Grupo Muscular (Zero Intercalação):** Todos os exercícios de um mesmo grupo muscular devem ficar juntos em sequência na sessão. É proibido intercalar grupos (ex: nunca fazer Peito -> Core -> Peito).
2. **Hierarquia de Tamanho do Grupo Muscular (Maior $\rightarrow$ Menor $\rightarrow$ Core):**
   - **1º — Grandes Grupos Musculares:** `1. Peitoral (Peito)`, `2. Costas`, `3. Quadríceps`, `4. Posterior de Coxa e Glúteos`.
   - **2º — Grupos Musculares Médios:** `5. Ombros (Deltoides) e Trapézio`.
   - **3º — Grupos Musculares Menores:** `6. Bíceps e Antebraço`, `7. Tríceps`, `8. Panturrilhas e Tibial`.
   - **4º — Core / Estabilizadores (Final):** `9. Abdômen e Core`.
3. **Ordem Biomecânica Interna em Cada Grupo Muscular:** Dentro do bloco de cada músculo, iniciar pelos exercícios multiarticulares de complexidade **Alta (🔴)** ou **Média (🟡)** e posicionar os exercícios de complexidade **Baixa (🟢)** e alta eficiência ao final daquele bloco muscular como finalizadores seguros.
4. **Anti-Redundância Biomecânica:** Nunca alocar no mesmo dia de treino exercícios com exatamente o mesmo padrão biomecânico e ângulo (ex: proibido prescrever *Supino Reto com Barra*, *Supino Reto com Halteres* e *Supino Máquina* na mesma sessão; deve-se variar os ângulos, como Reto + Inclinado + Crucifixo/Peck Deck).

### RN-04: Dimensionamento de Tempo (Musculação + Cardio)
- A soma do tempo estimado dos exercícios de musculação + o tempo de cardio prescrito para o dia **não deve ultrapassar o tempo disponível em minutos** configurado no perfil do usuário.
- O formato do exercício cardiovascular deve ser sempre exibido como texto direto de duração: `"{tempo} min de cardio"` (ex: `"40 min de cardio"`, `"20 min de cardio"`).

### RN-05: Alteração de Dias na Semana na Edição de Perfil
- Se o usuário editar seu perfil e alterar a quantidade de dias na semana (ex: de 3 dias para 5 dias), a interface manterá o treino atual visível com um aviso sugerindo gerar um novo treino completo para se adequar à nova frequência semanal de 5 dias.

---

## 5. Histórias de Usuário e Critérios de Aceite (Gherkin)

### US-01: Criar e Editar Perfil sem Autenticação
> **Como** usuário na minha rede doméstica,  
> **Quero** criar e editar meu perfil informando meus dados físicos, objetivo e rotina direto na tela do aplicativo sem precisar de login,  
> **Para que** eu possa acessar e atualizar rapidamente minhas configurações de treino em qualquer dispositivo da casa.

**Critérios de Aceite:**
```gherkin
Cenário: Criação de um novo perfil com sucesso
  Dado que o usuário acessou o Peito Infinity pelo navegador sem qualquer tela de login
  Quando ele clica em "Novo Perfil" e preenche:
    | Campo                        | Valor            |
    | Nome                         | Carlos Silva     |
    | Peso (kg)                    | 82.5             |
    | Altura (cm)                  | 178              |
    | Nível de Condicionamento     | Intermediário    |
    | Objetivo                     | Hipertrofia      |
    | Tempo Disponível (minutos)   | 60               |
    | Dias na Semana               | 4                |
  E clica em "Salvar Perfil"
  Então o perfil "Carlos Silva" é persistido no banco de dados PostgreSQL
  E o usuário é direcionado imediatamente para o painel do seu perfil.

Cenário: Edição de dados de um perfil existente
  Dado que o perfil "Carlos Silva" já existe e está selecionado
  Quando o usuário clica em "Editar Perfil"
  E altera o "Objetivo" para "Emagrecimento" e o "Tempo Disponível" para "75" minutos
  E confirma a alteração
  Então os novos dados são atualizados no PostgreSQL
  E as próximas gerações de treino passam a utilizar o objetivo "Emagrecimento" e o limite de 75 minutos.
```

---

### US-02: Excluir Exercícios Indesejados Antes de Gerar o Treino
> **Como** usuário do Peito Infinity,  
> **Quero** visualizar a lista de exercícios antes de gerar o treino e marcar quais exercícios desejo excluir,  
> **Para que** o Agente LLM não inclua aparelhos que não existem na minha academia ou movimentos que me causam desconforto.

**Critérios de Aceite:**
```gherkin
Cenário: Exibição e exclusão prévia de exercícios antes da geração
  Dado que o usuário está na tela do seu perfil e clica em "Gerar Treino Completo" (ou "Gerar Novo Treino para Este Dia")
  Quando o modal de revisão de exercícios é aberto antes de acionar a IA
  Então o sistema exibe os exercícios carregados do PostgreSQL organizados pelos 9 grupos musculares
  Quando o usuário marca para excluir "Agachamento Livre com Barra" e "Levantamento Terra Tradicional"
  E confirma clicando em "Gerar Treino Agora"
  Então a requisição enviada ao Back-end contém a lista de IDs excluídos
  E o Agente LLM gera o treino sem incluir "Agachamento Livre com Barra" nem "Levantamento Terra Tradicional" em nenhum dia.
```

---

### US-03: Gerar Treino Completo do Zero com Agente LLM e Cardio em Minutos
> **Como** usuário do Peito Infinity,  
> **Quero** que um Agente LLM especialista monte todo o meu treinamento semanal do zero, incluindo cardio apenas com o tempo,  
> **Para que** eu tenha uma rotina otimizada para meu corpo, objetivo e tempo disponível.

**Critérios de Aceite:**
```gherkin
Cenário: Geração de treinamento semanal completo do zero
  Dado um perfil com objetivo "Emagrecimento", nível "Iniciante", 60 minutos por dia e 3 dias na semana
  E que o usuário já revisou a tela de exclusão de exercícios
  Quando ele confirma a geração do treino completo do zero
  Então o Agente LLM Especialista processa os parâmetros do perfil e os exercícios permitidos do PostgreSQL
  E retorna um plano contendo exatamente 3 dias de treino
  E cada dia de treino ordena exercícios de complexidade Média/Alta antes dos exercícios de complexidade Baixa
  E os exercícios cardiovasculares aparecem informando apenas o tempo (exemplo: "30 min de cardio" ou "40 min de cardio").
```

---

### US-04: Regenerar Apenas o Treino de um Dia Específico
> **Como** usuário que já possui um plano de treino semanal gerado,  
> **Quero** poder gerar novamente apenas o treino de um dia específico (ou gerar todo o treino do zero novamente quantas vezes eu quiser),  
> **Para que** eu possa variar o treino daquele dia sem perder os treinos dos outros dias da semana que eu gostei.

**Critérios de Aceite:**
```gherkin
Cenário: Regeneração exclusiva de um único dia de treino
  Dado que o usuário possui um Plano de Treino ativo de 4 dias (Dia 1, Dia 2, Dia 3 e Dia 4)
  Quando ele visualiza o "Dia 2" e clica em "Gerar Novo Treino para Este Dia"
  E confirma (após poder ajustar a lista de exercícios excluídos no modal pré-geração)
  Então o Agente LLM gera uma nova prescrição exclusivamente para o "Dia 2" mantendo a coerência com o foco muscular do dia
  E os treinos do "Dia 1", "Dia 3" e "Dia 4" permanecem 100% intactos no banco de dados.
```
