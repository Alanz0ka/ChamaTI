"""Funções utilitárias do ChamaTI."""
import os

from . import config


def formatar_duracao(td):
    """Formata um timedelta como '2h 15min', '3h' ou '40min'."""
    total_min = int(td.total_seconds() // 60)
    horas, minutos = divmod(total_min, 60)
    if horas and minutos:
        return f"{horas}h {minutos}min"
    if horas:
        return f"{horas}h"
    return f"{minutos}min"


def validar_anexo(arquivo):
    """Valida o anexo enviado.

    Retorna (extensao, mensagem_de_erro). A extensão é None quando não há
    arquivo; a mensagem é None quando o anexo é válido.
    """
    if not arquivo or not arquivo.filename:
        return None, None
    ext = os.path.splitext(arquivo.filename)[1].lower()
    if ext not in config.EXTENSOES_OK:
        return None, "Formato não aceito. Use PNG, JPG ou PDF."
    arquivo.seek(0, os.SEEK_END)
    tamanho = arquivo.tell()
    arquivo.seek(0)
    if tamanho > config.TAM_MAX:
        return None, "O arquivo excede o limite de 5 MB."
    return ext, None
