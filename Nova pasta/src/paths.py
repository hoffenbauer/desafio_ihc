from pathlib import Path

parent_path = Path(__file__).resolve().parents[1]


PARQUET_PATH = parent_path / "data" / "pontos_coleta_municipios_longo.parquet"
DB_PATH = parent_path / "data" / "coletas.db"
