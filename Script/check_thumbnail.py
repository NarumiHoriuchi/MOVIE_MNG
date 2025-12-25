import ffmpeg
import sys

def has_cover_image(video_path):
    try:
        # ffprobeを実行してメタデータを取得
        probe = ffmpeg.probe(video_path)
        
        # ストリーム情報を確認
        for stream in probe['streams']:
            # 'attached_pic' disposition（配置属性）を持つストリームを探す
            if 'disposition' in stream and stream['disposition'].get('attached_pic') == 1:
                # このストリームはカバー画像です
                return True
                
    except ffmpeg.Error as e:
        print(f"FFmpeg error: {e.stderr.decode()}")
        return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False

    # どのストリームも'attached_pic'を持っていなければ、カバー画像はありません
    return False

# 使用例
video_file = 'E:\MOVIE_MNG\media\2025\12\20\5jegi4g3ef3.mp4' # ここに動画ファイルのパスを指定してください
if has_cover_image(video_file):
    print(f"'{video_file}' にはカバー画像が埋め込まれています。")
else:
    print(f"'{video_file}' にはカバー画像が埋め込まれていません。")
