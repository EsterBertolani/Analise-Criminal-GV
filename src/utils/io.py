from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd


def file_sha256(path: Path, chunk_size: int = 1024 * 1024) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(chunk_size), b""):
            sha.update(chunk)
    return sha.hexdigest()


def read_csv_flexible(path: Path, nrows: int | None = None) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")

    encodings = ["utf-8-sig", "utf-8", "latin-1", "cp1252"]
    separators = [None, ";", ",", "|", "\t"]
    last_error: Exception | None = None
    best: pd.DataFrame | None = None

    for encoding in encodings:
        for sep in separators:
            try:
                candidate = pd.read_csv(
                    path,
                    sep=sep,
                    encoding=encoding,
                    engine="python" if sep is None else "c",
                    nrows=nrows,
                    low_memory=False,
                )
                if best is None or candidate.shape[1] > best.shape[1]:
                    best = candidate
                if candidate.shape[1] > 1:
                    return candidate
            except Exception as exc:  # noqa: BLE001
                last_error = exc

    if best is not None:
        return best
    raise RuntimeError(f"Não foi possível ler {path}. Último erro: {last_error}")


def save_json(data: dict[str, Any] | list[Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2, default=str)


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_table(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    suffix = path.suffix.lower()
    if suffix == ".parquet":
        df.to_parquet(path, index=False)
    elif suffix == ".csv":
        df.to_csv(path, index=False, encoding="utf-8-sig")
    else:
        raise ValueError(f"Formato não suportado: {suffix}")


def read_table(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".parquet":
        return pd.read_parquet(path)
    if suffix == ".csv":
        return pd.read_csv(path)
    raise ValueError(f"Formato não suportado: {suffix}")
