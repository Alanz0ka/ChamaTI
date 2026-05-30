# ChamaTI — Sistema Web para Gerenciamento de Chamados de Suporte de TI

Aplicação web para registro e acompanhamento de chamados de suporte de TI,
desenvolvida como entrega da **Ação Curricular de Extensão 2 (ACEx2)** do Curso
Superior de Tecnologia em Sistemas para Internet da **UNCISAL**.

O sistema atende dois perfis de usuário:

- **Colaborador** — abre chamados (com anexo opcional), acompanha o andamento e
  consulta os detalhes das próprias solicitações.
- **Técnico de TI** — vê todos os chamados no painel (Kanban), filtra os que estão
  atribuídos a si, assume, atualiza o status e consulta o detalhe (incluindo anexos).
  Também pode **abrir chamados**, **cadastrar novos usuários** (colaboradores ou
  técnicos, definindo o perfil) e **manter a base de conhecimento** (criar, editar e
  excluir artigos).

## Funcionalidades

| Tela | Funcionalidade | Requisito |
|------|----------------|-----------|
| Login | Autenticação e controle de acesso por perfil | RF01 |
| Abrir chamado | Registro de nova solicitação com validação e anexo (imagem/PDF) | RF02 |
| Meus chamados | Acompanhamento, filtro por status e tela de detalhe | RF03 |
| Atendimento | Painel do técnico: indicadores, Kanban e filtro "atribuídos a mim" | RF04 |
| Base de conhecimento | Consulta (busca + categorias) para todos; gestão de artigos pelo técnico | RF05 |

Ao clicar em um chamado (na lista ou no Kanban), abre-se a **tela de detalhe**, que
mostra todas as informações, a descrição completa e o anexo (imagem exibida na própria
página ou link para o PDF).

O projeto das telas seguiu princípios de **Interação Humano-Computador (IHC)**:
heurísticas de usabilidade de Nielsen, princípios de design de Norman e da Gestalt.
Destaques: consistência visual, visibilidade do status do sistema (etiquetas
coloridas — azul para *Aberto*, âmbar para *Em análise* e verde para *Concluído*),
prevenção de erros (campos estruturados e validação) e contraste adequado.

## Tecnologias

- **Python 3** com **Flask** (API REST + renderização das páginas)
- **HTML, CSS e JavaScript** (sem dependências de front-end)
- Persistência em **SQLite** (`chamati.db`); anexos salvos em disco (`uploads/`)

## Estrutura do projeto

```
ChamaTI/
├── app.py                       # Ponto de entrada (cria o app via fábrica e executa)
├── requirements.txt             # Dependências
├── chamati/                     # Pacote da aplicação
│   ├── __init__.py              # create_app(): fábrica que registra os blueprints
│   ├── config.py                # Constantes, caminhos e usuários iniciais
│   ├── db.py                    # Conexão SQLite, helpers, init_db e dados de demonstração
│   ├── auth.py                  # login_obrigatorio, encontrar_usuario, pode_ver_chamado
│   ├── utils.py                 # Funções utilitárias (duração, validação de anexo)
│   ├── conteudo.py              # Artigos da base de conhecimento (RF05)
│   └── blueprints/              # Rotas agrupadas por área
│       ├── paginas.py           # Rotas das telas (HTML)
│       ├── auth_api.py          # Login, logout, sessão e opções (RF01)
│       ├── usuarios.py          # Cadastro/listagem de usuários (técnico)
│       ├── chamados.py          # Chamados: RF02/RF03/RF04 + anexo + indicadores
│       └── artigos.py           # Base de conhecimento (RF05)
├── templates/                   # Páginas (Jinja2)
│   ├── base.html                # Layout comum (barra de navegação)
│   ├── login.html               # Tela 1 — Login (RF01)
│   ├── abrir_chamado.html       # Tela 2 — Abrir chamado (RF02)
│   ├── meus_chamados.html       # Tela 3 — Meus chamados (RF03)
│   ├── atendimento.html         # Tela 4 — Atendimento / Kanban (RF04)
│   ├── chamado_detalhe.html     # Detalhe do chamado (com anexo)
│   ├── usuarios.html            # Cadastro/listagem de usuários (técnico)
│   └── base_conhecimento.html   # Tela 5 — Base de conhecimento (RF05)
├── static/
│   ├── css/styles.css           # Design system (cores, tipografia, componentes)
│   └── js/                       # Lógica de cada tela + utilitários (comum.js)
├── chamati.db                   # Banco SQLite (criado na 1ª execução)
└── uploads/                     # Anexos enviados (criado na 1ª execução)
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

Por segurança, estas credenciais **não aparecem na tela de login** — ficam apenas
nesta documentação:

| Perfil | E-mail (ou usuário) | Senha |
|--------|---------------------|-------|
| Colaborador | `colaborador@uncisal.edu.br` | `123456` |
| Técnico | `tecnico@uncisal.edu.br` | `123456` |

O login também aceita apenas o usuário institucional (parte antes do `@`),
por exemplo `tecnico`.

### Cadastro de novos usuários

Ao entrar como **técnico**, o menu exibe a opção **Usuários**, onde é possível
cadastrar novos acessos informando nome, e-mail, senha e o **perfil** (colaborador
ou técnico). O novo usuário já pode entrar com o e-mail e a senha definidos.

### Gestão da base de conhecimento

Para o **colaborador**, a base de conhecimento é apenas de consulta (busca e
navegação por categorias). O **técnico** vê, na mesma tela, as ações para **criar**,
**editar** e **excluir** artigos; o conteúdo fica salvo no banco e é compartilhado
com todos os usuários.

## API REST

| Método | Rota | Corpo | Descrição | Requisito |
|--------|------|-------|-----------|-----------|
| POST | `/api/login` | JSON | Autentica o usuário | RF01 |
| POST | `/api/logout` | — | Encerra a sessão | RF01 |
| GET | `/api/sessao` | — | Retorna o usuário logado | RF01 |
| GET | `/api/opcoes` | — | Categorias e urgências válidas | RF02 |
| POST | `/api/chamados` | JSON · multipart | Abre um novo chamado (multipart quando há anexo) | RF02 |
| GET | `/api/chamados` | — | Lista chamados (`?meus=1`, `?status=`, `?responsavel=me`) | RF03/RF04 |
| GET | `/api/chamados/<id>` | — | Detalha um chamado | RF03 |
| GET | `/api/chamados/<id>/anexo` | — | Baixa/exibe o anexo do chamado | RF03 |
| GET | `/api/indicadores` | — | Métricas do painel (técnico) | RF04 |
| POST | `/api/chamados/<id>/assumir` | — | Técnico assume o chamado | RF04 |
| PATCH | `/api/chamados/<id>/status` | JSON | Atualiza o status do chamado | RF04 |
| GET | `/api/usuarios` | — | Lista usuários (técnico) | RF01 |
| POST | `/api/usuarios` | JSON | Cadastra um usuário (técnico) | RF01 |
| GET | `/api/artigos` | — | Lista artigos (`?q=`, `?categoria=`) | RF05 |
| GET | `/api/artigos/<id>` | — | Detalha um artigo | RF05 |
| POST | `/api/artigos` | JSON | Cria um artigo (técnico) | RF05 |
| PUT | `/api/artigos/<id>` | JSON | Edita um artigo (técnico) | RF05 |
| DELETE | `/api/artigos/<id>` | — | Exclui um artigo (técnico) | RF05 |

### Tipos de corpo das requisições

As rotas de escrita usam **JSON** (`application/json`) — no Insomnia/Postman, selecione
**Body → JSON** e cole o conteúdo dos blocos abaixo. A única exceção é a abertura de
chamado **com anexo**, que exige **`multipart/form-data`** (JSON não transporta
arquivos); nesse caso, use **Body → Multipart Form**.

> **Anexo** — campo `anexo`, arquivo **PNG, JPG/JPEG ou PDF** de até **5 MB**. As
> imagens são exibidas na tela de detalhe; o PDF vira um link para download.

> **Sessão** — a autenticação é por **cookie**. Envie primeiro um `POST /api/login`; o
> Insomnia/Postman guarda o cookie automaticamente e o reutiliza nas chamadas seguintes.

### Corpos JSON (Body → JSON)

Cada bloco abaixo é um JSON pronto para copiar e colar.

**`POST /api/login`** — autentica (aceita `usuario`, a parte antes do `@`, ou `email`):

```json
{
  "usuario": "tecnico",
  "senha": "123456"
}
```

**`POST /api/chamados`** — abre um chamado sem anexo.
`categoria`: `Hardware` · `Software` · `Acessos` · `Rede e VPN` · `E-mail`.
`urgencia`: `Baixa` · `Media` · `Alta` (sem acento). `assunto` ≥ 5 e `descricao` ≥ 10 caracteres:

```json
{
  "categoria": "Software",
  "urgencia": "Alta",
  "assunto": "Erro ao acessar o sistema de folha de ponto",
  "descricao": "Recebo a mensagem de usuario ou senha invalidos."
}
```

**`PATCH /api/chamados/<id>/status`** — atualiza o status
(`Aberto`, `Em análise` ou `Concluído`, com acento):

```json
{
  "status": "Em análise"
}
```

**`POST /api/usuarios`** (técnico) — cadastra usuário.
`perfil`: `colaborador` ou `tecnico`; `senha` ≥ 6 caracteres:

```json
{
  "nome": "Ana Pereira",
  "email": "ana@uncisal.edu.br",
  "senha": "segredo123",
  "perfil": "colaborador"
}
```

**`POST /api/artigos`** e **`PUT /api/artigos/<id>`** (técnico) — cria/edita artigo:

```json
{
  "categoria": "Software",
  "titulo": "Como redefinir a senha",
  "resumo": "Passo a passo da redefinicao.",
  "conteudo": "1. Acesse o portal e clique em Esqueci a senha..."
}
```

### Abrir chamado com anexo (Body → Multipart Form)

Quando houver arquivo, **não use JSON**: selecione **Body → Multipart Form** e preencha
os campos abaixo. Não defina o `Content-Type` à mão — o cliente preenche o `boundary`:

| Campo | Tipo | Exemplo |
|-------|------|---------|
| `categoria` | Text | `Hardware` |
| `urgencia` | Text | `Media` |
| `assunto` | Text | `Monitor sem imagem` |
| `descricao` | Text | `O monitor da estacao 12 nao exibe nada ao ligar.` |
| `anexo` | **File** | selecione um PNG, JPG/JPEG ou PDF (até 5 MB) |

### Resposta — `201 Created`

Tanto em JSON quanto em multipart, a abertura responde com o chamado criado. Com anexo,
`tem_anexo` vem `true` e `anexo_nome` preenchido:

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
    "aberto_em": "2026-05-28T10:42:11",
    "tem_anexo": false,
    "anexo_nome": null
  }
}
```

Campos inválidos — categoria/urgência fora da lista, assunto < 5 ou descrição < 10
caracteres, anexo em formato ou tamanho não aceito — retornam `400 Bad Request` com os
erros por campo.

## Observações

- Os dados são gravados em **SQLite** (`chamati.db`) e os anexos em `uploads/`, ambos
  criados automaticamente na primeira execução e **mantidos entre reinícios**. Na
  primeira vez, alguns chamados de exemplo são cadastrados para demonstração.
- Para recomeçar do zero, basta apagar o arquivo `chamati.db` (e, opcionalmente, a
  pasta `uploads/`); ele será recriado e populado novamente.
- Projeto de finalidade **acadêmica**; não usar em produção sem tratamento adequado de
  autenticação (senhas em texto puro e sessão simples são apenas para demonstração).

## Autor

José Alan de Aquino Santos — UNCISAL, CST em Sistemas para Internet.
Orientadora: Profª. Drª. Edileuza Virginio Leão Mazza.
