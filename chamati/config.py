"""Configurações e constantes do ChamaTI."""
import os

# Caminhos — o pacote chamati/ fica dentro da raiz do projeto, então a raiz é o
# diretório pai deste arquivo. templates/, static/, o banco e os anexos vivem lá.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "chamati.db")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")

SECRET_KEY = "chamati-chave-de-desenvolvimento"
MAX_CONTENT_LENGTH = 8 * 1024 * 1024  # margem para o arquivo (5 MB) + campos

# Anexos: extensões aceitas e tamanho máximo (5 MB)
EXTENSOES_OK = {".png", ".jpg", ".jpeg", ".pdf"}
EXTENSOES_IMAGEM = {".png", ".jpg", ".jpeg"}
TAM_MAX = 5 * 1024 * 1024

# Valores aceitos para validação (RF02)
CATEGORIAS = {"Hardware", "Software", "Acessos", "Rede e VPN", "E-mail"}
URGENCIAS = {"Baixa", "Media", "Alta"}
ORDEM_URGENCIAS = ["Baixa", "Media", "Alta"]

# Status do fluxo de atendimento (codificação de cores no front-end:
# azul = Aberto, âmbar = Em análise, verde = Concluído)
STATUS_VALIDOS = ["Aberto", "Em análise", "Concluído"]

# Perfis de acesso (RF01)
PERFIS_VALIDOS = {"colaborador", "tecnico"}

# Usuários iniciais (seed) — criados na 1ª execução; novos são cadastrados no app
USUARIOS_PADRAO = {
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
