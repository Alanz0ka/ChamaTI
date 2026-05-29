"""Rotas que renderizam as telas (HTML)."""
import os

from flask import Blueprint, abort, redirect, render_template, session, url_for

from .. import config, db
from ..auth import login_obrigatorio, pode_ver_chamado

bp = Blueprint("paginas", __name__)


@bp.route("/")
def index():
    usuario = session.get("usuario")
    if not usuario:
        return redirect(url_for("paginas.pagina_login"))
    if usuario["perfil"] == "tecnico":
        return redirect(url_for("paginas.pagina_atendimento"))
    return redirect(url_for("paginas.pagina_meus_chamados"))


@bp.route("/login")
def pagina_login():
    return render_template("login.html")


@bp.route("/abrir")
@login_obrigatorio()
def pagina_abrir():
    return render_template("abrir_chamado.html", usuario=session["usuario"])


@bp.route("/meus-chamados")
@login_obrigatorio()
def pagina_meus_chamados():
    return render_template("meus_chamados.html", usuario=session["usuario"])


@bp.route("/atendimento")
@login_obrigatorio(perfis=["tecnico"])
def pagina_atendimento():
    return render_template("atendimento.html", usuario=session["usuario"])


@bp.route("/usuarios")
@login_obrigatorio(perfis=["tecnico"])
def pagina_usuarios():
    return render_template("usuarios.html", usuario=session["usuario"])


@bp.route("/chamados/<int:chamado_id>")
@login_obrigatorio()
def pagina_chamado(chamado_id):
    row = db.buscar_chamado(chamado_id)
    if not row:
        abort(404)
    usuario = session["usuario"]
    if not pode_ver_chamado(row, usuario):
        return redirect(url_for("paginas.index"))
    chamado = db.chamado_dict(row)
    anexo_eh_imagem = bool(
        row["anexo"] and os.path.splitext(row["anexo"])[1].lower() in config.EXTENSOES_IMAGEM
    )
    return render_template(
        "chamado_detalhe.html",
        usuario=usuario,
        chamado=chamado,
        anexo_eh_imagem=anexo_eh_imagem,
    )


@bp.route("/base")
@login_obrigatorio()
def pagina_base():
    return render_template("base_conhecimento.html", usuario=session["usuario"])
