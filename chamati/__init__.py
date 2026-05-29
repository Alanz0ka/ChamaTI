"""Pacote da aplicação ChamaTI — fábrica da aplicação Flask.

Organização:
    config.py      constantes, caminhos e usuários iniciais
    db.py          conexão SQLite, helpers, init_db e dados de demonstração
    auth.py        login_obrigatorio, encontrar_usuario, pode_ver_chamado
    utils.py       funções utilitárias (duração, validação de anexo)
    conteudo.py    artigos da base de conhecimento (RF05)
    blueprints/    rotas agrupadas por área (paginas, auth, usuarios, chamados, artigos)
"""
from flask import Flask

from . import config, db


def create_app():
    app = Flask(
        __name__,
        template_folder=config.TEMPLATES_DIR,
        static_folder=config.STATIC_DIR,
    )
    app.secret_key = config.SECRET_KEY
    app.config["MAX_CONTENT_LENGTH"] = config.MAX_CONTENT_LENGTH

    # Cria as tabelas e os dados iniciais (idempotente).
    db.init_db()

    # Registra os blueprints.
    from .blueprints.paginas import bp as paginas_bp
    from .blueprints.auth_api import bp as auth_bp
    from .blueprints.usuarios import bp as usuarios_bp
    from .blueprints.chamados import bp as chamados_bp
    from .blueprints.artigos import bp as artigos_bp

    for blueprint in (paginas_bp, auth_bp, usuarios_bp, chamados_bp, artigos_bp):
        app.register_blueprint(blueprint)

    return app
