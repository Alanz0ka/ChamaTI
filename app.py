"""
ChamaTI - Sistema Web para Gerenciamento de Chamados de Suporte de TI

Ponto de entrada da aplicação. A lógica está organizada no pacote chamati/
(config, db, auth, utils, conteudo e os blueprints em chamati/blueprints/).

Execução:
    pip install -r requirements.txt
    python app.py

A aplicação sobe em http://localhost:5000

Usuários de demonstração (senha: 123456):
    colaborador@uncisal.edu.br  -> perfil colaborador
    tecnico@uncisal.edu.br      -> perfil tecnico
"""
import os

from chamati import create_app

app = create_app()


if __name__ == "__main__":
    # No macOS a porta 5000 costuma ser usada pelo "AirPlay Receiver".
    # Defina a variavel PORT para usar outra porta, ex.: PORT=5001 python app.py
    porta = int(os.environ.get("PORT", "5000"))
    app.run(host="127.0.0.1", port=porta, debug=True)
