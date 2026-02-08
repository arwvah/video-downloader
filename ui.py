import tkinter as tk
from tkinter import filedialog, ttk
from threading import Thread
from queue import Queue
import io
import urllib.request
from PIL import Image, ImageTk
from downloader_engine.downloader import download_video
from downloader_engine.metadata import get_video_info
from effects_layer.progress_bar import parse_progress
from output_manager.history import (
    log_download,
    get_last_week_downloads,
    get_downloads_per_day,
    get_downloads_by_quality
)
import os
import sys
import subprocess



download_queue = Queue()
is_downloading = False
download_folder = None


def open_file(path):
    try:
        if sys.platform.startswith("win"):
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.call(["open", path])
        else:
            subprocess.call(["xdg-open", path])
    except Exception as e:
        print("Failed to open file:", e)



def launch_ui():
    global is_downloading, download_folder


    root = tk.Tk()

    root.title("Video Downloader")
    root.geometry("700x500")

    # ---- ROOT GRID ----
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    main = tk.Frame(root)
    main.grid(row=0, column=0, sticky="nsew")

    main.columnconfigure(0, weight=1)
    main.rowconfigure(0, weight=3)
    main.rowconfigure(1, weight=0)
    main.rowconfigure(2, weight=0)
    main.rowconfigure(3, weight=0)
    main.rowconfigure(4, weight=0)
    main.rowconfigure(5, weight=0)
    main.rowconfigure(6, weight=0)


    # ---- THUMBNAIL ----
    thumb_label = tk.Label(main, bg="black")
    thumb_label.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

    current_thumb = {"img": None, "original": None}

    def resize_thumbnail(event):
        if not current_thumb["original"]:
            return

        w = event.width
        h = int(w * 9 / 16)

        if h > event.height:
            h = event.height
            w = int(h * 16 / 9)

        img = current_thumb["original"].resize((w, h))
        photo = ImageTk.PhotoImage(img)
        current_thumb["img"] = photo
        thumb_label.config(image=photo)

    thumb_label.bind("<Configure>", resize_thumbnail)


    # ---- URL BOX ----
    url_box = tk.Text(main, height=4)
    url_box.grid(row=1, column=0, sticky="ew", padx=10)


    # ---- QUALITY ----
    quality_var = tk.StringVar(value="best")
    quality_frame = tk.Frame(main)
    quality_frame.grid(row=2, column=0, pady=5)

    for label, val in [
        ("Best", "best"),
        ("1080p", "1080p"),
        ("720p", "720p"),
        ("Audio only", "audio"),
    ]:
        tk.Radiobutton(
            quality_frame,
            text=label,
            variable=quality_var,
            value=val
        ).pack(side="left", padx=5)

    # ---- PROGRESS ----
    progress_var = tk.DoubleVar(value=0)
    progress_bar = ttk.Progressbar(
        main,
        variable=progress_var,
        maximum=100
    )
    progress_bar.grid(row=3, column=0, sticky="ew", padx=10, pady=5)

    status_label = tk.Label(main, text="Idle")
    status_label.grid(row=4, column=0)

    # ---- THUMBNAIL LOADER ----
    def load_thumbnail(url):
        try:
            info = get_video_info(url)
            thumb_url = info.get("thumbnail")
            if not thumb_url:
                return

            with urllib.request.urlopen(thumb_url) as u:
                raw = u.read()

            img = Image.open(io.BytesIO(raw))
            current_thumb["original"] = img

            resize_thumbnail(type("e", (), {
                "width": thumb_label.winfo_width(),
                "height": thumb_label.winfo_height()
            })())

        except Exception:
            current_thumb["original"] = None
            thumb_label.config(image="")

    def preview_first_url(event=None):
        content = url_box.get("1.0", tk.END).strip()
        if not content:
            thumb_label.config(image="")
            return

        first = content.splitlines()[0].strip()
        if first.startswith("http"):
            Thread(
                target=load_thumbnail,
                args=(first,),
                daemon=True
            ).start()

    url_box.bind("<KeyRelease>", preview_first_url)

    # ---- PROGRESS CALLBACK ----
    def update_ui(percent, text):
        progress_var.set(percent)
        status_label.config(text=text)

    def progress_hook(data):
        parsed = parse_progress(data)
        if parsed:
            percent, speed, eta = parsed
            root.after(
                0,
                update_ui,
                percent,
                f"{percent:.1f}% | {speed} | ETA {eta}"
            )

    # ---- QUEUE WORKER ----
    def process_queue():
        global is_downloading
        is_downloading = True

        while not download_queue.empty():
            url = download_queue.get()

            root.after(
                0,
                status_label.config,
                {"text": f"Downloading:\n{url}"}
            )

            info = download_video(
                url,
                download_folder,
                progress_hook,
                quality_var.get()
            )

            if info:
                log_download(
                    url=url,
                    title=info.get("title"),
                    file_path=info.get("filename"),
                    quality=quality_var.get()
                )

            root.after(0, progress_var.set, 0)

        root.after(
            0,
            status_label.config,
            {"text": "All downloads finished"}
        )
        is_downloading = False




    def show_stats():
        win = tk.Toplevel(root)
        win.title("Download Stats")
        win.geometry("600x400")

        canvas = tk.Canvas(win, bg="white")
        canvas.pack(expand=True, fill="both")

    # ---- DATA ----
        per_day = get_downloads_per_day()
        by_quality = get_downloads_by_quality()

    # ---- DRAW: Downloads per day ----
        canvas.create_text(300, 20, text="Downloads (Last 7 Days)", font=("Arial", 12, "bold"))

        if per_day:
            max_count = max(c for _, c in per_day)
            bar_width = 40
            start_x = 50
            base_y = 180

            for i, (day, count) in enumerate(per_day):
                height = int((count / max_count) * 100) if max_count else 0
                x = start_x + i * (bar_width + 10)

                canvas.create_rectangle(
                    x, base_y - height,
                    x + bar_width, base_y,
                    fill="#4a90e2"
                )
                canvas.create_text(x + bar_width / 2, base_y + 10, text=day[-2:])
                canvas.create_text(x + bar_width / 2, base_y - height - 10, text=str(count))
        else:
            canvas.create_text(300, 100, text="No data yet")

    # ---- DRAW: Quality breakdown ----
        canvas.create_text(300, 230, text="Downloads by Quality", font=("Arial", 12, "bold"))

        y = 260
        total = sum(c for _, c in by_quality) or 1

        for quality, count in by_quality:
            percent = int((count / total) * 100)
            canvas.create_text(150, y, anchor="w", text=f"{quality}")
            canvas.create_rectangle(250, y - 8, 250 + percent * 2, y + 8, fill="#7ed321")
            canvas.create_text(260 + percent * 2, y, anchor="w", text=f"{count}")
            y += 30


    # ---- HISTORY WINDOW ----
    def show_last_week():
        records = get_last_week_downloads()
        win = tk.Toplevel(root)
        win.title("Downloads – Last 7 Days")
        win.geometry("700x400")
        frame = tk.Frame(win)
        frame.pack(expand=True, fill="both")

        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side="right", fill="y")

        listbox = tk.Listbox(
            frame,
            yscrollcommand=scrollbar.set
        )
        listbox.pack(expand=True, fill="both")
        scrollbar.config(command=listbox.yview)

        paths = []

        if not records:
            listbox.insert(tk.END, "No downloads in the last 7 days.")
            return
        for title, path, quality, time in records:
            listbox.insert(
                tk.END,
                f"{time} | {quality} | {title}"
            )
            paths.append(path)

        def on_open(event):
            sel = listbox.curselection()
            if not sel:
                return
            idx = sel[0]
            file_path = paths[idx]
            open_file(file_path)

        listbox.bind("<Double-Button-1>", on_open)

    # ---- START ----
    def start_download():
        global download_folder

        urls = [
            u.strip()
            for u in url_box.get("1.0", tk.END).splitlines()
            if u.strip()
        ]

        if not urls:
            status_label.config(text="Paste URLs first")
            return

        download_folder = filedialog.askdirectory()
        if not download_folder:
            return

        for u in urls:
            download_queue.put(u)

        status_label.config(text=f"Queued {len(urls)} videos")

        if not is_downloading:
            Thread(target=process_queue, daemon=True).start()

    tk.Button(
        main,
        text="Download",
        command=start_download
    ).grid(row=5, column=0, pady=10)

    tk.Button(
        main,
        text="Last 7 Days",
        command=show_last_week
    ).grid(row=6, column=0, pady=5)

    tk.Button(
        main,
        text="Stats",
        command=show_stats
    ).grid(row=7, column=0, pady=5)



    root.mainloop()
