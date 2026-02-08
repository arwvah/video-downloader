from ui import launch_ui
from output_manager.history import init_db

if __name__ == "__main__":
    init_db()
    launch_ui()
