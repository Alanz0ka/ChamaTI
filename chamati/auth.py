"""Autenticação, autorização e localização de usuários (RF01)."""
from functools import wraps

from flask import jsonify, redirect, request, session, url_for

from . import db


def encontrar_usuario(identificador):
    """Localiza um usuário por e-mail completo ou pelo usuário institucional
    (parte antes do @)."""
    identificador = (identificador or "").strip().lower()
    if not identificador:
        return None
    row = db.consultar("SELECT * FROM usuarios WHERE email = ?", (identificador,), um=True)
    if not row:
        for r in db.consultar("SELECT * FROM usuarios"):
            if r["email"].split("@")[0] == identificador:
                row = r
                break
    if not row:
        return None
    return {"email": row["email"], "nome": row["nome"], "senha": row["senha"], "perfil": row["perfil"]}


def pode_ver_chamado(row, usuario):
    """Técnico vê qualquer chamado; colaborador apenas os próprios."""
    return usuario["perfil"] == "tecnico" or row["solicitante"] == usuario["email"]


def login_obrigatorio(perfis=None):
    """Garante autenticação. Em rotas /api/* responde JSON; nas páginas redireciona."""
    def decorador(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            usuario = session.get("usuario")
            eh_api = request.path.startswith("/api/")
            if not usuario:
                if eh_api:
                    return jsonify({"erro": "Não autenticado"}), 401
                return redirect(url_for("paginas.pagina_login"))
            if perfis and usuario["perfil"] not in perfis:
                if eh_api:
                    return jsonify({"erro": "Acesso negado"}), 403
                return redirect(url_for("paginas.index"))
            return view(*args, **kwargs)
        return wrapper
    return decorador
