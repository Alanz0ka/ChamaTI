"""
ChamaTI - Sistema Web para Gerenciamento de Chamados de Suporte de TI

Funcionalidades (Ação Curricular de Extensão 2):
    RF01 - Autenticacao e Controle de Acesso (login/logout por perfil)
    RF02 - Abertura de Chamado (com anexo opcional: imagem ou PDF)
    RF03 - Acompanhamento de Chamados (lista, filtro e detalhe)
    RF04 - Gestao e Atendimento (painel do tecnico: indicadores e Kanban)
    RF05 - Base de Conhecimento

Persistencia: banco de dados SQLite (chamati.db); anexos salvos em uploads/.

Execucao:
    pip install flask
    python app.py

A aplicacao sobe em http://localhost:5000

Usuarios de demonstracao (senha: 123456):
    colaborador@uncisal.edu.br  -> perfil colaborador
    tecnico@uncisal.edu.br      -> perfil tecnico
"""
import os
import sqlite3
import uuid
from datetime import datetime, timedelta
from functools import wraps

from flask import (
    Flask,
    abort,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "chamati-chave-de-desenvolvimento"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "chamati.db")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")

# Anexos: extensoes aceitas e tamanho maximo (5 MB)
EXTENSOES_OK = {".png", ".jpg", ".jpeg", ".pdf"}
EXTENSOES_IMAGEM = {".png", ".jpg", ".jpeg"}
TAM_MAX = 5 * 1024 * 1024
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024  # margem para o arquivo + campos

# Valores aceitos para validacao (RF02)
CATEGORIAS = {"Hardware", "Software", "Acessos", "Rede e VPN", "E-mail"}
URGENCIAS = {"Baixa", "Media", "Alta"}
ORDEM_URGENCIAS = ["Baixa", "Media", "Alta"]

# Status do fluxo de atendimento (codificacao de cores no front-end:
# azul = Aberto, ambar = Em analise, verde = Concluido)
STATUS_VALIDOS = ["Aberto", "Em análise", "Concluído"]

# Perfis de acesso (RF01)
PERFIS_VALIDOS = {"colaborador", "tecnico"}

# Usuarios iniciais (seed) - criados na 1a execucao; novos sao cadastrados no app
USUARIOS_PADRAO = {
    "colaborador@uncisal.edu.br": {
        "senha": "123456",
        "nome": "Maria Souza",
        "perfil": "colaborador",
    },
    "tecnico@uncisal.edu.br": {
        "senha": "123456",
        "nome": "Carlos Lima",
        "perfil": "tecnico",
    },
}

# Base de conhecimento (RF05) - conteudo estatico
ARTIGOS = [
    {
        "id": 1,
        "categoria": "Acessos",
        "titulo": "Como redefinir sua senha institucional",
        "resumo": "Passo a passo para recuperar o acesso sem abrir um chamado.",
        "conteudo": (
            "1. Acesse a tela de login e clique em \"Esqueci minha senha\".\n"
            "2. Informe seu e-mail institucional.\n"
            "3. Siga o link enviado para a sua caixa de entrada.\n"
            "4. Cadastre uma nova senha com pelo menos 8 caracteres."
        ),
    },
    {
        "id": 2,
        "categoria": "Rede e VPN",
        "titulo": "Conectando-se à VPN da instituição",
        "resumo": "Configuração da VPN para acesso remoto seguro.",
        "conteudo": (
            "1. Instale o cliente de VPN indicado pela TI.\n"
            "2. Use seu usuário institucional e senha.\n"
            "3. Em caso de quedas frequentes, prefira uma rede cabeada.\n"
            "4. Persistindo o problema, abra um chamado na categoria Rede e VPN."
        ),
    },
    {
        "id": 3,
        "categoria": "E-mail",
        "titulo": "Configurando o e-mail no celular",
        "resumo": "Adicione a conta institucional no aplicativo de e-mail.",
        "conteudo": (
            "1. Adicione uma nova conta do tipo Exchange/IMAP.\n"
            "2. Informe o e-mail e a senha institucionais.\n"
            "3. Aceite as configurações de segurança solicitadas."
        ),
    },
    {
        "id": 4,
        "categoria": "Hardware",
        "titulo": "Impressora não imprime: o que verificar",
        "resumo": "Checklist rápido antes de abrir um chamado de impressora.",
        "conteudo": (
            "1. Verifique se há papel e toner.\n"
            "2. Confira se a impressora está ligada e conectada à rede.\n"
            "3. Reinicie a fila de impressão no seu computador.\n"
            "4. Se o erro continuar, abra um chamado na categoria Hardware."
        ),
    },
    {
        "id": 5,
        "categoria": "Software",
        "titulo": "Erro \"usuário ou senha inválidos\" nos sistemas",
        "resumo": "Causas comuns e como resolver rapidamente.",
        "conteudo": (
            "1. Confirme se o Caps Lock está desativado.\n"
            "2. Verifique se a senha não expirou.\n"
            "3. Limpe o cache do navegador e tente novamente.\n"
            "4. Caso persista, abra um chamado na categoria Software."
        ),
    },
]


# ---------------------------------------------------------------------------
# Banco de dados (SQLite)
# ---------------------------------------------------------------------------
def conectar():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def consultar(sql, params=(), um=False):
    conn = conectar()
    try:
        cur = conn.execute(sql, params)
        return cur.fetchone() if um else cur.fetchall()
    finally:
        conn.close()


def executar(sql, params=()):
    conn = conectar()
    try:
        cur = conn.execute(sql, params)
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def init_db():
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    conn = conectar()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chamados (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                categoria        TEXT NOT NULL,
                urgencia         TEXT NOT NULL,
                assunto          TEXT NOT NULL,
                descricao        TEXT NOT NULL,
                status           TEXT NOT NULL DEFAULT 'Aberto',
                aberto_em        TEXT NOT NULL,
                atualizado_em    TEXT NOT NULL,
                concluido_em     TEXT,
                solicitante      TEXT,
                solicitante_nome TEXT,
                responsavel      TEXT,
                responsavel_nome TEXT,
                anexo            TEXT,
                anexo_nome       TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS usuarios (
                email   TEXT PRIMARY KEY,
                nome    TEXT NOT NULL,
                senha   TEXT NOT NULL,
                perfil  TEXT NOT NULL
            )
            """
        )
        conn.commit()
    finally:
        conn.close()
    seed_usuarios_se_vazio()
    seed_se_vazio()


def chamado_dict(row):
    """Converte uma linha do banco no formato esperado pela API/telas.
    O caminho interno do anexo nao e exposto; em vez disso usa-se tem_anexo."""
    return {
        "id": row["id"],
        "categoria": row["categoria"],
        "urgencia": row["urgencia"],
        "assunto": row["assunto"],
        "descricao": row["descricao"],
        "status": row["status"],
        "aberto_em": row["aberto_em"],
        "atualizado_em": row["atualizado_em"],
        "concluido_em": row["concluido_em"],
        "solicitante": row["solicitante"],
        "solicitante_nome": row["solicitante_nome"],
        "responsavel": row["responsavel"],
        "responsavel_nome": row["responsavel_nome"],
        "tem_anexo": bool(row["anexo"]),
        "anexo_nome": row["anexo_nome"],
    }


def buscar_chamado(chamado_id):
    return consultar("SELECT * FROM chamados WHERE id = ?", (chamado_id,), um=True)


# ---------------------------------------------------------------------------
# Utilitarios
# ---------------------------------------------------------------------------
def seed_usuarios_se_vazio():
    """Cadastra os usuarios iniciais apenas se a tabela estiver vazia."""
    total = consultar("SELECT COUNT(*) c FROM usuarios", um=True)["c"]
    if total:
        return
    for email, dados in USUARIOS_PADRAO.items():
        executar(
            "INSERT INTO usuarios (email, nome, senha, perfil) VALUES (?, ?, ?, ?)",
            (email, dados["nome"], dados["senha"], dados["perfil"]),
        )


def encontrar_usuario(identificador):
    """Localiza um usuario por e-mail completo ou pelo usuario institucional
    (parte antes do @)."""
    identificador = (identificador or "").strip().lower()
    if not identificador:
        return None
    row = consultar("SELECT * FROM usuarios WHERE email = ?", (identificador,), um=True)
    if not row:
        for r in consultar("SELECT * FROM usuarios"):
            if r["email"].split("@")[0] == identificador:
                row = r
                break
    if not row:
        return None
    return {"email": row["email"], "nome": row["nome"], "senha": row["senha"], "perfil": row["perfil"]}


def formatar_duracao(td):
    total_min = int(td.total_seconds() // 60)
    horas, minutos = divmod(total_min, 60)
    if horas and minutos:
        return f"{horas}h {minutos}min"
    if horas:
        return f"{horas}h"
    return f"{minutos}min"


def validar_anexo(arquivo):
    """Retorna (extensao, mensagem_de_erro). Extensao None se nao houver arquivo."""
    if not arquivo or not arquivo.filename:
        return None, None
    ext = os.path.splitext(arquivo.filename)[1].lower()
    if ext not in EXTENSOES_OK:
        return None, "Formato não aceito. Use PNG, JPG ou PDF."
    arquivo.seek(0, os.SEEK_END)
    tamanho = arquivo.tell()
    arquivo.seek(0)
    if tamanho > TAM_MAX:
        return None, "O arquivo excede o limite de 5 MB."
    return ext, None


def login_obrigatorio(perfis=None):
    """Garante autenticacao. Em rotas /api/* responde JSON; nas paginas redireciona."""
    def decorador(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            usuario = session.get("usuario")
            eh_api = request.path.startswith("/api/")
            if not usuario:
                if eh_api:
                    return jsonify({"erro": "Não autenticado"}), 401
                return redirect(url_for("pagina_login"))
            if perfis and usuario["perfil"] not in perfis:
                if eh_api:
                    return jsonify({"erro": "Acesso negado"}), 403
                return redirect(url_for("index"))
            return view(*args, **kwargs)
        return wrapper
    return decorador


def pode_ver_chamado(row, usuario):
    """Tecnico ve qualquer chamado; colaborador apenas os proprios."""
    return usuario["perfil"] == "tecnico" or row["solicitante"] == usuario["email"]


# ---------------------------------------------------------------------------
# RF01 - Autenticacao e Controle de Acesso
# ---------------------------------------------------------------------------
@app.route("/api/login", methods=["POST"])
def api_login():
    dados = request.get_json(silent=True) or {}
    identificador = dados.get("usuario") or dados.get("email") or ""
    senha = dados.get("senha") or ""

    usuario = encontrar_usuario(identificador)
    if not usuario or usuario["senha"] != senha:
        return jsonify({"erro": "E-mail/usuário ou senha inválidos."}), 401

    session["usuario"] = {
        "email": usuario["email"],
        "nome": usuario["nome"],
        "perfil": usuario["perfil"],
    }
    return jsonify({"mensagem": "Login realizado", "usuario": session["usuario"]}), 200


@app.route("/api/logout", methods=["POST"])
def api_logout():
    session.pop("usuario", None)
    return jsonify({"mensagem": "Sessão encerrada"}), 200


@app.route("/api/sessao", methods=["GET"])
def api_sessao():
    return jsonify({"usuario": session.get("usuario")}), 200


@app.route("/api/opcoes", methods=["GET"])
def api_opcoes():
    """Opcoes oficiais para os formularios, mantendo o front-end alinhado a
    validacao do back-end."""
    return jsonify({"categorias": sorted(CATEGORIAS), "urgencias": ORDEM_URGENCIAS}), 200


# ---------------------------------------------------------------------------
# Gestao de usuarios (somente tecnico)
# ---------------------------------------------------------------------------
@app.route("/api/usuarios", methods=["GET"])
@login_obrigatorio(perfis=["tecnico"])
def api_listar_usuarios():
    rows = consultar("SELECT email, nome, perfil FROM usuarios ORDER BY perfil, nome")
    return jsonify({"total": len(rows), "usuarios": [dict(r) for r in rows]}), 200


@app.route("/api/usuarios", methods=["POST"])
@login_obrigatorio(perfis=["tecnico"])
def api_criar_usuario():
    dados = request.get_json(silent=True) or {}
    nome = (dados.get("nome") or "").strip()
    email = (dados.get("email") or "").strip().lower()
    senha = dados.get("senha") or ""
    perfil = (dados.get("perfil") or "").strip()

    erros = {}
    if len(nome) < 2:
        erros["nome"] = "Informe o nome completo."
    if "@" not in email or len(email) < 5:
        erros["email"] = "Informe um e-mail válido."
    elif consultar("SELECT 1 FROM usuarios WHERE email = ?", (email,), um=True):
        erros["email"] = "Já existe um usuário com este e-mail."
    if len(senha) < 6:
        erros["senha"] = "A senha deve ter ao menos 6 caracteres."
    if perfil not in PERFIS_VALIDOS:
        erros["perfil"] = "Selecione um perfil válido."

    if erros:
        return jsonify({"erro": "Dados invalidos", "campos": erros}), 400

    executar(
        "INSERT INTO usuarios (email, nome, senha, perfil) VALUES (?, ?, ?, ?)",
        (email, nome, senha, perfil),
    )
    return jsonify({
        "mensagem": "Usuário criado com sucesso",
        "usuario": {"email": email, "nome": nome, "perfil": perfil},
    }), 201


# ---------------------------------------------------------------------------
# RF02 - Abertura de Chamado
# ---------------------------------------------------------------------------
@app.route("/api/chamados", methods=["POST"])
def abrir_chamado():
    """Abre um novo chamado de suporte (RF02).

    Aceita JSON (contrato documentado) ou multipart/form-data quando ha anexo.
    """
    if request.content_type and "application/json" in request.content_type:
        dados = request.get_json(silent=True) or {}
        arquivo = None
    else:
        dados = request.form
        arquivo = request.files.get("anexo")

    # Validacao dos campos obrigatorios
    erros = {}
    categoria = (dados.get("categoria") or "").strip()
    urgencia = (dados.get("urgencia") or "").strip()
    assunto = (dados.get("assunto") or "").strip()
    descricao = (dados.get("descricao") or "").strip()

    if categoria not in CATEGORIAS:
        erros["categoria"] = f"Categoria invalida. Use uma de: {sorted(CATEGORIAS)}"
    if urgencia not in URGENCIAS:
        erros["urgencia"] = f"Urgencia invalida. Use uma de: {sorted(URGENCIAS)}"
    if len(assunto) < 5:
        erros["assunto"] = "O assunto deve ter ao menos 5 caracteres."
    if len(descricao) < 10:
        erros["descricao"] = "A descricao deve ter ao menos 10 caracteres."

    ext, erro_anexo = validar_anexo(arquivo)
    if erro_anexo:
        erros["anexo"] = erro_anexo

    if erros:
        return jsonify({"erro": "Dados invalidos", "campos": erros}), 400

    # Salva o anexo, se houver
    anexo_armazenado = None
    anexo_nome = None
    if ext:
        anexo_armazenado = uuid.uuid4().hex + ext
        anexo_nome = secure_filename(arquivo.filename) or ("anexo" + ext)
        arquivo.save(os.path.join(UPLOAD_DIR, anexo_armazenado))

    usuario = session.get("usuario")
    agora = datetime.now().isoformat(timespec="seconds")
    novo_id = executar(
        """
        INSERT INTO chamados
            (categoria, urgencia, assunto, descricao, status, aberto_em,
             atualizado_em, concluido_em, solicitante, solicitante_nome,
             responsavel, responsavel_nome, anexo, anexo_nome)
        VALUES (?, ?, ?, ?, 'Aberto', ?, ?, NULL, ?, ?, NULL, NULL, ?, ?)
        """,
        (
            categoria, urgencia, assunto, descricao, agora, agora,
            usuario["email"] if usuario else None,
            usuario["nome"] if usuario else "Visitante",
            anexo_armazenado, anexo_nome,
        ),
    )
    row = buscar_chamado(novo_id)
    return jsonify({"mensagem": "Chamado aberto com sucesso", "chamado": chamado_dict(row)}), 201


# ---------------------------------------------------------------------------
# RF03 - Acompanhamento de Chamados
# ---------------------------------------------------------------------------
@app.route("/api/chamados", methods=["GET"])
def listar_chamados():
    """Lista os chamados (RF03). Filtros opcionais:
    ?status=  | ?meus=1 (solicitante logado) | ?responsavel=me (tecnico logado)."""
    status = request.args.get("status")
    apenas_meus = request.args.get("meus") in ("1", "true", "True")
    responsavel_me = request.args.get("responsavel") == "me"

    clausulas, params = [], []
    if apenas_meus or responsavel_me:
        usuario = session.get("usuario")
        if not usuario:
            return jsonify({"erro": "Não autenticado"}), 401
        if apenas_meus:
            clausulas.append("solicitante = ?")
            params.append(usuario["email"])
        if responsavel_me:
            clausulas.append("responsavel = ?")
            params.append(usuario["email"])
    if status:
        clausulas.append("LOWER(status) = LOWER(?)")
        params.append(status)

    sql = "SELECT * FROM chamados"
    if clausulas:
        sql += " WHERE " + " AND ".join(clausulas)
    sql += " ORDER BY id DESC"

    rows = consultar(sql, params)
    return jsonify({"total": len(rows), "chamados": [chamado_dict(r) for r in rows]}), 200


@app.route("/api/chamados/<int:chamado_id>", methods=["GET"])
def obter_chamado(chamado_id):
    row = buscar_chamado(chamado_id)
    if not row:
        return jsonify({"erro": "Chamado não encontrado"}), 404
    return jsonify(chamado_dict(row)), 200


@app.route("/api/chamados/<int:chamado_id>/anexo", methods=["GET"])
@login_obrigatorio()
def baixar_anexo(chamado_id):
    row = buscar_chamado(chamado_id)
    if not row or not row["anexo"]:
        abort(404)
    if not pode_ver_chamado(row, session["usuario"]):
        abort(403)
    return send_from_directory(
        UPLOAD_DIR, row["anexo"], download_name=row["anexo_nome"] or row["anexo"]
    )


# ---------------------------------------------------------------------------
# RF04 - Gestao e Atendimento (painel do tecnico)
# ---------------------------------------------------------------------------
@app.route("/api/indicadores", methods=["GET"])
@login_obrigatorio(perfis=["tecnico"])
def indicadores():
    pendentes = consultar(
        "SELECT COUNT(*) c FROM chamados WHERE status = 'Aberto'", um=True
    )["c"]
    em_analise = consultar(
        "SELECT COUNT(*) c FROM chamados WHERE status = 'Em análise'", um=True
    )["c"]
    concluidos = consultar(
        "SELECT aberto_em, concluido_em FROM chamados WHERE status = 'Concluído'"
    )

    duracoes = []
    for c in concluidos:
        if c["aberto_em"] and c["concluido_em"]:
            inicio = datetime.fromisoformat(c["aberto_em"])
            fim = datetime.fromisoformat(c["concluido_em"])
            duracoes.append(fim - inicio)

    if duracoes:
        media = sum(duracoes, timedelta()) / len(duracoes)
        tempo_medio = formatar_duracao(media)
    else:
        tempo_medio = "—"

    return jsonify({
        "pendentes": pendentes,
        "em_analise": em_analise,
        "concluidos": len(concluidos),
        "tempo_medio": tempo_medio,
    }), 200


@app.route("/api/chamados/<int:chamado_id>/assumir", methods=["POST"])
@login_obrigatorio(perfis=["tecnico"])
def assumir_chamado(chamado_id):
    row = buscar_chamado(chamado_id)
    if not row:
        return jsonify({"erro": "Chamado não encontrado"}), 404

    usuario = session["usuario"]
    novo_status = "Em análise" if row["status"] == "Aberto" else row["status"]
    executar(
        """UPDATE chamados
           SET responsavel = ?, responsavel_nome = ?, status = ?, atualizado_em = ?
           WHERE id = ?""",
        (usuario["email"], usuario["nome"], novo_status,
         datetime.now().isoformat(timespec="seconds"), chamado_id),
    )
    return jsonify({"mensagem": "Chamado assumido", "chamado": chamado_dict(buscar_chamado(chamado_id))}), 200


@app.route("/api/chamados/<int:chamado_id>/status", methods=["PATCH", "PUT"])
@login_obrigatorio(perfis=["tecnico"])
def atualizar_status(chamado_id):
    dados = request.get_json(silent=True) or {}
    novo_status = (dados.get("status") or "").strip()

    if novo_status not in STATUS_VALIDOS:
        return jsonify({"erro": "Status inválido", "validos": STATUS_VALIDOS}), 400

    row = buscar_chamado(chamado_id)
    if not row:
        return jsonify({"erro": "Chamado não encontrado"}), 404

    agora = datetime.now().isoformat(timespec="seconds")
    concluido_em = agora if novo_status == "Concluído" else None

    # Ao mover para o fluxo de atendimento, garante um responsavel.
    responsavel = row["responsavel"]
    responsavel_nome = row["responsavel_nome"]
    if novo_status in ("Em análise", "Concluído") and not responsavel:
        usuario = session["usuario"]
        responsavel = usuario["email"]
        responsavel_nome = usuario["nome"]

    executar(
        """UPDATE chamados
           SET status = ?, atualizado_em = ?, concluido_em = ?,
               responsavel = ?, responsavel_nome = ?
           WHERE id = ?""",
        (novo_status, agora, concluido_em, responsavel, responsavel_nome, chamado_id),
    )
    return jsonify({"mensagem": "Status atualizado", "chamado": chamado_dict(buscar_chamado(chamado_id))}), 200


# ---------------------------------------------------------------------------
# RF05 - Base de Conhecimento
# ---------------------------------------------------------------------------
@app.route("/api/artigos", methods=["GET"])
def listar_artigos():
    termo = (request.args.get("q") or "").strip().lower()
    categoria = (request.args.get("categoria") or "").strip()

    resultado = ARTIGOS
    if categoria:
        resultado = [a for a in resultado if a["categoria"] == categoria]
    if termo:
        resultado = [
            a for a in resultado
            if termo in a["titulo"].lower()
            or termo in a["resumo"].lower()
            or termo in a["conteudo"].lower()
        ]

    categorias = sorted({a["categoria"] for a in ARTIGOS})
    return jsonify({"total": len(resultado), "categorias": categorias, "artigos": resultado}), 200


# ---------------------------------------------------------------------------
# Paginas (telas do sistema)
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    usuario = session.get("usuario")
    if not usuario:
        return redirect(url_for("pagina_login"))
    if usuario["perfil"] == "tecnico":
        return redirect(url_for("pagina_atendimento"))
    return redirect(url_for("pagina_meus_chamados"))


@app.route("/login")
def pagina_login():
    return render_template("login.html")


@app.route("/abrir")
@login_obrigatorio()
def pagina_abrir():
    return render_template("abrir_chamado.html", usuario=session["usuario"])


@app.route("/meus-chamados")
@login_obrigatorio()
def pagina_meus_chamados():
    return render_template("meus_chamados.html", usuario=session["usuario"])


@app.route("/atendimento")
@login_obrigatorio(perfis=["tecnico"])
def pagina_atendimento():
    return render_template("atendimento.html", usuario=session["usuario"])


@app.route("/usuarios")
@login_obrigatorio(perfis=["tecnico"])
def pagina_usuarios():
    return render_template("usuarios.html", usuario=session["usuario"])


@app.route("/chamados/<int:chamado_id>")
@login_obrigatorio()
def pagina_chamado(chamado_id):
    row = buscar_chamado(chamado_id)
    if not row:
        abort(404)
    usuario = session["usuario"]
    if not pode_ver_chamado(row, usuario):
        return redirect(url_for("index"))
    chamado = chamado_dict(row)
    anexo_eh_imagem = bool(
        row["anexo"] and os.path.splitext(row["anexo"])[1].lower() in EXTENSOES_IMAGEM
    )
    return render_template(
        "chamado_detalhe.html",
        usuario=usuario,
        chamado=chamado,
        anexo_eh_imagem=anexo_eh_imagem,
    )


@app.route("/base")
@login_obrigatorio()
def pagina_base():
    return render_template("base_conhecimento.html", usuario=session["usuario"])


# ---------------------------------------------------------------------------
# Dados de demonstracao
# ---------------------------------------------------------------------------
def seed_se_vazio():
    """Popula chamados de exemplo apenas se a tabela estiver vazia."""
    total = consultar("SELECT COUNT(*) c FROM chamados", um=True)["c"]
    if total:
        return

    agora = datetime.now()
    # (categoria, urgencia, assunto, descricao, status, horas_atras, duracao_horas)
    exemplos = [
        ("Software", "Alta", "Erro ao acessar o sistema de folha de ponto",
         "Recebo a mensagem de usuário ou senha inválidos ao tentar entrar.",
         "Aberto", 3, None),
        ("Hardware", "Media", "Impressora do setor não imprime",
         "A impressora do 2º andar mostra luz vermelha e não responde aos comandos.",
         "Aberto", 5, None),
        ("Acessos", "Alta", "Solicitação de acesso ao sistema acadêmico",
         "Preciso de acesso de leitura ao módulo de matrículas para conferência.",
         "Em análise", 8, None),
        ("Rede e VPN", "Baixa", "VPN desconecta a cada dez minutos",
         "Trabalhando de casa, a conexão VPN cai sozinha com frequência.",
         "Em análise", 26, None),
        ("E-mail", "Media", "Não recebo e-mails de remetentes externos",
         "Mensagens de fora da instituição não chegam à minha caixa de entrada.",
         "Concluído", 72, 28),
        ("Software", "Baixa", "Planilha corporativa não abre",
         "Ao abrir a planilha compartilhada o programa fecha inesperadamente.",
         "Concluído", 50, 6),
    ]

    for categoria, urgencia, assunto, descricao, status, horas_atras, duracao in exemplos:
        aberto_em = agora - timedelta(hours=horas_atras)
        atualizado_em = aberto_em
        concluido_em = None
        responsavel = responsavel_nome = None

        if status in ("Em análise", "Concluído"):
            responsavel = "tecnico@uncisal.edu.br"
            responsavel_nome = "Carlos Lima"
        if status == "Concluído" and duracao is not None:
            concluido_em = aberto_em + timedelta(hours=duracao)
            atualizado_em = concluido_em

        executar(
            """
            INSERT INTO chamados
                (categoria, urgencia, assunto, descricao, status, aberto_em,
                 atualizado_em, concluido_em, solicitante, solicitante_nome,
                 responsavel, responsavel_nome, anexo, anexo_nome)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL)
            """,
            (
                categoria, urgencia, assunto, descricao, status,
                aberto_em.isoformat(timespec="seconds"),
                atualizado_em.isoformat(timespec="seconds"),
                concluido_em.isoformat(timespec="seconds") if concluido_em else None,
                "colaborador@uncisal.edu.br", "Maria Souza",
                responsavel, responsavel_nome,
            ),
        )


# Inicializa o banco assim que o modulo e carregado (idempotente).
init_db()


if __name__ == "__main__":
    # No macOS a porta 5000 costuma ser usada pelo "AirPlay Receiver".
    # Defina a variavel PORT para usar outra porta, ex.: PORT=5001 python app.py
    porta = int(os.environ.get("PORT", "5000"))
    app.run(host="127.0.0.1", port=porta, debug=True)
