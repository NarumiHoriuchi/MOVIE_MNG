from datetime import datetime
from pathlib import Path

LOG_FILE = Path("logs/app.log")
LOG_FILE.parent.mkdir(exist_ok=True)

def logprint(script: str, message: str, *, level: str = "INFO") -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{script}] [{timestamp}] [{level}] {message}\n"

    print(line, end="")
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line)
