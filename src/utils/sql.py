"""Funções utilitárias para manipulação de consultas SQL em SQLite."""
from typing import List, Sequence, Tuple
import warnings


def placeholders(n: int) -> str:
    """Retorna uma string de placeholders do SQLite do tipo '?, ?, ?' com n itens.

    Args:
        n (int): quantidade de placeholders.
    Returns:
        str: string com os placeholders.
    """
    if not isinstance(n, int):
        warnings.warn(f"Esperado int para n, {type(n)} recebido. Convertendo para int.")
        try:
            n = int(n)
            warnings.warn(f"Convertido {n} para int.")
        except (ValueError, TypeError):
            warnings.warn(
                f"Não foi possível converter {n} para int. Retornando string vazia."
            )
            return ""
    if n <= 0:
        return ""
    return ",".join(["?"] * n)


def efetiva_selecao(selecao: Sequence[str] | None, padrao: Sequence[str]) -> List[str]:
    """Retorna a seleção efetiva dos filtros; se a seleção estiver vazia/None, usa o padrão.
    Args:
        selecao (Sequence[str] | None): Critérios de seleção dos filtros (pode ser vazia ou None).
        padrao (Sequence[str]): Seleção padrão (default, todas as opções disponíveis).
    Returns:
        List[str]: Seleção efetiva (selecao ou padrao).
    """
    if not isinstance(selecao, (Sequence, type(None))):
        warnings.warn(
            f"Esperado Sequence[str] ou None para selecao, {type(selecao)} recebido. Convertendo para str."
        )
        try:
            selecao = str(selecao)
            warnings.warn(f"Convertido {selecao} para str.")
        except (ValueError, TypeError):
            warnings.warn(
                f"Não foi possível converter {selecao} para str. Usando padrão."
            )
            return list(padrao)

    if not selecao:
        return list(padrao)
    return list(selecao)


def clausula_in(coluna: str, valores: Sequence[str]) -> Tuple[str, List[str]]:
    """Constroi uma cláusula IN e retorna também os valores como params usandos nas consultas.
    Args:
        coluna (str): Nome da coluna para a cláusula IN.
        valores (Sequence[str]): Valores para a cláusula IN.

    Returns:
        Tuple[str, List[str]]: Tupla com a cláusula SQL e a lista de valores.

    Ex.: clausula_in("state", ["SP","RJ"]) -> ("state IN (?,?)", ["SP","RJ"]).
    """
    vals = list(valores)
    if not vals:
        return "1=0", []  # nenhum valor -> evita retornar tudo por engano
    return f"{coluna} IN ({placeholders(len(vals))})", vals


def monta_filtro_terrestre(
    estados: Sequence[str],
    cidades: Sequence[str],
    estacoes: Sequence[str],
    poluentes: Sequence[str],
) -> Tuple[str, List[str]]:
    """Monta a cláusula composta para filtro terrestre com params.
    Args:
        estados (Sequence[str]): Lista de estados para o filtro.
        cidades (Sequence[str]): Lista de cidades para o filtro.
        estacoes (Sequence[str]): Lista de estações para o filtro.
        poluentes (Sequence[str]): Lista de poluentes para o filtro.
    Returns:
        Tuple[str, List[str]]: Tupla com a cláusula SQL e a lista de parâmetros.
    """
    if not all(
        isinstance(lst, Sequence) for lst in [estados, cidades, estacoes, poluentes]
    ):
        raise TypeError("Todos os argumentos devem ser do tipo sequência.")

    parts: List[str] = []
    params: List[str] = []

    # Monta as partes da cláusula WHERE

    for coluna, valores in (
        ("state", estados), 
        ("city", cidades),
        ("station_name", estacoes),
        ("pollutant", poluentes),
    ):
        # Adiciona a cláusula e os parâmetros se houver valores
        sql_part, p = clausula_in(coluna, valores)
        parts.append(sql_part)
        params.extend(p)

    return "(" + " AND ".join(parts) + ")", params
