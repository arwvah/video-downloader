from yt_dlp import YoutubeDL


def download_video(url, output_path, progress_callback=None, quality="best"):
    result = {}

    def hook(d):
        if progress_callback:
            progress_callback(d)
        if d.get("status") == "finished":
            result["filename"] = d.get("filename")

    postprocessors = []

    if quality == "best":
        format_opt = "bv*+ba/b"
    elif quality == "1080p":
        format_opt = "bv*[height<=1080]+ba/b"
    elif quality == "720p":
        format_opt = "bv*[height<=720]+ba/b"
    elif quality == "audio":
        format_opt = "ba/b"
        postprocessors = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }]
    else:
        format_opt = "bv*+ba/b"

    ydl_opts = {
        "outtmpl": f"{output_path}/%(title)s.%(ext)s",
        "format": format_opt,
        "merge_output_format": "mkv",  # <-- THIS IS THE FIX
        "prefer_ffmpeg": True,
        "postprocessors": postprocessors,
        "progress_hooks": [hook],
        "noplaylist": True,
        "quiet": False,
    }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        result["title"] = info.get("title")

    return result
