import sqlite3
import subprocess
import sys
from datetime import date

DB_PATH = "mediadb.sqlite"
WRITE_COUNT = 1

def get_volume_label_windows(drive_letter):
    """
    Windowsでボリュームラベルを取得
    """
    try:
        result = subprocess.check_output(
            ["cmd", "/c", f"vol {drive_letter}"],
            encoding="cp932",
            errors="ignore"
        )
        for line in result.splitlines():
            if "ボリューム ラベル" in line or "Volume label" in line:
                return line.split(" : ")[-1].strip()
    except Exception as e:
        print("ボリュームラベル取得失敗:", e)
    return None

def main():
    drive_letter = input("ブルーレイドライブのドライブ文字（例: D:）を入力: ").strip()

    volume_label = get_volume_label_windows(drive_letter)
    if not volume_label:
        print("ボリュームラベルを取得できませんでした")
        sys.exit(1)

    print(f"検出された Volume Label: {volume_label}")

    human_number = input("human_number（手入力）: ").strip()
    notes = input("notes（手入力・省略可）: ").strip()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO Volume (
            volume_label,
            human_number,
            notes,
            write_count
        ) VALUES (?, ?, ?, ?)
    """, (
        volume_label,
        human_number,
        notes,
        WRITE_COUNT
    ))

    conn.commit()
    conn.close()

    print("Volume テーブルへ登録しました")

if __name__ == "__main__":
    main()
