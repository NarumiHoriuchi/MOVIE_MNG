import os
import sqlite3
import pathlib
from typing import Optional, Tuple, List, Dict

# ファイル名のみ（例: my_script.py）
script_name = os.path.basename(__file__)
# print(f"ファイル名: {file_name}")

# --------------------
# log出力
# --------------------
import lib.log as log

# --------------------
# DB Writer (SQLite)
# --------------------
class videosDBWriter:
    def __init__(self, db_path: str):
        log.logprint(script_name, "DBのオープン処理開始")
        self.conn = sqlite3.connect(db_path)
        # self._ensure_schema()

    def _ensure_schema(self):
        log.logprint(script_name, "DBのtable確認を開始")
        c = self.conn.cursor()
        c.execute(
            """
            SELECT name FROM sqlite_master WHERE type='table' AND name='videos'
            """
        )
        # self.conn.commit()
        # if cursor.fetchone() is None:
        log.logprint(script_name, f"DBのtable確認結果 {cursor.fetchone()}")
        return cursor.fetchone()

    def insert_video(self, file_id: str, title: Optional[str], author: Optional[str], publish_date: Optional[str], folder_path: str, checkin_time: str, original_filename: str, checksum: str) -> None:
        c = self.conn.cursor()
        try:
            HDD_flag = 1
            RMB_flag = 0
            c.execute(
                """
                INSERT INTO Videos(file_id, title, author, publish_date, HDD_flag, RMB_flag, checkin_time, original_filename, checksum)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (file_id, title, author, publish_date, HDD_flag, RMB_flag, checkin_time, original_filename, checksum),
            )
            
            # HDD テーブルにデータを追加
            # ただし、テーブル作成時に「FOREIGN KEY (file_id) REFERENCES Videos(file_id)」を実行済み。
            c.execute(
                """
                INSERT INTO HDD(file_id, folder_path)
                VALUES (?, ?)
                """,
                (file_id, folder_path),
            )
            self.conn.commit()
        except sqlite3.IntegrityError as e:
            log.logprint(script_name, "DB insert failed (maybe duplicate file_id): %s", level="Error")

    def select_checksum(self, str_checksum):
        c = self.conn.cursor()
        str_ret = c.execute(
            """
            SELECT *
            FROM Videos
            WHERE checksum = ?
            LIMIT 1;
            """,
            (str_checksum,)
        )
        return str_ret.fetchone()

    def close(self):
        self.conn.close()

