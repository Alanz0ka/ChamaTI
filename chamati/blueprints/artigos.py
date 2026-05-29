"""Base de Conhecimento (RF05)."""
from flask import Blueprint, jsonify, request

from ..conteudo import ARTIGOS

bp = Blueprint("artigos", __name__)


@bp.route("/api/artigos", methods=["GET"])
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
