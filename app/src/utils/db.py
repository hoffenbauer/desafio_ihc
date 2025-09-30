"""Funções utilitárias para conexão e consulta de dados em SQLite."""


import streamlit as st
import pandas as pd
import sqlite3
from pathlib import Path
import time
from paths import DB_PATH, PARQUET_PATH


@st.cache_data(show_spinner="Gerando banco de dados...")
def cria_banco_sqlite(data_path: Path = PARQUET_PATH, db_path: Path = DB_PATH) -> str:
    if DB_PATH.exists():
        print("Banco já existe, não foi recriado.")
    else:
        df = pd.read_parquet(data_path)

        # Conexão e exportação
        conn = sqlite3.connect(db_path)
        df.to_sql("coletas", conn, if_exists="replace", index=False)

        # Cria índices úteis
        cursor = conn.cursor()
        cursor.execute("CREATE INDEX idx_state ON coletas(state)")
        cursor.execute("CREATE INDEX idx_city ON coletas(city)")
        cursor.execute("CREATE INDEX idx_station ON coletas(station_name)")

        conn.commit()
        conn.close()
        print("Banco criado com sucesso.")
        # st.spinner("Banco criado com sucesso.")

    return "Banco já existe, não foi recriado."


@st.cache_data
def prepara_banco(*args):
    return cria_banco_sqlite(args)


# Mostra a mensagem temporária
status_msg = prepara_banco()

if status_msg != "Banco já existe, não foi recriado.":
    # Cria um placeholder para a mensagem
    placeholder = st.sidebar.empty()
    placeholder.success(status_msg)
    time.sleep(3)  # tempo em segundos
    placeholder.empty()


@st.cache_data
def obtem_dados_unicos(db_path: Path, coluna: str) -> list[str]:
    dados_unicos = []
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        query = f"SELECT DISTINCT {coluna} FROM coletas ORDER BY {coluna}"
        cursor.execute(query)
        dados_unicos = [row[0] for row in cursor.fetchall()]
    if coluna in ["state", "city"]:
        dados_unicos.remove("N/A")

    return dados_unicos


@st.cache_data
def query(db_path: Path, query: str, params: tuple = ()) -> list[str]:
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()


@st.cache_data
def busca_cidades(db_path: Path, estados: list[str]) -> list[str]:
    placeholders = ",".join(["?"] * len(estados))
    sql_query = f"SELECT DISTINCT city FROM coletas WHERE state IN ({placeholders}) ORDER BY city"
    params = tuple(estados)
    return [row[0] for row in query(db_path, sql_query, params)]


@st.cache_data
def busca_estacoes(db_path: Path, cidades: list[str]) -> list[str]:
    placeholders = ",".join(["?"] * len(cidades))
    sql_query = f"SELECT DISTINCT station_name FROM coletas WHERE city IN ({placeholders}) ORDER BY station_name"
    params = tuple(cidades)
    return [row[0] for row in query(db_path, sql_query, params)]


@st.cache_data
def busca_poluentes(db_path: Path, cidades: list[str]) -> list[str]:
    sql_query = "SELECT DISTINCT pollutant FROM coletas ORDER BY pollutant"
    return [row[0] for row in query(db_path, sql_query)]


@st.cache_data
def busca_coletas(db_path: Path, sql_query: str, params: tuple = ()) -> pd.DataFrame:
    with sqlite3.connect(db_path) as conn:
        return pd.read_sql_query(sql_query, conn, params=params)
