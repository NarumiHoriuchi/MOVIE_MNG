import sqlite3
import subprocess
import sys
import csv
import os
import hashlib

DB_PATH = "database/media.db"
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


def calc_checksum(filepath):
    sha256 = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    except OSError:
        return ""


def main():
    if len(sys.argv) != 3:
        print("Usage: python BD_Volume_and_File_Insert.py <drive_letter> <csv_path>")
        sys.exit(1)

    drive_letter = sys.argv[1]
    csv_path = sys.argv[2]

    # --- Volume 登録 ---
    volume_label = get_volume_label_windows(drive_letter)
    if not volume_label:
        print("ボリュームラベルを取得できませんでした")
        sys.exit(1)

    print(f"検出された Volume Label: {volume_label}")

    human_number = input("human_number（手入力）: ").strip()
    notes = input("notes（手入力・省略可）: ").strip()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO Volume (volume_label, human_number, notes, write_count)
            VALUES (?, ?, ?, ?)
        """, (volume_label, human_number, notes, WRITE_COUNT))
        conn.commit()
        volume_id = cur.lastrowid
        print(f"Volume 登録完了 (volume_id={volume_id})")

    except sqlite3.IntegrityError:
        cur.execute("""
            SELECT volume_id
            FROM Volume
            WHERE volume_label = ?
              AND human_number = ?
        """, (volume_label, human_number))
        volume_id = cur.fetchone()[0]
        print(f"既存 Volume を再利用 (volume_id={volume_id})")


    # --- File 登録 ---
    with open(csv_path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)

        inserted = 0
        skipped = 0

        for line_no, row in enumerate(reader, start=2):
            full_path = os.path.join(row["path"], row["file_name"])
            checksum = calc_checksum(full_path)

            print(f"{line_no} 実行中です。")
            try:
                cur.execute("""
                    INSERT OR IGNORE INTO File (
                        volume_id,
                        channel_name,
                        file_name,
                        upload_date,
                        path,
                        checksum,
                        owner,
                        readonly_flag,
                        encrypted_flag,
                        notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    volume_id,
                    row["channel_name"],
                    row["file_name"],
                    row["upload_date"],
                    row["path"],
                    checksum,
                    row.get("owner"),
                    1 if row.get("readonly_flag", "").upper() == "TRUE" else 0,
                    1 if row.get("encrypted_flag", "").upper() == "TRUE" else 0,
                    row.get("notes")
                ))
                
                if cur.rowcount == 0:
                    skipped += 1
                else:
                    inserted += 1

            except Exception as e:
                print(f"ERROR at CSV line {line_no}: {e} ")
                conn.rollback()
                conn.close()
                sys.exit(1)

    conn.commit()
    conn.close()

    print(f"  新規追加: {inserted}")
    print(f"  既存スキップ: {skipped}")

    print("Volume + File の登録がすべて完了しました")


if __name__ == "__main__":
    main()
