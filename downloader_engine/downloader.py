from yt_dlp import YoutubeDL


def download_video(url, output_path, progress_callback=None, quality="best"):
    result = {}

    def hook(d):
        if progress_callback:
            progress_callback(d)

        if d.get("status") == "finished":
            result["filename"] = d.get("filename")

    # ---- QUALITY HANDLING ----
    if quality == "best":
        format_opt = "bestvideo+bestaudio/best"
        postprocessors = []

    elif quality == "1080p":
        format_opt = "bestvideo[height<=1080]+bestaudio/best"
        postprocessors = []

    elif quality == "720p":
        format_opt = "bestvideo[height<=720]+bestaudio/best"
        postprocessors = []

    elif quality == "audio":
        format_opt = "bestaudio/best"
        postprocessors = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }]

    else:
        format_opt = "bestvideo+bestaudio/best"
        postprocessors = []

    # ---- YT-DLP OPTIONS ----
    ydl_opts = {
        "outtmpl": f"{output_path}/%(title)s.%(ext)s",
        "format": format_opt,
        "merge_output_format": "mp4",
        "progress_hooks": [hook],
        "postprocessors": postprocessors,
        "noplaylist": True,
        "quiet": False,
    }

    # ---- DOWNLOAD ----
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        result["title"] = info.get("title")

    return result
