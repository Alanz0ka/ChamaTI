"""
ChamaTI - Sistema Web para Gerenciamento de Chamados de Suporte de TI

Funcionalidades (Ação Curricular de Extensão 2):
    RF01 - Autenticacao e Controle de Acesso (login/logout por perfil)
    RF02 - Abertura de Chamado
    RF03 - Acompanhamento de Chamados
    RF04 - Gestao e Atendimento (painel do tecnico: indicadores e Kanban)
    RF05 - Base de Conhecimento

Execucao:
    pip install flask
    python app.py

A aplicacao sobe em http://localhost:5000

Usuarios de demonstracao (senha: 123456):
    colaborador@uncisal.edu.br  -> perfil colaborador
    tecnico@uncisal.edu.br      -> perfil tecnico
"""
import os
from datetime import datetime, timedelta
from functools import wraps

from flask import (
    Flask,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

app = Flask(__name__)
app.secret_key = "chamati-chave-de-desenvolvimento"

# ---------------------------------------------------------------------------
# Armazenamento em memoria (em producao: banco de dados)
# ---------------------------------------------------------------------------
chamados = []
proximo_id = 1

# Valores aceitos para validacao (RF02)
CATEGORIAS = {"Hardware", "Software", "Acessos", "Rede e VPN", "E-mail"}
URGENCIAS = {"Baixa", "Media", "Alta"}
ORDEM_URGENCIAS = ["Baixa", "Media", "Alta"]

# Status do fluxo de atendimento (codificacao de cores definida no front-end:
# azul = Aberto, ambar = Em analise, verde = Concluido)
STATUS_VALIDOS = ["Aberto", "Em análise", "Concluído"]

# Usuarios cadastrados (RF01) - apenas para demonstracao
USUARIOS = {
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

# Base de conhecimento (RF05)
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
# Utilitarios
# ---------------------------------------------------------------------------
def encontrar_usuario(identificador):
    """Localiza um usuario por e-mail completo ou pelo usuario institucional
    (parte antes do @)."""
    identificador = (identificador or "").strip().lower()
    for email, dados in USUARIOS.items():
        if identificador in (email, email.split("@")[0]):
            return {"email": email, **dados}
    return None


def buscar_chamado(chamado_id):
    return next((c for c in chamados if c["id"] == chamado_id), None)


def formatar_duracao(td):
    total_min = int(td.total_seconds() // 60)
    horas, minutos = divmod(total_min, 60)
    if horas and minutos:
        return f"{horas}h {minutos}min"
    if horas:
        return f"{horas}h"
    return f"{minutos}min"


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
# RF02 - Abertura de Chamado
# ---------------------------------------------------------------------------
@app.route("/api/chamados", methods=["POST"])
def abrir_chamado():
    """Abre um novo chamado de suporte (RF02)."""
    dados = request.get_json(silent=True) or {}

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

    if erros:
        return jsonify({"erro": "Dados invalidos", "campos": erros}), 400

    global proximo_id
    usuario = session.get("usuario")
    agora = datetime.now().isoformat(timespec="seconds")
    chamado = {
        "id": proximo_id,
        "categoria": categoria,
        "urgencia": urgencia,
        "assunto": assunto,
        "descricao": descricao,
        "status": "Aberto",
        "aberto_em": agora,
        "atualizado_em": agora,
        "concluido_em": None,
        "solicitante": usuario["email"] if usuario else None,
        "solicitante_nome": usuario["nome"] if usuario else "Visitante",
        "responsavel": None,
        "responsavel_nome": None,
    }
    chamados.append(chamado)
    proximo_id += 1

    return jsonify({"mensagem": "Chamado aberto com sucesso", "chamado": chamado}), 201


# ---------------------------------------------------------------------------
# RF03 - Acompanhamento de Chamados
# ---------------------------------------------------------------------------
@app.route("/api/chamados", methods=["GET"])
def listar_chamados():
    """Lista os chamados, com filtro opcional por status (RF03) e por
    solicitante logado (?meus=1)."""
    status = request.args.get("status")
    apenas_meus = request.args.get("meus") in ("1", "true", "True")

    resultado = chamados
    if apenas_meus:
        usuario = session.get("usuario")
        if not usuario:
            return jsonify({"erro": "Não autenticado"}), 401
        resultado = [c for c in resultado if c.get("solicitante") == usuario["email"]]
    if status:
        resultado = [c for c in resultado if c["status"].lower() == status.lower()]

    return jsonify({"total": len(resultado), "chamados": resultado}), 200


@app.route("/api/chamados/<int:chamado_id>", methods=["GET"])
def obter_chamado(chamado_id):
    chamado = buscar_chamado(chamado_id)
    if not chamado:
        return jsonify({"erro": "Chamado não encontrado"}), 404
    return jsonify(chamado), 200


# ---------------------------------------------------------------------------
# RF04 - Gestao e Atendimento (painel do tecnico)
# ---------------------------------------------------------------------------
@app.route("/api/indicadores", methods=["GET"])
@login_obrigatorio(perfis=["tecnico"])
def indicadores():
    pendentes = sum(1 for c in chamados if c["status"] == "Aberto")
    em_analise = sum(1 for c in chamados if c["status"] == "Em análise")
    concluidos = [c for c in chamados if c["status"] == "Concluído"]

    duracoes = []
    for c in concluidos:
        if c.get("aberto_em") and c.get("concluido_em"):
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
    chamado = buscar_chamado(chamado_id)
    if not chamado:
        return jsonify({"erro": "Chamado não encontrado"}), 404

    usuario = session["usuario"]
    chamado["responsavel"] = usuario["email"]
    chamado["responsavel_nome"] = usuario["nome"]
    if chamado["status"] == "Aberto":
        chamado["status"] = "Em análise"
    chamado["atualizado_em"] = datetime.now().isoformat(timespec="seconds")

    return jsonify({"mensagem": "Chamado assumido", "chamado": chamado}), 200


@app.route("/api/chamados/<int:chamado_id>/status", methods=["PATCH", "PUT"])
@login_obrigatorio(perfis=["tecnico"])
def atualizar_status(chamado_id):
    dados = request.get_json(silent=True) or {}
    novo_status = (dados.get("status") or "").strip()

    if novo_status not in STATUS_VALIDOS:
        return jsonify({"erro": "Status inválido", "validos": STATUS_VALIDOS}), 400

    chamado = buscar_chamado(chamado_id)
    if not chamado:
        return jsonify({"erro": "Chamado não encontrado"}), 404

    agora = datetime.now().isoformat(timespec="seconds")
    chamado["status"] = novo_status
    chamado["atualizado_em"] = agora
    chamado["concluido_em"] = agora if novo_status == "Concluído" else None

    # Ao mover para o fluxo de atendimento, garante um responsavel.
    if novo_status in ("Em análise", "Concluído") and not chamado.get("responsavel"):
        usuario = session["usuario"]
        chamado["responsavel"] = usuario["email"]
        chamado["responsavel_nome"] = usuario["nome"]

    return jsonify({"mensagem": "Status atualizado", "chamado": chamado}), 200


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


@app.route("/base")
@login_obrigatorio()
def pagina_base():
    return render_template("base_conhecimento.html", usuario=session["usuario"])


# ---------------------------------------------------------------------------
# Dados de demonstracao
# ---------------------------------------------------------------------------
def carregar_dados_demo():
    """Popula chamados de exemplo para a apresentacao."""
    global proximo_id
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

        chamados.append({
            "id": proximo_id,
            "categoria": categoria,
            "urgencia": urgencia,
            "assunto": assunto,
            "descricao": descricao,
            "status": status,
            "aberto_em": aberto_em.isoformat(timespec="seconds"),
            "atualizado_em": atualizado_em.isoformat(timespec="seconds"),
            "concluido_em": concluido_em.isoformat(timespec="seconds") if concluido_em else None,
            "solicitante": "colaborador@uncisal.edu.br",
            "solicitante_nome": "Maria Souza",
            "responsavel": responsavel,
            "responsavel_nome": responsavel_nome,
        })
        proximo_id += 1


if __name__ == "__main__":
    carregar_dados_demo()
    # No macOS a porta 5000 costuma ser usada pelo "AirPlay Receiver".
    # Defina a variavel PORT para usar outra porta, ex.: PORT=5001 python app.py
    porta = int(os.environ.get("PORT", "5000"))
    app.run(host="127.0.0.1", port=porta, debug=True)
