from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from src.config import get_settings  # noqa: E402


def generate_demo_data(path: Path, seed: int = 42) -> None:
    rng = np.random.default_rng(seed)
    settings = get_settings()
    municipalities = list(settings.municipalities)
    bairros = {
        "VITÓRIA": ["CENTRO", "JARDIM CAMBURI", "PRAIA DO CANTO", "SANTO ANTÔNIO"],
        "VILA VELHA": ["CENTRO", "GLÓRIA", "ITAPARICA", "PRAIA DA COSTA"],
        "SERRA": ["LARANJEIRAS", "JACARAÍPE", "CARAPINA", "FEU ROSA"],
        "CARIACICA": ["CAMPO GRANDE", "ITACIBÁ", "PORTO DE SANTANA", "JARDIM AMÉRICA"],
        "VIANA": ["CENTRO", "MARCÍLIO DE NORONHA", "AREINHA"],
        "GUARAPARI": ["CENTRO", "MUQUIÇABA", "PRAIA DO MORRO"],
        "FUNDÃO": ["CENTRO", "PRAIA GRANDE", "TIMBUÍ"],
    }
    date_range = pd.date_range(settings.start_date, settings.end_date, freq="D")
    base_intensity = {
        "VITÓRIA": 12,
        "VILA VELHA": 13,
        "SERRA": 17,
        "CARIACICA": 11,
        "VIANA": 3,
        "GUARAPARI": 5,
        "FUNDÃO": 1,
    }
    rows = []
    event_id = 1
    for date in date_range:
        weekend = date.weekday() >= 5
        month_factor = 1.15 if date.month in {1, 7, 12} else 1.0
        for municipality in municipalities:
            lam = base_intensity[municipality] * month_factor * (1.08 if weekend else 1.0)
            n = rng.poisson(lam)
            for _ in range(n):
                crime = rng.choice(["FURTO", "ROUBO"], p=[0.62, 0.38])
                if crime == "ROUBO":
                    hour = int(rng.choice([7, 8, 12, 17, 18, 19, 20, 21], p=[0.08, 0.08, 0.10, 0.18, 0.20, 0.15, 0.12, 0.09]))
                else:
                    weights = np.array([1,1,1,1,1,2,3,4,4,4,4,5,5,5,5,5,6,6,5,4,3,2,1,1], dtype=float)
                    hour = int(rng.choice(list(range(24)), p=weights / weights.sum()))
                if rng.random() < 0.025:
                    hour_text = "INDETERMINADO"
                else:
                    hour_text = f"{hour:02d}:00:00"
                rows.append(
                    {
                        "ID_OCORRENCIA": f"DEMO-{event_id:07d}",
                        "DATA_FATO": date.strftime("%d/%m/%Y"),
                        "HORA_FATO": hour_text,
                        "MUNICIPIO": municipality,
                        "BAIRRO": rng.choice(bairros[municipality]),
                        "TIPO_INCIDENTE": crime,
                        "TIPO_LOCAL": rng.choice(["VIA PÚBLICA", "RESIDÊNCIA", "COMÉRCIO", "TRANSPORTE"]),
                    }
                )
                event_id += 1
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False, sep=";", encoding="utf-8-sig")
    print(f"Dados sintéticos gerados em {path} ({len(rows):,} linhas).")


if __name__ == "__main__":
    settings = get_settings()
    generate_demo_data(settings.demo_raw_file)
