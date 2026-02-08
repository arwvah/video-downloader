import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path("downloads.db")


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS downloads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT,
                title TEXT,
                file_path TEXT,
                quality TEXT,
                downloaded_at TEXT
            )
        """)


def log_download(url, title, file_path, quality):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            INSERT INTO downloads (url, title, file_path, quality, downloaded_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            url,
            title,
            file_path,
            quality,
            datetime.now().isoformat()
        ))


def get_last_week_downloads():
    since = (datetime.now() - timedelta(days=7)).isoformat()

    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute("""
            SELECT title, file_path, quality, downloaded_at
            FROM downloads
            WHERE downloaded_at >= ?
            ORDER BY downloaded_at DESC
        """, (since,))
        return cur.fetchall()


def get_downloads_per_day(days=7):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute("""
            SELECT substr(downloaded_at, 1, 10) AS day, COUNT(*)
            FROM downloads
            WHERE downloaded_at >= datetime('now', ?)
            GROUP BY day
            ORDER BY day
        """, (f'-{days} days',))
        return cur.fetchall()


def get_downloads_by_quality():
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute("""
            SELECT quality, COUNT(*)
            FROM downloads
            GROUP BY quality
        """)
        return cur.fetchall()

