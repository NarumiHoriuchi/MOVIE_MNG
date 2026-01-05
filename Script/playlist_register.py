import sqlite3
import os
import subprocess
import sys
from datetime import datetime
# check_thumbnail.py を読み込む
# import check_thumbnail

#------------------------------
# 初期変数の読み込み
#------------------------------
from config.settings import VIDEO_DB_PATH, MEDIA_DIR, THUMBNAIL_DIR
# ファイル名のみ（例: my_script.py）
script_name = os.path.basename(__file__)


#------------------------------
# ログ出力
#------------------------------
import lib.log as log


# --------------------
# DB Writer (SQLite)
# --------------------
from lib.db import videosDBWriter


def get_unregistered_videos(db):
    rows = db.p_diff_v_table()
    
    for row in rows:
        # print("追加候補:", row)
        log.logprint(script_name, f"追加候補: {row}")

    return rows


def create_thumbnail(folder_path, created_at, file_name):
    print(created_at)
    dt = datetime.fromisoformat(created_at)
    year = dt.strftime('%Y')
    month = dt.strftime('%m')

    video_path = folder_path + "/" + file_name
    log.logprint(script_name, f"Thumbnail ディレクトリは、{THUMBNAIL_DIR}/{year}/{month}")
    out_dir = os.path.join(THUMBNAIL_DIR, year, month)
    os.makedirs(out_dir, exist_ok=True)

    base = os.path.basename(video_path)
    thumb_name = f"{base}.png"
    thumb_path = os.path.join(out_dir, thumb_name)
    log.logprint(script_name, f"サムネイルの作成を行います。({base})")

    # カバー画像を取り出す
    # ffmpeg -i input.mp4 -map disp:attached_pic -c copy thumbnail.png
    cmd = ["ffmpeg", "-i", video_path]
    proc = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    
    output = proc.stderr  # ffmpeg は基本的に stderr に情報を出す
    if "attached pic" in output:
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-map', 'disp:attached_pic',
            '-c', 'copy',
            thumb_path
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        log.logprint(script_name, f"カバー画像の取り出しを行いました。({thumb_path})")
    else:
    # if not os.path.exists(thumb_path):
        cmd = [
            'ffmpeg',
            '-y',
            '-ss', '00:00:10',
            '-i', video_path,
            '-frames:v', '1',
            thumb_path
        ]
        log.logprint(script_name, f"ffmpeg 実行コマンド [{cmd}]")
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        log.logprint(script_name, f"カバー画像がないため、サムネイルを生成しました。({thumb_path})")

    return thumb_path


def register_playlist():
    db = videosDBWriter(VIDEO_DB_PATH)

    videos = get_unregistered_videos(db)

    print(f"122行目：videos {videos}")

    for id, file_id, title, checkin_time, folder_path, file_name in videos:
        thumbnail = create_thumbnail(folder_path, checkin_time, file_name)
        db.playlist_insert(id, title, thumbnail)


if __name__ == '__main__':
    register_playlist()
