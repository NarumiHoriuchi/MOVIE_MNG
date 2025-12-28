import os
import sys
import csv
from datetime import datetime
import sys
import io

# Windows stdout を UTF-8 に強制
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", newline="")

def main():
    if len(sys.argv) != 2:
        print("Usage: python scan_mp4_to_csv.py <root_path>", file=sys.stderr)
        sys.exit(1)

    root_path = sys.argv[1]

    writer = csv.writer(sys.stdout, lineterminator="\n")
    # CSVヘッダー
    writer.writerow(["path", "file_name", "upload_date"])

    for dirpath, dirnames, filenames in os.walk(root_path):
        for filename in filenames:
            if filename.lower().endswith(".mp4"):
                full_path = os.path.join(dirpath, filename)

                try:
                    ctime = os.path.getctime(full_path)
                    upload_date = datetime.fromtimestamp(ctime).strftime("%Y-%m-%d")
                except OSError:
                    # 取得失敗時は空欄（後で人間が補正）
                    upload_date = ""

                writer.writerow([
                    dirpath,
                    filename,
                    upload_date
                ])

if __name__ == "__main__":
    main()
