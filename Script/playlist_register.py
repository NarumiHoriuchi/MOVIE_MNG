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


#VIDEOS_DB = os.path.join(DB_DIR, 'videos.db')
# PLAYLIST_DB = os.path.join(DB_DIR, 'playlist.db')
# PLAYLIST_DB = os.path.join(DB_DIR, 'videos.db')


"""
def init_playlist_db():
    conn = sqlite3.connect(VIDEO_DB_PATH)
    cur = conn.cursor()

    # conn.commit()
    # conn.close()
"""


def get_unregistered_videos():
    vconn = sqlite3.connect(VIDEO_DB_PATH)
    # pconn = sqlite3.connect(PLAYLIST_DB)

    vcur = vconn.cursor()
    # DB本体は同じだが、混乱を防ぐため、あえて定義
    pcur = vconn.cursor()

    log.logprint(script_name, "playlist に登録されていない videos テーブルを抽出")
    rows = vcur.execute(
    """
        SELECT v.id, v.file_id, v.title, v.publish_date, h.folder_path
        FROM (Videos v JOIN HDD h ON v.id = h.id)
        WHERE NOT EXISTS (
            SELECT 1
            FROM Playlist p
            WHERE p.video_id = v.id
        )
    """).fetchall()

    print(rows)
    for row in rows:
        print("追加候補:", row)
        # log.logprint(script_name, f"追加候補: {row[file_id]}")

    vconn.close()
    # pconn.close()
    return rows


def create_thumbnail(video_path, created_at):
    print(created_at)
    sys.exit()
    dt = datetime.fromisoformat(created_at)
    year = dt.strftime('%Y')
    month = dt.strftime('%m')

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
        log.logprint(script_name, "カバー画像の取り出しを行いました。")
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
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        log.logprint(script_name, "カバー画像がないため、サムネイルを生成しました")

    return os.path.relpath(thumb_path, BASE_DIR)


def register_playlist():
    # init_playlist_db()
    videos = get_unregistered_videos()

    conn = sqlite3.connect(VIDEO_DB_PATH)
    cur = conn.cursor()

    for id, folder_path, file_id, title, publish_date in videos:
        thumbnail = create_thumbnail(folder_path, publish_date)
        cur.execute("""
            INSERT INTO playlist (
                video_id, title, thumbnail,
                played_time, play_count, favorite
            ) VALUES (?, ?, ?, '00:00:00', 0, 0)
        """, (id, title, thumbnail))

    conn.commit()
    conn.close()


if __name__ == '__main__':
    register_playlist()
