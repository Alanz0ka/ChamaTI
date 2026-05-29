"""Acesso ao banco de dados SQLite e carga de dados iniciais."""
import os
import sqlite3
from datetime import datetime, timedelta

from . import config, conteudo


def conectar():
    conn = sqlite3.connect(config.DB_PATH)
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
    """Cria as tabelas (idempotente) e popula os dados iniciais."""
    os.makedirs(config.UPLOAD_DIR, exist_ok=True)
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
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS artigos (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                categoria TEXT NOT NULL,
                titulo    TEXT NOT NULL,
                resumo    TEXT NOT NULL,
                conteudo  TEXT NOT NULL
            )
            """
        )
        conn.commit()
    finally:
        conn.close()
    seed_usuarios_se_vazio()
    seed_artigos_se_vazio()
    seed_chamados_se_vazio()


def chamado_dict(row):
    """Converte uma linha do banco no formato esperado pela API/telas.
    O caminho interno do anexo não é exposto; em vez disso usa-se tem_anexo."""
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
# Dados iniciais (seed) — inseridos apenas quando as tabelas estão vazias
# ---------------------------------------------------------------------------
def seed_usuarios_se_vazio():
    if consultar("SELECT COUNT(*) c FROM usuarios", um=True)["c"]:
        return
    for email, dados in config.USUARIOS_PADRAO.items():
        executar(
            "INSERT INTO usuarios (email, nome, senha, perfil) VALUES (?, ?, ?, ?)",
            (email, dados["nome"], dados["senha"], dados["perfil"]),
        )


def seed_artigos_se_vazio():
    if consultar("SELECT COUNT(*) c FROM artigos", um=True)["c"]:
        return
    for a in conteudo.ARTIGOS:
        executar(
            "INSERT INTO artigos (categoria, titulo, resumo, conteudo) VALUES (?, ?, ?, ?)",
            (a["categoria"], a["titulo"], a["resumo"], a["conteudo"]),
        )


def seed_chamados_se_vazio():
    if consultar("SELECT COUNT(*) c FROM chamados", um=True)["c"]:
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
