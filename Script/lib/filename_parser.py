import os
from dataclasses import dataclass
from typing import Optional
import pathlib
import re


# ファイル名のみ（例: my_script.py）
script_name = os.path.basename(__file__)
# print(f"ファイル名: {file_name}")


# --------------------
# ファイル名パーサ
# --------------------

@dataclass
class ParsedMeta:
    title: Optional[str]
    author: Optional[str]
    publish_date: Optional[str]  # YYYYMMDD or None


TITLE_DELIM = "("  # 最初の ( より前をタイトルとする


def parse_filename(fname: str) -> ParsedMeta:
    """
    ファイル名から title, author, publish_date を抜き出す。

    想定フォーマット:
      ...(<displayname>@<handle>,YYYYMMDD)

    例:
      ...[vhX7bJ37ukA](ゆっくりオカルトQ@occultQ,20240521).mp4
    """
    name = pathlib.Path(fname).name

    # 拡張子除去
    stem = name.rsplit(".", 1)[0] if "." in name else name

    title = None
    author = None
    publish = None

    if TITLE_DELIM in stem:
        idx = stem.find(TITLE_DELIM)
        title = stem[:idx].strip()
        tail = stem[idx + 1 :].strip()

        if tail.endswith(")"):
            tail = tail[:-1]

        if "," in tail:
            left, right = tail.rsplit(",", 1)
            right = right.strip()

            if re.fullmatch(r"\d{8}", right):
                publish = right

            author = left.strip() if left.strip() else None
        else:
            author = tail.strip() if "@" in tail else None
    else:
        title = stem

    return ParsedMeta(
        title=title or None,
        author=author or None,
        publish_date=publish or None,
    )
