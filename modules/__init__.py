# import sys
# from pathlib import Path

# p = f"{Path(sys.prefix).absolute().parent}/modules"
# sys.path.append(str(p))
# print(sys.path)

# Define the __all__ variable
__all__ = [
    "path",
]

# # Import the submodules
from . import path
