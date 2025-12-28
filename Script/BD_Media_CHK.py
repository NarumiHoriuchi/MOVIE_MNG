import ctypes
import string
import os

# Windowsのドライブ種別
DRIVE_TYPES = {
    0: "Unknown",
    1: "No Root Directory",
    2: "Removable Disk",
    3: "Local Disk",
    4: "Network Drive",
    5: "CD-ROM",
    6: "RAM Disk"
}

def get_cdrom_drives():
    """システム上のCD-ROMドライブを取得"""
    drives = []
    bitmask = ctypes.cdll.kernel32.GetLogicalDrives()
    for i, letter in enumerate(string.ascii_uppercase):
        if bitmask & (1 << i):
            drive = f"{letter}:\\"
            drive_type = ctypes.cdll.kernel32.GetDriveTypeW(ctypes.c_wchar_p(drive))
            if drive_type == 5:  # CD-ROM
                drives.append(drive)
    return drives

def check_media(drive):
    """ドライブにメディアがセットされているか確認"""
    try:
        volume_label = os.path.basename(os.path.normpath(drive))
        volume_label = ctypes.create_unicode_buffer(1024)
        ctypes.windll.kernel32.GetVolumeInformationW(
            ctypes.c_wchar_p(drive),
            volume_label,
            ctypes.sizeof(volume_label),
            None,
            None,
            None,
            None,
            0
        )
        return volume_label.value if volume_label.value else None
    except Exception:
        return None

def user_confirm(prompt):
    """Yes/Noの確認"""
    while True:
        ans = input(f"{prompt} (Y/N): ").strip().lower()
        if ans in ["y", "yes"]:
            return True
        elif ans in ["n", "no"]:
            return False
        else:
            print("Y または N を入力してください。")

if __name__ == "__main__":
    cdrom_drives = get_cdrom_drives()
    if not cdrom_drives:
        print("BD-R/CD-ROMドライブは検出されませんでした。")
        exit()

    for drive in cdrom_drives:
        volume_label = check_media(drive)
        if volume_label:
            print(f"ドライブ {drive} にメディアがセットされています。ボリューム名: {volume_label}")
            if user_confirm(f"このドライブを登録対象にしますか？"):
                print(f"→ {drive} を登録対象として承認しました。")
            else:
                print(f"→ {drive} は登録対象外です。")
        else:
            print(f"ドライブ {drive} は空またはアクセス不可です。")
