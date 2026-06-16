from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

import pandas as pd


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip().upper()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"\s+", " ", text)
    return text


def normalize_column_name(name: str) -> str:
    text = normalize_text(name).lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return re.sub(r"_+", "_", text).strip("_")


@dataclass(frozen=True)
class ColumnMap:
    data: str
    hora: str | None
    municipio: str
    bairro: str | None
    crime: str
    tipo_local: str | None
    id_ocorrencia: str | None
    hora_inicio: str | None
    hora_fim: str | None


COLUMN_CANDIDATES = {
    "data": [
        "data_fato",
        "data_do_fato",
        "data_ocorrencia",
        "data_da_ocorrencia",
        "data_registro",
        "data",
    ],
    "hora": [
        "hora_fato",
        "horario_fato",
        "hora_do_fato",
        "hora_ocorrencia",
        "hora_da_ocorrencia",
        "hora",
        "horario",
    ],
    "municipio": ["municipio", "municipio_fato", "cidade", "localidade_municipio"],
    "bairro": ["bairro", "bairro_fato", "bairro_ocorrencia", "localidade_bairro"],
    "crime": [
        "natureza",
        "tipo_incidente",
        "incidente",
        "tipo_ocorrencia",
        "descricao_natureza",
        "categoria",
        "crime",
    ],
    "tipo_local": ["tipo_local", "local", "local_fato", "tipo_de_local", "ambiente"],
    "id_ocorrencia": [
        "id_ocorrencia",
        "codigo_ocorrencia",
        "cod_ocorrencia",
        "numero_ocorrencia",
        "num_ocorrencia",
        "n_ocorrencia",
        "id_boletim",
        "numero_boletim",
        "num_boletim",
    ],
    "hora_inicio": ["hora_inicio", "horario_inicio", "hora_inicial", "inicio_periodo"],
    "hora_fim": ["hora_fim", "horario_fim", "hora_final", "fim_periodo"],
}


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    renamed = {column: normalize_column_name(str(column)) for column in df.columns}
    return df.rename(columns=renamed)


def _find_column(columns: list[str], candidates: list[str], required: bool) -> str | None:
    for candidate in candidates:
        if candidate in columns:
            return candidate
    for candidate in candidates:
        for column in columns:
            if candidate in column:
                return column
    if required:
        raise KeyError(
            "Coluna obrigatória não encontrada. "
            f"Procuradas: {candidates}. Disponíveis: {columns[:30]}"
        )
    return None


def _find_id_column(columns: list[str]) -> str | None:
    """Busca ID sem confundir campos descritivos como tipoincidente.

    A busca genérica por substring aceitava termos curtos demais, como
    "id", e podia transformar a coluna de tipo de incidente em ID.
    Isso fazia o ETL remover quase todas as linhas no drop_duplicates.
    """
    candidates = COLUMN_CANDIDATES["id_ocorrencia"]
    for candidate in candidates:
        if candidate in columns:
            return candidate

    blocked_prefixes = ("tipo", "descricao", "categoria", "natureza", "crime")
    for column in columns:
        if column.startswith(blocked_prefixes):
            continue
        if ("ocorrencia" in column or "boletim" in column) and (
            "id" in column or "cod" in column or "codigo" in column or "num" in column or "numero" in column
        ):
            return column
    return None


def infer_columns(df: pd.DataFrame) -> ColumnMap:
    columns = list(df.columns)
    return ColumnMap(
        data=_find_column(columns, COLUMN_CANDIDATES["data"], required=True),
        hora=_find_column(columns, COLUMN_CANDIDATES["hora"], required=False),
        municipio=_find_column(columns, COLUMN_CANDIDATES["municipio"], required=True),
        bairro=_find_column(columns, COLUMN_CANDIDATES["bairro"], required=False),
        crime=_find_column(columns, COLUMN_CANDIDATES["crime"], required=True),
        tipo_local=_find_column(columns, COLUMN_CANDIDATES["tipo_local"], required=False),
        id_ocorrencia=_find_id_column(columns),
        hora_inicio=_find_column(columns, COLUMN_CANDIDATES["hora_inicio"], required=False),
        hora_fim=_find_column(columns, COLUMN_CANDIDATES["hora_fim"], required=False),
    )
