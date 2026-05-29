"""Rotas de autenticação e opções (RF01)."""
from flask import Blueprint, jsonify, request, session

from .. import config
from ..auth import encontrar_usuario

bp = Blueprint("auth", __name__)


@bp.route("/api/login", methods=["POST"])
def login():
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


@bp.route("/api/logout", methods=["POST"])
def logout():
    session.pop("usuario", None)
    return jsonify({"mensagem": "Sessão encerrada"}), 200


@bp.route("/api/sessao", methods=["GET"])
def sessao():
    return jsonify({"usuario": session.get("usuario")}), 200


@bp.route("/api/opcoes", methods=["GET"])
def opcoes():
    """Opções oficiais para os formulários, mantendo o front-end alinhado à
    validação do back-end."""
    return jsonify({
        "categorias": sorted(config.CATEGORIAS),
        "urgencias": config.ORDEM_URGENCIAS,
    }), 200
