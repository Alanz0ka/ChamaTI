"""Chamados: abertura (RF02), acompanhamento (RF03) e atendimento (RF04)."""
import os
import uuid
from datetime import datetime, timedelta

from flask import Blueprint, abort, jsonify, request, send_from_directory, session
from werkzeug.utils import secure_filename

from .. import config, db, utils
from ..auth import login_obrigatorio, pode_ver_chamado

bp = Blueprint("chamados", __name__)


# ---------------------------------------------------------------------------
# RF02 - Abertura de Chamado
# ---------------------------------------------------------------------------
@bp.route("/api/chamados", methods=["POST"])
def abrir_chamado():
    """Abre um novo chamado de suporte (RF02).

    Aceita JSON (contrato documentado) ou multipart/form-data quando há anexo.
    """
    if request.content_type and "application/json" in request.content_type:
        dados = request.get_json(silent=True) or {}
        arquivo = None
    else:
        dados = request.form
        arquivo = request.files.get("anexo")

    erros = {}
    categoria = (dados.get("categoria") or "").strip()
    urgencia = (dados.get("urgencia") or "").strip()
    assunto = (dados.get("assunto") or "").strip()
    descricao = (dados.get("descricao") or "").strip()

    if categoria not in config.CATEGORIAS:
        erros["categoria"] = f"Categoria invalida. Use uma de: {sorted(config.CATEGORIAS)}"
    if urgencia not in config.URGENCIAS:
        erros["urgencia"] = f"Urgencia invalida. Use uma de: {sorted(config.URGENCIAS)}"
    if len(assunto) < 5:
        erros["assunto"] = "O assunto deve ter ao menos 5 caracteres."
    if len(descricao) < 10:
        erros["descricao"] = "A descricao deve ter ao menos 10 caracteres."

    ext, erro_anexo = utils.validar_anexo(arquivo)
    if erro_anexo:
        erros["anexo"] = erro_anexo

    if erros:
        return jsonify({"erro": "Dados invalidos", "campos": erros}), 400

    anexo_armazenado = None
    anexo_nome = None
    if ext:
        anexo_armazenado = uuid.uuid4().hex + ext
        anexo_nome = secure_filename(arquivo.filename) or ("anexo" + ext)
        arquivo.save(os.path.join(config.UPLOAD_DIR, anexo_armazenado))

    usuario = session.get("usuario")
    agora = datetime.now().isoformat(timespec="seconds")
    novo_id = db.executar(
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
    row = db.buscar_chamado(novo_id)
    return jsonify({"mensagem": "Chamado aberto com sucesso", "chamado": db.chamado_dict(row)}), 201


# ---------------------------------------------------------------------------
# RF03 - Acompanhamento de Chamados
# ---------------------------------------------------------------------------
@bp.route("/api/chamados", methods=["GET"])
def listar_chamados():
    """Lista os chamados (RF03). Filtros opcionais:
    ?status=  | ?meus=1 (solicitante logado) | ?responsavel=me (técnico logado)."""
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

    rows = db.consultar(sql, params)
    return jsonify({"total": len(rows), "chamados": [db.chamado_dict(r) for r in rows]}), 200


@bp.route("/api/chamados/<int:chamado_id>", methods=["GET"])
def obter_chamado(chamado_id):
    row = db.buscar_chamado(chamado_id)
    if not row:
        return jsonify({"erro": "Chamado não encontrado"}), 404
    return jsonify(db.chamado_dict(row)), 200


@bp.route("/api/chamados/<int:chamado_id>/anexo", methods=["GET"])
@login_obrigatorio()
def baixar_anexo(chamado_id):
    row = db.buscar_chamado(chamado_id)
    if not row or not row["anexo"]:
        abort(404)
    if not pode_ver_chamado(row, session["usuario"]):
        abort(403)
    return send_from_directory(
        config.UPLOAD_DIR, row["anexo"], download_name=row["anexo_nome"] or row["anexo"]
    )


# ---------------------------------------------------------------------------
# RF04 - Gestão e Atendimento (painel do técnico)
# ---------------------------------------------------------------------------
@bp.route("/api/indicadores", methods=["GET"])
@login_obrigatorio(perfis=["tecnico"])
def indicadores():
    pendentes = db.consultar(
        "SELECT COUNT(*) c FROM chamados WHERE status = 'Aberto'", um=True
    )["c"]
    em_analise = db.consultar(
        "SELECT COUNT(*) c FROM chamados WHERE status = 'Em análise'", um=True
    )["c"]
    concluidos = db.consultar(
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
        tempo_medio = utils.formatar_duracao(media)
    else:
        tempo_medio = "—"

    return jsonify({
        "pendentes": pendentes,
        "em_analise": em_analise,
        "concluidos": len(concluidos),
        "tempo_medio": tempo_medio,
    }), 200


@bp.route("/api/chamados/<int:chamado_id>/assumir", methods=["POST"])
@login_obrigatorio(perfis=["tecnico"])
def assumir_chamado(chamado_id):
    row = db.buscar_chamado(chamado_id)
    if not row:
        return jsonify({"erro": "Chamado não encontrado"}), 404

    usuario = session["usuario"]
    novo_status = "Em análise" if row["status"] == "Aberto" else row["status"]
    db.executar(
        """UPDATE chamados
           SET responsavel = ?, responsavel_nome = ?, status = ?, atualizado_em = ?
           WHERE id = ?""",
        (usuario["email"], usuario["nome"], novo_status,
         datetime.now().isoformat(timespec="seconds"), chamado_id),
    )
    return jsonify({"mensagem": "Chamado assumido", "chamado": db.chamado_dict(db.buscar_chamado(chamado_id))}), 200


@bp.route("/api/chamados/<int:chamado_id>/status", methods=["PATCH", "PUT"])
@login_obrigatorio(perfis=["tecnico"])
def atualizar_status(chamado_id):
    dados = request.get_json(silent=True) or {}
    novo_status = (dados.get("status") or "").strip()

    if novo_status not in config.STATUS_VALIDOS:
        return jsonify({"erro": "Status inválido", "validos": config.STATUS_VALIDOS}), 400

    row = db.buscar_chamado(chamado_id)
    if not row:
        return jsonify({"erro": "Chamado não encontrado"}), 404

    agora = datetime.now().isoformat(timespec="seconds")
    concluido_em = agora if novo_status == "Concluído" else None

    # Ao mover para o fluxo de atendimento, garante um responsável.
    responsavel = row["responsavel"]
    responsavel_nome = row["responsavel_nome"]
    if novo_status in ("Em análise", "Concluído") and not responsavel:
        usuario = session["usuario"]
        responsavel = usuario["email"]
        responsavel_nome = usuario["nome"]

    db.executar(
        """UPDATE chamados
           SET status = ?, atualizado_em = ?, concluido_em = ?,
               responsavel = ?, responsavel_nome = ?
           WHERE id = ?""",
        (novo_status, agora, concluido_em, responsavel, responsavel_nome, chamado_id),
    )
    return jsonify({"mensagem": "Status atualizado", "chamado": db.chamado_dict(db.buscar_chamado(chamado_id))}), 200
