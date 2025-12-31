import pathlib
import re
import sys
import os
import shutil
from datetime import datetime
from typing import Optional, Tuple, List, Dict


# --------------------
# 36進変換（既存モジュール相当の実装を内包）
# --------------------
_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyz"


def to_base36(n: int) -> str:
    if n < 0:
        raise ValueError("n must be non-negative")
    if n == 0:
        return "0"
    chars = []
    base = 36
    while n:
        n, r = divmod(n, base)
        chars.append(_ALPHABET[r])
    return "".join(reversed(chars))


def datetime_to_int(dt: datetime) -> int:
    ms = int(dt.microsecond / 1000)
    s = dt.strftime("%Y%m%d%H%M%S")
    return int(f"{s}{ms:03d}")


def make_timestamp_name(dt: Optional[datetime] = None) -> str:
    if dt is None:
        dt = datetime.now()
    n = datetime_to_int(dt)
    return to_base36(n)