# datetime_to_base36_renamer.py
"""ファイルを日時（年～秒＋ミリ秒）を36進数に変換した名前にリネームするモジュール

主な関数:
- to_base36(n): 整数 n を小文字の36進数文字列に変換
- datetime_to_int(dt): datetime -> YYYYMMDDHHMMSSmmm の整数
- make_timestamp_name(dt=None): dt(省略時=now) を変換してベース36文字列を返す (拡張子無し)
- rename_file_to_timestamp(path, dt=None, keep_ext=True, allow_collision_suffix=True):
    指定ファイルをリネーム（同名衝突時はサフィックス追加）
- rename_files_in_dir(dirpath, pattern="*", **kwargs):
    ディレクトリ中の複数ファイルを順にリネーム（glob パターン指定可）
"""

from __future__ import annotations
import os
from datetime import datetime
import pathlib
import typing
import glob

_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyz"

def to_base36(n: int) -> str:
    """非負整数 n を base36 小文字文字列に変換。0 は '0' を返す。"""
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
    """datetime -> 整数 YYYYMMDDHHMMSSmmm を返す（ミリ秒3桁）。"""
    ms = int(dt.microsecond / 1000)  # ミリ秒
    s = dt.strftime("%Y%m%d%H%M%S")
    return int(f"{s}{ms:03d}")

def make_timestamp_name(dt: typing.Optional[datetime] = None) -> str:
    """datetime (省略時=now) を base36 に変換したファイル名ベースを返す。"""
    if dt is None:
        dt = datetime.now()
    n = datetime_to_int(dt)
    return to_base36(n)

def _unique_target_path(target_path: pathlib.Path, allow_suffix: bool = True) -> pathlib.Path:
    """target_path が存在する場合、_1, _2... を付けてユニークにする（allow_suffix True の場合）。"""
    if not target_path.exists():
        return target_path
    if not allow_suffix:
        raise FileExistsError(f"Target exists: {target_path}")
    parent = target_path.parent
    stem = target_path.stem
    suffix = target_path.suffix
    i = 1
    while True:
        candidate = parent / f"{stem}_{i}{suffix}"
        if not candidate.exists():
            return candidate
        i += 1

def rename_file_to_timestamp(path: typing.Union[str, os.PathLike],
                             dt: typing.Optional[datetime] = None,
                             keep_ext: bool = True,
                             allow_collision_suffix: bool = True) -> pathlib.Path:
    """単一ファイルを日時-based36 名にリネームして新しい Path を返す。
    - keep_ext=True の場合、元の拡張子を保持する（例: .txt）。
    - allow_collision_suffix=True の場合、既に同名があれば _1, _2... を追加して衝突回避。
    """
    p = pathlib.Path(path)
    if not p.exists():
        raise FileNotFoundError(p)

    base = make_timestamp_name(dt)
    new_name = base + (p.suffix if keep_ext else "")
    target = p.with_name(new_name)
    target = _unique_target_path(target, allow_suffix=allow_collision_suffix)
    p.rename(target)
    return target

def rename_files_in_dir(dirpath: typing.Union[str, os.PathLike],
                        pattern: str = "*",
                        keep_ext: bool = True,
                        allow_collision_suffix: bool = True,
                        sort_by: str = "mtime") -> list[pathlib.Path]:
    """
    ディレクトリ内の複数ファイルを順にリネームする。
    - pattern: glob パターン（例: '*.png'）
    - sort_by: 'mtime' (更新時刻) or 'name' (名前) or 'none'
    戻り値: 新しい Path のリスト（処理順）
    """
    dirp = pathlib.Path(dirpath)
    if not dirp.is_dir():
        raise NotADirectoryError(dirp)
    files = [pathlib.Path(p) for p in glob.glob(str(dirp / pattern))]
    if sort_by == "mtime":
        files.sort(key=lambda p: p.stat().st_mtime)
    elif sort_by == "name":
        files.sort(key=lambda p: p.name)
    # else leave unsorted

    results = []
    for f in files:
        if f.is_file():
            newp = rename_file_to_timestamp(f, dt=None, keep_ext=keep_ext, allow_collision_suffix=allow_collision_suffix)
            results.append(newp)
    return results

# --- 簡単なコマンドラインテスト用 ---
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Rename files to datetime-based base36 names.")
    parser.add_argument("paths", nargs="+", help="file or directory paths to process")
    parser.add_argument("--dir", action="store_true", help="treat given path(s) as directories and rename all files inside")
    parser.add_argument("--pattern", default="*", help="when --dir: glob pattern (default '*')")
    parser.add_argument("--no-ext", action="store_true", help="do not keep original extension")
    parser.add_argument("--no-suffix", action="store_true", help="do not add _1/_2 when collision")
    args = parser.parse_args()

    for p in args.paths:
        if args.dir:
            try:
                res = rename_files_in_dir(p, pattern=args.pattern, keep_ext=not args.no_ext, allow_collision_suffix=(not args.no_suffix))
                for r in res:
                    print("RENAMED:", r)
            except Exception as e:
                print("ERROR:", p, e)
        else:
            try:
                newp = rename_file_to_timestamp(p, keep_ext=not args.no_ext, allow_collision_suffix=(not args.no_suffix))
                print("RENAMED:", newp)
            except Exception as e:
                print("ERROR:", p, e)
