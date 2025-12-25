import sqlite3
import os
import subprocess
from datetime import datetime
# check_thumbnail.py を読み込む
import check_thumbnail


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DB_DIR = os.path.join(BASE_DIR, 'database')
THUMB_DIR = os.path.join(BASE_DIR, 'thumbnail')

VIDEOS_DB = os.path.join(DB_DIR, 'videos.db')
PLAYLIST_DB = os.path.join(DB_DIR, 'playlist.db')


def init_playlist_db():
    conn = sqlite3.connect(PLAYLIST_DB)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS playlist (
            video_id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            thumbnail TEXT NOT NULL,
            played_time TEXT NOT NULL DEFAULT '00:00:00',
            play_count INTEGER NOT NULL DEFAULT 0,
            favorite INTEGER NOT NULL DEFAULT 0
        );
    """)

    conn.commit()
    conn.close()


def get_unregistered_videos():
    vconn = sqlite3.connect(VIDEOS_DB)
    pconn = sqlite3.connect(PLAYLIST_DB)

    vcur = vconn.cursor()
    pcur = pconn.cursor()

    pcur.execute("SELECT video_id FROM playlist")
    registered_ids = {row[0] for row in pcur.fetchall()}

    vcur.execute("SELECT id, title, stored_path, checkin_time FROM videos")
    rows = [
        row for row in vcur.fetchall()
        if row[0] not in registered_ids
    ]

    vconn.close()
    pconn.close()
    return rows


def create_thumbnail(video_path, created_at):
    dt = datetime.fromisoformat(created_at)
    year = dt.strftime('%Y')
    month = dt.strftime('%m')

    out_dir = os.path.join(THUMB_DIR, year, month)
    os.makedirs(out_dir, exist_ok=True)

    base = os.path.basename(video_path)
    thumb_name = f"{base}.png"
    thumb_path = os.path.join(out_dir, thumb_name)

    CHK_thumb = check_thumbnail.has_cover_image(video_path)
    
    # カバー画像を取り出す
    # ffmpeg -i input.mp4 -map disp:attached_pic -c copy thumbnail.png
    if CHK_thumb:
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-map', 'disp:attached_pic',
            '-c', 'copy',
            thumb_path
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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

    return os.path.relpath(thumb_path, BASE_DIR)


def register_playlist():
    init_playlist_db()
    videos = get_unregistered_videos()

    conn = sqlite3.connect(PLAYLIST_DB)
    cur = conn.cursor()

    for video_id, title, filepath, created_at in videos:
        thumbnail = create_thumbnail(filepath, created_at)

        cur.execute("""
            INSERT INTO playlist (
                video_id, title, thumbnail,
                played_time, play_count, favorite
            ) VALUES (?, ?, ?, '00:00:00', 0, 0)
        """, (video_id, title, thumbnail))

    conn.commit()
    conn.close()


if __name__ == '__main__':
    register_playlist()
