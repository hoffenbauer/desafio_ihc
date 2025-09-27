import inspect
import src.utils.utils as utils  # ou apenas `import utils.utils` dependendo do sys.path

public_symbols = [
    name for name in inspect.getmembers(utils) if not name.startswith("_")
]

print("__all__ =", public_symbols)
