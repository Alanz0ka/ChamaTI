# ChamaTI — Sistema Web para Gerenciamento de Chamados de Suporte de TI

Aplicação web para registro e acompanhamento de chamados de suporte de TI,
desenvolvida como entrega da **Ação Curricular de Extensão 2 (ACEx2)** do Curso
Superior de Tecnologia em Sistemas para Internet da **UNCISAL**.

O sistema atende dois perfis de usuário:

- **Colaborador** — abre chamados e acompanha o andamento das próprias solicitações.
- **Técnico de TI** — visualiza todos os chamados em um painel (Kanban), assume e
  atualiza o status de cada atendimento.

## Funcionalidades

| Tela | Funcionalidade | Requisito |
|------|----------------|-----------|
| Login | Autenticação e controle de acesso por perfil | RF01 |
| Abrir chamado | Registro de nova solicitação com validação | RF02 |
| Meus chamados | Acompanhamento e filtro por status | RF03 |
| Atendimento | Painel do técnico: indicadores + Kanban | RF04 |
| Base de conhecimento | Artigos com busca e navegação por categorias | RF05 |

O projeto das telas seguiu princípios de **Interação Humano-Computador (IHC)**:
heurísticas de usabilidade de Nielsen, princípios de design de Norman e da Gestalt.
Destaques: consistência visual, visibilidade do status do sistema (etiquetas
coloridas — azul para *Aberto*, âmbar para *Em análise* e verde para *Concluído*),
prevenção de erros (campos estruturados e validação) e contraste adequado.

## Tecnologias

- **Python 3** com **Flask** (API REST + renderização das páginas)
- **HTML, CSS e JavaScript** (sem dependências de front-end)
- Armazenamento **em memória** (para fins didáticos, sem banco de dados)

## Estrutura do projeto

```
RegistroChamados/
├── app.py                       # Aplicação Flask (API + rotas das páginas)
├── requirements.txt             # Dependências
├── templates/                   # Páginas (Jinja2)
│   ├── base.html                # Layout comum (barra de navegação)
│   ├── login.html               # Tela 1 — Login (RF01)
│   ├── abrir_chamado.html       # Tela 2 — Abrir chamado (RF02)
│   ├── meus_chamados.html       # Tela 3 — Meus chamados (RF03)
│   ├── atendimento.html         # Tela 4 — Atendimento / Kanban (RF04)
│   └── base_conhecimento.html   # Tela 5 — Base de conhecimento (RF05)
└── static/
    ├── css/styles.css           # Design system (cores, tipografia, componentes)
    └── js/                       # Lógica de cada tela + utilitários (comum.js)
```

## Como executar

**Pré-requisitos:** Python 3 instalado.

```bash
# 1. (Opcional) criar e ativar um ambiente virtual
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. Instalar as dependências
pip install -r requirements.txt

# 3. Iniciar a aplicação
python app.py
```

A aplicação sobe em **http://localhost:5000**.

> **macOS — atenção à porta 5000.** No macOS, a porta 5000 costuma ser usada pelo
> *AirPlay Receiver*, o que impede o Flask de iniciar (e responde HTTP 403). Nesse
> caso, use outra porta:
>
> ```bash
> PORT=5001 python app.py        # acesse http://localhost:5001
> ```
>
> Alternativamente, desative *AirPlay Receiver* em
> *Ajustes do Sistema → Geral → AirDrop e Handoff*.

### Usuários de demonstração

| Perfil | E-mail (ou usuário) | Senha |
|--------|---------------------|-------|
| Colaborador | `colaborador@uncisal.edu.br` | `123456` |
| Técnico | `tecnico@uncisal.edu.br` | `123456` |

O login também aceita apenas o usuário institucional (parte antes do `@`),
por exemplo `tecnico`.

## API REST

| Método | Rota | Descrição | Requisito |
|--------|------|-----------|-----------|
| POST | `/api/login` | Autentica o usuário | RF01 |
| POST | `/api/logout` | Encerra a sessão | RF01 |
| GET | `/api/sessao` | Retorna o usuário logado | RF01 |
| GET | `/api/opcoes` | Categorias e urgências válidas | RF02 |
| POST | `/api/chamados` | Abre um novo chamado | RF02 |
| GET | `/api/chamados` | Lista chamados (`?meus=1`, `?status=`) | RF03 |
| GET | `/api/chamados/<id>` | Detalha um chamado | RF03 |
| GET | `/api/indicadores` | Métricas do painel (técnico) | RF04 |
| POST | `/api/chamados/<id>/assumir` | Técnico assume o chamado | RF04 |
| PATCH | `/api/chamados/<id>/status` | Atualiza o status do chamado | RF04 |
| GET | `/api/artigos` | Lista artigos (`?q=`, `?categoria=`) | RF05 |

### Exemplo — abrir um chamado (RF02)

```http
POST /api/chamados
Content-Type: application/json

{
  "categoria": "Software",
  "urgencia": "Alta",
  "assunto": "Erro ao acessar o sistema de folha de ponto",
  "descricao": "Recebo a mensagem de usuario ou senha invalidos."
}
```

Resposta `201 Created`:

```json
{
  "mensagem": "Chamado aberto com sucesso",
  "chamado": {
    "id": 1,
    "categoria": "Software",
    "urgencia": "Alta",
    "assunto": "Erro ao acessar o sistema de folha de ponto",
    "descricao": "Recebo a mensagem de usuario ou senha invalidos.",
    "status": "Aberto",
    "aberto_em": "2026-05-28T10:42:11"
  }
}
```

Campos inválidos retornam `400 Bad Request` com a descrição dos erros por campo.

## Observações

- Os dados ficam **em memória**: ao reiniciar a aplicação, a lista volta ao estado
  inicial, com alguns chamados de exemplo já cadastrados para demonstração.
- Projeto de finalidade **acadêmica**; não usar em produção sem persistência em
  banco de dados e tratamento adequado de autenticação.

## Autor

José Alan de Aquino Santos — UNCISAL, CST em Sistemas para Internet.
Orientadora: Profª. Drª. Edileuza Virginio Leão Mazza.
