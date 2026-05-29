"""Base de Conhecimento (RF05).

Consulta (busca + categorias) é pública para os usuários logados; a gestão
(criar, editar e excluir artigos) é restrita ao perfil técnico.
"""
from flask import Blueprint, jsonify, request

from .. import db
from ..auth import login_obrigatorio

bp = Blueprint("artigos", __name__)


def artigo_dict(row):
    return {
        "id": row["id"],
        "categoria": row["categoria"],
        "titulo": row["titulo"],
        "resumo": row["resumo"],
        "conteudo": row["conteudo"],
    }


def validar_artigo(dados):
    """Normaliza e valida os campos. Retorna (campos, erros)."""
    campos = {
        "categoria": (dados.get("categoria") or "").strip(),
        "titulo": (dados.get("titulo") or "").strip(),
        "resumo": (dados.get("resumo") or "").strip(),
        "conteudo": (dados.get("conteudo") or "").strip(),
    }
    erros = {}
    if len(campos["categoria"]) < 2:
        erros["categoria"] = "Informe a categoria."
    if len(campos["titulo"]) < 5:
        erros["titulo"] = "O título deve ter ao menos 5 caracteres."
    if len(campos["resumo"]) < 5:
        erros["resumo"] = "O resumo deve ter ao menos 5 caracteres."
    if len(campos["conteudo"]) < 10:
        erros["conteudo"] = "O conteúdo deve ter ao menos 10 caracteres."
    return campos, erros


# ---------------------------------------------------------------------------
# Consulta (RF05) — disponível para qualquer usuário logado
# ---------------------------------------------------------------------------
@bp.route("/api/artigos", methods=["GET"])
def listar_artigos():
    termo = (request.args.get("q") or "").strip().lower()
    categoria = (request.args.get("categoria") or "").strip()

    artigos = [artigo_dict(r) for r in db.consultar("SELECT * FROM artigos ORDER BY categoria, titulo")]
    resultado = artigos
    if categoria:
        resultado = [a for a in resultado if a["categoria"] == categoria]
    if termo:
        resultado = [
            a for a in resultado
            if termo in a["titulo"].lower()
            or termo in a["resumo"].lower()
            or termo in a["conteudo"].lower()
        ]

    categorias = sorted({a["categoria"] for a in artigos})
    return jsonify({"total": len(resultado), "categorias": categorias, "artigos": resultado}), 200


@bp.route("/api/artigos/<int:artigo_id>", methods=["GET"])
def obter_artigo(artigo_id):
    row = db.consultar("SELECT * FROM artigos WHERE id = ?", (artigo_id,), um=True)
    if not row:
        return jsonify({"erro": "Artigo não encontrado"}), 404
    return jsonify(artigo_dict(row)), 200


# ---------------------------------------------------------------------------
# Gestão (somente técnico)
# ---------------------------------------------------------------------------
@bp.route("/api/artigos", methods=["POST"])
@login_obrigatorio(perfis=["tecnico"])
def criar_artigo():
    campos, erros = validar_artigo(request.get_json(silent=True) or {})
    if erros:
        return jsonify({"erro": "Dados invalidos", "campos": erros}), 400
    novo_id = db.executar(
        "INSERT INTO artigos (categoria, titulo, resumo, conteudo) VALUES (?, ?, ?, ?)",
        (campos["categoria"], campos["titulo"], campos["resumo"], campos["conteudo"]),
    )
    row = db.consultar("SELECT * FROM artigos WHERE id = ?", (novo_id,), um=True)
    return jsonify({"mensagem": "Artigo criado com sucesso", "artigo": artigo_dict(row)}), 201


@bp.route("/api/artigos/<int:artigo_id>", methods=["PUT", "PATCH"])
@login_obrigatorio(perfis=["tecnico"])
def atualizar_artigo(artigo_id):
    if not db.consultar("SELECT 1 FROM artigos WHERE id = ?", (artigo_id,), um=True):
        return jsonify({"erro": "Artigo não encontrado"}), 404
    campos, erros = validar_artigo(request.get_json(silent=True) or {})
    if erros:
        return jsonify({"erro": "Dados invalidos", "campos": erros}), 400
    db.executar(
        "UPDATE artigos SET categoria = ?, titulo = ?, resumo = ?, conteudo = ? WHERE id = ?",
        (campos["categoria"], campos["titulo"], campos["resumo"], campos["conteudo"], artigo_id),
    )
    row = db.consultar("SELECT * FROM artigos WHERE id = ?", (artigo_id,), um=True)
    return jsonify({"mensagem": "Artigo atualizado com sucesso", "artigo": artigo_dict(row)}), 200


@bp.route("/api/artigos/<int:artigo_id>", methods=["DELETE"])
@login_obrigatorio(perfis=["tecnico"])
def excluir_artigo(artigo_id):
    if not db.consultar("SELECT 1 FROM artigos WHERE id = ?", (artigo_id,), um=True):
        return jsonify({"erro": "Artigo não encontrado"}), 404
    db.executar("DELETE FROM artigos WHERE id = ?", (artigo_id,))
    return jsonify({"mensagem": "Artigo excluído com sucesso"}), 200
