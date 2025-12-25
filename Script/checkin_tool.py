#!/usr/bin/env python3
"""checkin_tool.py

カレントディレクトリ（".") 内の動画ファイルをチェックインする一体型スクリプト。
主な機能：
 - ファイル名からメタ情報を抽出（タイトル／著者／公開日）
 - ファイルを36進数日時名にリネーム（内部実装を含む）
 - 実行日ベースで YYYY/MM/DD フォルダへ移動
 - SQLite にメタ情報を登録

使い方（例）:
  # まずは実働せずに動作確認（dry-run）
  python checkin_tool.py --dry-run --verbose

  # 実際にチェックインして移動・DB登録
  python checkin_tool.py --db ./videos.db

設計上のポイント：
 - ファイル名パースは "(" をタイトル切り取りのデリミタとする。
 - 著者は "(" と "@" の間、公開日はカンマ "," と ")" の間を想定。
 - イレギュラーなファイル名は部分的にしか抽出できない場合がある。
 - DB は SQLite（ファイル）で簡易に扱う。必要なら他DBに差し替え可能。

"""

from __future__ import annotations
import argparse
import logging
import sqlite3
from dataclasses import dataclass
from datetime import datetime
import pathlib
import re
import sys
import os
import shutil
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
    """ファイル名から title, author, publish_date を抜き出す。

    想定フォーマット:
      ...(<displayname>@<handle>,YYYYMMDD)

    例:
      ...[vhX7bJ37ukA](ゆっくりオカルトQ@occultQ,20240521).mp4

    ルールは柔軟にしているが100%完璧ではないため、
    抽出できない要素は None を返す。
    """
    name = pathlib.Path(fname).name
    # 拡張子除去
    stem = name
    if "." in name:
        stem = name.rsplit(".", 1)[0]

    # タイトル抽出（最初の '(' の前まで）
    title = None
    author = None
    publish = None

    if TITLE_DELIM in stem:
        idx = stem.find(TITLE_DELIM)
        title = stem[:idx].strip()
        tail = stem[idx + 1 :].strip()
        # tail は e.g. "ゆっくりオカルトQ@occultQ,20240521)" など
        # 最後の ')' をトリム
        if tail.endswith(")"):
            tail = tail[:-1]
        # author と日付をカンマで分割
        # ただし author 部に @ が含まれる前提で切る
        # パターン: (display@handle,YYYYMMDD)
        # まずカンマを探す
        if "," in tail:
            left, right = tail.rsplit(",", 1)
            right = right.strip()
            # right は日付らしい文字列
            if re.fullmatch(r"\d{8}", right):
                publish = right
            else:
                # 日付形式でない場合は None
                publish = None
            # left に著者文字列
            # left をさらに '@' で分割してハンドルを想定
            # 例: "ゆっくりオカルトQ@occultQ"
            if "@" in left:
                # author を display@handle の形で保持
                author = left.strip()
            else:
                # @ がない場合は left 全体を author として保存
                author = left.strip()
        else:
            # カンマが無い—著者/日付の形式ではない
            # try to extract author-like with @
            if "@" in tail:
                author = tail.strip()
            else:
                author = None
    else:
        # '(' がない場合はタイトルは拡張子を除いた全体
        title = stem

    # Normalize empty strings to None
    title = title if title and title != "" else None
    author = author if author and author != "" else None
    publish = publish if publish and publish != "" else None

    return ParsedMeta(title=title, author=author, publish_date=publish)


# --------------------
# DB Writer (SQLite)
# --------------------
class DBWriter:
    def __init__(self, db_path: pathlib.Path):
        self.db_path = pathlib.Path(db_path)
        self.conn = sqlite3.connect(str(self.db_path))
        self._ensure_schema()

    def _ensure_schema(self):
        c = self.conn.cursor()
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id TEXT UNIQUE,
                title TEXT,
                author TEXT,
                publish_date TEXT,
                stored_path TEXT,
                checkin_time TEXT,
                original_filename TEXT
            )
            """
        )
        self.conn.commit()

    def insert_video(self, file_id: str, title: Optional[str], author: Optional[str], publish_date: Optional[str], stored_path: str, checkin_time: str, original_filename: str) -> None:
        c = self.conn.cursor()
        try:
            c.execute(
                """
                INSERT INTO videos (file_id, title, author, publish_date, stored_path, checkin_time, original_filename)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (file_id, title, author, publish_date, stored_path, checkin_time, original_filename),
            )
            self.conn.commit()
        except sqlite3.IntegrityError as e:
            logging.warning("DB insert failed (maybe duplicate file_id): %s", e)

    def close(self):
        self.conn.close()


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


def move_to_date_folder(p: pathlib.Path, root: pathlib.Path, dt: Optional[datetime] = None) -> pathlib.Path:
    if dt is None:
        dt = datetime.now()
    yyyy = dt.strftime("%Y")
    mm = dt.strftime("%m")
    dd = dt.strftime("%d")
    dest_dir = pathlib.Path(root) / yyyy / mm / dd
    dest_dir.mkdir(parents=True, exist_ok=True)
    target = dest_dir / p.name
    target = _unique_target_path(target, allow_suffix=True)
    shutil.move(str(p), str(target))
    return target


# --------------------
# メイン処理
# --------------------

def collect_files(cwd: pathlib.Path, exts: Optional[List[str]] = None, pattern: str = "*") -> List[pathlib.Path]:
    files = [p for p in cwd.glob(pattern) if is_video_file(p, exts)]
    files.sort(key=lambda p: p.name)
    return files


def process_file(p: pathlib.Path, dest_root: pathlib.Path, db: Optional[DBWriter], dry_run: bool = False, debug: bool = False) -> Dict[str, str]:
    logging.info("Processing: %s", p)
    parsed = parse_filename(p.name)
    logging.debug("Parsed meta: %s", parsed)

    # 1) Rename to base36 (use current time for uniqueness)
    checkin_time = datetime.now()
    file_id = make_timestamp_name(checkin_time)
    # We'll construct new name as file_id + original ext; but use rename_to_base36 to avoid collision logic duplication

    if dry_run:
        new_name = file_id + p.suffix
        new_path = p.with_name(new_name)
        logging.info("[DRY] Would rename %s -> %s", p.name, new_path.name)
    else:
        # To keep transactional safety: rename in place, then move
        new_path = rename_to_base36(p, dt=checkin_time, keep_ext=True, allow_collision_suffix=True)
        logging.info("Renamed to: %s", new_path.name)

    # 2) Move to YYYY/MM/DD folder under dest_root
    if dry_run:
        moved_path = pathlib.Path(dest_root) / checkin_time.strftime("%Y") / checkin_time.strftime("%m") / checkin_time.strftime("%d") / new_path.name
        logging.info("[DRY] Would move to: %s", moved_path)
    else:
        moved_path = move_to_date_folder(new_path, dest_root, dt=checkin_time)
        logging.info("Moved to: %s", moved_path)

    # 3) DB insert
    if db and not dry_run:
        db.insert_video(
            file_id=file_id,
            title=parsed.title,
            author=parsed.author,
            publish_date=parsed.publish_date,
            stored_path=str(moved_path),
            checkin_time=checkin_time.isoformat(),
            original_filename=p.name,
        )
        logging.info("Inserted DB record for %s", file_id)

    return {
        "original": p.name,
        "file_id": file_id,
        "title": parsed.title or "",
        "author": parsed.author or "",
        "publish_date": parsed.publish_date or "",
        "stored_path": str(moved_path),
    }


def main(argv: Optional[List[str]] = None):
    parser = argparse.ArgumentParser(description="Check-in video files in current directory")
    parser.add_argument("--db", type=str, default="./videos.db", help="SQLite DB path (default: ./videos.db)")
    parser.add_argument("--root", type=str, default=".", help='Root folder to store YYYY/MM/DD (default: current dir)')
    parser.add_argument("--pattern", type=str, default="*", help='glob pattern to select files (default: "*")')
    parser.add_argument("--ext", type=str, nargs="*", default=None, help='extension filter, e.g. --ext mp4 mkv')
    parser.add_argument("--dry-run", action="store_true", help="Do not perform filesystem changes or DB writes; show actions only")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")
    parser.add_argument("--debug", action="store_true", help="Debug logging (more) and keep intermediate files on error)")
    args = parser.parse_args(argv)

    log_level = logging.DEBUG if args.debug or args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format="%(asctime)s %(levelname)s: %(message)s")

    #cwd = pathlib.Path(".").resolve()
    cwd = pathlib.Path("Checkin/").resolve()
    dest_root = pathlib.Path(args.root).resolve()
    dest_root = dest_root / "media"

    files = collect_files(cwd, exts=args.ext, pattern=args.pattern)
    if not files:
        logging.info("No target files found in %s", cwd)
        return

    dbw = None
    if not args.dry_run:
        dbw = DBWriter(pathlib.Path(args.db))
    else:
        logging.info("Dry-run: DB writes disabled")

    results = []
    for f in files:
        try:
            res = process_file(f, dest_root, dbw, dry_run=args.dry_run, debug=args.debug)
            results.append(res)
        except Exception as e:
            logging.exception("Failed processing %s: %s", f, e)
            if args.debug:
                logging.error("Debug mode: stopping on first error")
                break
            else:
                logging.warning("Continuing to next file")

    if dbw:
        dbw.close()

    # summary
    logging.info("Processed %d files", len(results))
    for r in results:
        logging.info("- %s -> %s", r['original'], r['file_id'])


if __name__ == '__main__':
    main()
