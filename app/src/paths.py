from pathlib import Path

# Este arquivo vive em app/src/paths.py
# parent_path = repo root
parent_path = Path(__file__).resolve().parents[2]

PARQUET_PATH = parent_path / "data" / "pontos_coleta_municipios_longo.parquet"
DB_PATH = parent_path / "data" / "coletas.db"
