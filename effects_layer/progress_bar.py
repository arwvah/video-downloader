def parse_progress(data):
    status = data.get("status")

    if status == "downloading":
        total = data.get("total_bytes") or data.get("total_bytes_estimate")
        downloaded = data.get("downloaded_bytes", 0)

        if total:
            percent = downloaded / total * 100
            speed = data.get("_speed_str", "")
            eta = data.get("_eta_str", "")
            return percent, speed, eta

    elif status == "finished":
        return 100, "processing", "0s"

    return None
