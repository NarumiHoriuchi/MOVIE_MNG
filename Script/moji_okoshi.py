import cv2
import pytesseract
from pathlib import Path

# フォルダ定義
SNAPSHOT_DIR = Path("snapshot")
MONO_DIR = Path("monoqlo")
TEXT_DIR = Path("srt-text")

MONO_DIR.mkdir(exist_ok=True)
TEXT_DIR.mkdir(exist_ok=True)

# OCR設定（日本語）
TESSERACT_LANG = "jpn"

def to_monochrome(src_path: Path, dst_path: Path):
    img = cv2.imread(str(src_path))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 2値化（Otsu）
    _, binary = cv2.threshold(
        gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    cv2.imwrite(str(dst_path), binary)

def ocr_image(img_path: Path) -> str:
    img = cv2.imread(str(img_path))
    text = pytesseract.image_to_string(img, lang=TESSERACT_LANG)
    return text.strip()

def main():
    for png in sorted(SNAPSHOT_DIR.glob("*.png")):
        mono_path = MONO_DIR / png.name
        text_path = TEXT_DIR / (png.stem + ".txt")

        print(f"Processing: {png.name}")

        # 1. モノクロ化
        to_monochrome(png, mono_path)

        # 2. OCR
        text = ocr_image(mono_path)

        # 3. 保存
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(text)

if __name__ == "__main__":
    main()
