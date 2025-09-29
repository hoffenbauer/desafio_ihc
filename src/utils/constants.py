"""Constantes e mapeamentos de domínio usados em toda a aplicação."""

NA_VALUE = "N/A"

# Mapeamento amigável para rótulos exibidos no UI
POLUENTES_ROTULO = {
    "pol_a": "Poluente A",
    "pol_b": "Poluente B",
}

# Reverso para converter do rótulo exibido para o código do banco
POLUENTES_ROTULO_REVERSO = {v: k for k, v in POLUENTES_ROTULO.items()}
