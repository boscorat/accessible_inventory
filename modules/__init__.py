import sys
from pathlib import Path

p = f"{Path(sys.prefix).absolute().parent}/modules"
sys.path.append(str(p))
print(sys.path)
