import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

try:
    from pipelines.phase1 import main
    main()
    print("ALL OK")
except BaseException as e:
    with open("debug_err.txt", "w", encoding="utf-8") as f:
        f.write(f"Exception type: {type(e)}\n")
        f.write(f"Exception msg: {e}\n")
        traceback.print_exc(file=f)
    print("FAILED, check debug_err.txt")
