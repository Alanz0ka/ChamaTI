"""Gestão de usuários — somente técnico (RF01)."""
from flask import Blueprint, jsonify, request

from .. import config, db
from ..auth import login_obrigatorio

bp = Blueprint("usuarios", __name__)


@bp.route("/api/usuarios", methods=["GET"])
@login_obrigatorio(perfis=["tecnico"])
def listar():
    rows = db.consultar("SELECT email, nome, perfil FROM usuarios ORDER BY perfil, nome")
    return jsonify({"total": len(rows), "usuarios": [dict(r) for r in rows]}), 200


@bp.route("/api/usuarios", methods=["POST"])
@login_obrigatorio(perfis=["tecnico"])
def criar():
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
    elif db.consultar("SELECT 1 FROM usuarios WHERE email = ?", (email,), um=True):
        erros["email"] = "Já existe um usuário com este e-mail."
    if len(senha) < 6:
        erros["senha"] = "A senha deve ter ao menos 6 caracteres."
    if perfil not in config.PERFIS_VALIDOS:
        erros["perfil"] = "Selecione um perfil válido."

    if erros:
        return jsonify({"erro": "Dados invalidos", "campos": erros}), 400

    db.executar(
        "INSERT INTO usuarios (email, nome, senha, perfil) VALUES (?, ?, ?, ?)",
        (email, nome, senha, perfil),
    )
    return jsonify({
        "mensagem": "Usuário criado com sucesso",
        "usuario": {"email": email, "nome": nome, "perfil": perfil},
    }), 201
