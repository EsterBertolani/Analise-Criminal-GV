from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

import pandas as pd  # noqa: E402

from src.analysis.eda import build_eda_outputs  # noqa: E402
from src.analysis.spatial import build_spatial_outputs  # noqa: E402
from src.cache.build_cache import build_dashboard_cache  # noqa: E402
from src.config import get_settings  # noqa: E402
from src.data.etl import run_etl  # noqa: E402
from src.models.train_all import train_all_models  # noqa: E402
from src.utils.io import read_table  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Executa ETL, EDA, modelos e cache do MVP.")
    parser.add_argument("--csv", type=str, default=None, help="Caminho para o CSV oficial ou sintético.")
    parser.add_argument("--skip-models", action="store_true", help="Executa apenas ETL/EDA/cache sem treinar modelos.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = get_settings()
    raw_path = Path(args.csv) if args.csv else settings.default_raw_file
    if not raw_path.is_absolute():
        raw_path = settings.project_root / raw_path
    if not raw_path.exists() and settings.demo_raw_file.exists():
        print("Arquivo oficial não encontrado. Usando dados sintéticos de demonstração.")
        raw_path = settings.demo_raw_file
    if not raw_path.exists():
        raise FileNotFoundError(
            "Nenhum CSV encontrado. Coloque MICRODADOS_OCORRENCIAS.csv em data/raw/ "
            "ou gere dados sintéticos com: python scripts/generate_demo_data.py"
        )

    print(f"[1/5] ETL: {raw_path}")
    run_etl(raw_path, settings)

    print("[2/5] Agregações exploratórias")
    df = read_table(settings.processed_dir / "ocorrencias_tratadas.csv")
    df["data_fato"] = pd.to_datetime(df["data_fato"], errors="coerce")
    print(
        f"      Linhas após filtro: {len(df):,} | "
        f"meses distintos: {df['ano_mes'].nunique() if 'ano_mes' in df.columns else 0} | "
        f"período: {df['data_fato'].min()} a {df['data_fato'].max()}"
    )
    aoristic = read_table(settings.processed_dir / "pesos_aoristicos.csv")
    eda_outputs = build_eda_outputs(df, aoristic, settings)

    print("[3/5] Saídas espaciais")
    municipal = pd.read_csv(eda_outputs["municipal_summary"])
    build_spatial_outputs(municipal, settings)

    if not args.skip_models:
        print("[4/5] Modelos preditivos com validação temporal")
        train_all_models(settings)
    else:
        print("[4/5] Modelos pulados por --skip-models")

    print("[5/5] Cache do dashboard")
    manifest = build_dashboard_cache(settings)
    print(f"Cache gerado com {len(manifest['files'])} arquivos. Ausentes: {manifest['missing']}")


if __name__ == "__main__":
    main()
