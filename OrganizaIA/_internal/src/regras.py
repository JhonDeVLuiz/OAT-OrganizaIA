"""Fase 2: categoria por extensao. Indeciso retorna None (= Revisar/)."""
from pathlib import Path

from .config import EXTENSAO_PARA_CATEGORIA


def categoria_por_extensao(ext):
    return EXTENSAO_PARA_CATEGORIA.get(str(ext).lower())


def decidir(caminho):
    return categoria_por_extensao(Path(caminho).suffix)
