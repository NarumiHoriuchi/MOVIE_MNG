#!/usr/bin/env python3
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
import lib.sha256 as sha256

# ファイル名のみ（例: my_script.py）
script_name = os.path.basename(__file__)
# print(f"ファイル名: {file_name}")

# --------------------
# log出力
# --------------------
import lib.log as log


# --------------------
# init 処理
# --------------------
from config.settings import VIDEO_DB_PATH, MEDIA_DIR, CHECKIN_DIR


# --------------------
# 36進変換（既存モジュール相当の実装を内包）
# --------------------
import lib.make_base36 as make_base36

# --------------------
# ファイル名パーサ
# --------------------
import lib.filename_parser as filename_parser


# --------------------
# DB Writer (SQLite)
# --------------------
import lib.db as db


# --------------------
# ファイル操作ユーティリティ
# --------------------
import lib.file_operation as file_operation


# --------------------
# メイン処理
# --------------------

def collect_files(cwd: pathlib.Path, exts: Optional[List[str]] = None, pattern: str = "*") -> List[pathlib.Path]:
    # files = [p for p in cwd.glob(pattern) if file_operation.is_video_file(p, exts)]
    files = []
    for p in cwd.glob(pattern):
        if file_operation.is_video_file(p, exts):
            files.append(p)

    files.sort(key=lambda p: p.name)
    return files


def process_file(p: pathlib.Path, dest_root: pathlib.Path, db: Optional[DBWriter]) -> Dict[str, str]:
    orig_name = p.name
    parsed = filename_parser.parse_filename(p.name)
    log.logprint(script_name, f"parsed = {parsed}")

    # 1) Rename to base36 (use current time for uniqueness)
    checkin_time = datetime.now()
    file_id = make_base36.make_timestamp_name(checkin_time)
    # We'll construct new name as file_id + original ext; but use rename_to_base36 to avoid collision logic duplication

    new_name = file_id + p.suffix
    # new_path = p.with_name(new_name)
    # print(f"new_name = {new_name}")

    # 2) Move to YYYY/MM/DD folder under dest_root
    #    moved_path = pathlib.Path(dest_root) / checkin_time.strftime("%Y") / checkin_time.strftime("%m") / checkin_time.strftime("%d") / new_path.name
    if parsed.publish_date:
        # アップロード日を取得できた場合
        # print(parsed.publish_date)
        dt = datetime.strptime(parsed.publish_date, "%Y%m%d")
    # log.logprint(script_name, f"ファイルを移動します: {moved_path}")
    #    moved_path = move_to_date_folder(new_path, dest_root, dt=checkin_time)
    moved_path = pathlib.Path(dest_root) / checkin_time.strftime("%Y") / checkin_time.strftime("%m") / checkin_time.strftime("%d") 
    # print(f"moved_oath = {moved_path}")
    
    # チェックサム計算
    source_full_path = CHECKIN_DIR / orig_name
    log.logprint(script_name, f"ファイルのチェックサム計算を開始。{source_full_path}")
    check_sha256 = sha256.calc_checksum(source_full_path)
    log.logprint(script_name, f"ファイルのチェックサム値（{check_sha256})")
    
    # Videosテーブルからchecksumを検索する。
    log.logprint(script_name, "Videosテーブルからchecksum値を検索。")
    ret = db.select_checksum(check_sha256)
    log.logprint(script_name, f"Videosテーブルからchecksum値を検索結果 ({ret})。")
    
    # ここで、値が返ってきたらこのレコード処理は中止。
    if ret is None:
        log.logprint(script_name, "対象ファイルはまだ、登録されていません。処理を継続します。")
        skip_flag = False
    else:
        log.logprint(script_name, "対象ファイルが、登録されています。処理をスキップします。")
        skip_flag = True
    
    # ファイルの移動処理
    if skip_flag == False:
        res = file_operation.move_to_date_folder(CHECKIN_DIR, orig_name, moved_path, new_name)
    return skip_flag, [file_id, parsed.title, parsed.author, parsed.publish_date, str(moved_path), checkin_time.isoformat(), p.name, check_sha256], [CHECKIN_DIR, orig_name, moved_path, new_name]


def main(argv: Optional[List[str]] = None):
    #cwd = pathlib.Path(".").resolve()
    log.logprint(script_name, "スクリプトを開始しました")
    log.logprint(script_name, "変数の初期化を開始")
    cwd = pathlib.Path("Checkin/").resolve()
    dest_root = pathlib.Path("media/").resolve()

    log.logprint(script_name, "対象ファイルの確認")
    files = collect_files(cwd)
    if not files:
        # logging.info("No target files found in %s", cwd)
        log.logprint(script_name, f"対象ファイルがありません。 {cwd}")
        return

    # ファイルの移動とデータベース処理
    log.logprint(script_name, f"Videos.DB の確認を実行 {VIDEO_DB_PATH}")
    dbw = db.videosDBWriter(VIDEO_DB_PATH)
    if dbw is None:
        log.logprint(script_name, "テーブルが初期化されていません。", level="Error")
        log.logprint(script_name, "スクリプトを終了します。")
        sys.exit()

    results = []
    for f in files:
        try:
            log.logprint(script_name, f"対象ファイル名。{f}")
            skip_flag, db_data, file_info = process_file(f, dest_root, dbw)
            # DB処理
            if skip_flag == False:
                print(db_data)
                log.logprint(script_name, f"データ {db_data[1]} の追加処理開始")
                dbw = db.videosDBWriter(VIDEO_DB_PATH)
                ret = dbw.insert_video(db_data[0], db_data[1], db_data[2], db_data[3], db_data[4], db_data[5], db_data[6], db_data[7])
                log.logprint(script_name, f"データ {db_data[1]} の追加処理終了")
                res = {
                    "original": db_data[6],
                    "file_id": db_data[0],
                    "title": db_data[1] or "",
                    "author": db_data[2] or "",
                    "publish_date": db_data[3] or "",
                    "folder_path": db_data[4],
                }
                results.append(res)
            else:
                log.logprint(script_name, "データ追加処理はスキップします。")
        except Exception as e:
            log.logprint(script_name,f"データのインサート処理でエラーが発生しました。 {e}", level="Error")
            log.logprint(script_name,"移動したファイルを元に戻します。")
            target_full_path = file_info[2] / file_info[3]
            orig_full_path = file_info[0] / file_info[1]
            shutil.move(target_full_path, orig_full_path)
            log.logprint(script_name,f"戻したファイル ({target_full_path})")
            log.logprint(script_name, "スクリプトを終了しました")

    if dbw:
        dbw.close()
    log.logprint(script_name, "スクリプトを終了しました")

if __name__ == '__main__':
    main()
