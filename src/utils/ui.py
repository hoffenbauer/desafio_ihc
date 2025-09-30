""" Utilitários para componentes de UI do Streamlit."""

import streamlit as st
from typing import List, Sequence


def pills_multi(
    label: str,
    options: Sequence[str],
    default: Sequence[str] | None,
    key: str,
    help: str | None = None,
) -> List[str]:
    """Wrapper para st.sidebar.pills com selection_mode="multi" e default opcional.

    Retorna a lista selecionada (pode ser vazia).
    """
    return st.sidebar.pills(
        label=label,
        options=list(options),
        default=list(default) if default is not None else None,
        key=key,
        selection_mode="multi",
        help=help,
    )


def multiselecao_todos_padrao(
    label: str,
    options: Sequence[str],
    key: str,
    help: str | None = None,
) -> List[str]:
    """Cria um multiselect com todas as opções pré-selecionadas por padrão.
    Se options estiver vazio, retorna lista vazia.
    """
    opts = list(options)
    return st.sidebar.multiselect(label, opts, default=opts, key=key, help=help)


def informa_se(condicao: bool, mensagem: str) -> None:
    """Exibe uma mensagem informativa na barra lateral se a condição for verdadeira.

    Args:
        condicao (bool): Indica se a mensagem deve ser exibida.
        mensagem (str): A mensagem a ser exibida.
    """
    if condicao:
        st.sidebar.info(mensagem)


def avisa_se(condicao: bool, mensagem: str) -> None:
    """Exibe uma mensagem de aviso na barra lateral se a condição for verdadeira.
    Args:
        condicao (bool): Indica se a mensagem deve ser exibida.
        mensagem (str): A mensagem a ser exibida.
    """
    if condicao:
        st.warning(mensagem)
