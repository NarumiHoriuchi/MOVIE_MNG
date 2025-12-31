import os
import pathlib
import re
import sys
import os
import shutil
from typing import Optional, Tuple, List, Dict
from datetime import datetime


# ファイル名のみ（例: my_script.py）
script_name = os.path.basename(__file__)
# print(f"ファイル名: {file_name}")


# --------------------
# log出力
# --------------------
import lib.log as log


# --------------------
# ファイル操作ユーティリティ
# --------------------
VIDEO_EXTS = {"mp4", "mkv", "webm", "mov", "mp3", "avi", "flv"}


def is_video_file(p: pathlib.Path, exts: Optional[List[str]] = None) -> bool:
    if exts:
        allowed = {e.lower().lstrip(".") for e in exts}
    else:
        allowed = VIDEO_EXTS
    return p.is_file() and p.suffix.lower().lstrip(".") in allowed


def _unique_target_path(target_path: pathlib.Path, allow_suffix: bool = True) -> pathlib.Path:
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


def rename_to_base36(p: pathlib.Path, dt: Optional[datetime] = None, keep_ext: bool = True, allow_collision_suffix: bool = True) -> pathlib.Path:
    base = make_timestamp_name(dt)
    new_name = base + (p.suffix if keep_ext else "")
    target = p.with_name(new_name)
    target = _unique_target_path(target, allow_suffix=allow_collision_suffix)
    p.rename(target)
    return target


def move_to_date_folder(source_dir, orig_name, moved_path, new_name) -> str:
    # log.logprint(script_name, f"orig_name = {orig_name}")
    """
    if dt is None:
        dt = datetime.now()
    yyyy = dt.strftime("%Y")
    mm = dt.strftime("%m")
    dd = dt.strftime("%d")
    dest_dir = pathlib.Path(root) / yyyy / mm / dd
    """
    dest_dir = moved_path
    orig_full_path = source_dir / orig_name
    log.logprint(script_name, f"移動前ファイルパス名 {orig_full_path}")
    # dest_dir.mkdir(parents=True, exist_ok=True)
    # target = dest_dir / p.name
    moved_path.mkdir(parents=True, exist_ok=True)
    target_full_path = dest_dir / new_name
    # target = _unique_target_path(target, allow_suffix=True)
    log.logprint(script_name, f"移動先ファイルパス名 {target_full_path}")
    shutil.move(orig_full_path, target_full_path)
    return 
