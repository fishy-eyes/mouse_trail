"""Application entry point for the mouse trail tool."""

import ctypes
import os
import sys
import threading
import tkinter as tk

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from control_panel import ControlPanel
from overlay_window import OverlayWindow
from trail_engine import TrailEngine


def _set_dpi_awareness():
    """Keep pynput coordinates aligned with tkinter on scaled displays."""
    if sys.platform != "win32":
        return

    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def mouse_listener(overlay):
    """Listen for global mouse movement and forward positions to the overlay."""
    from pynput.mouse import Listener

    def on_move(x, y):
        overlay.enqueue_position(x, y)

    with Listener(on_move=on_move) as listener:
        listener.join()


def _safe_print(message):
    """Print safely when a Windows terminal cannot encode Unicode text."""
    try:
        print(message)
    except UnicodeEncodeError:
        print(message.encode("gbk", errors="replace").decode("gbk", errors="replace"))


def main():
    _set_dpi_awareness()

    _safe_print("=" * 50)
    _safe_print("  Mouse Trail")
    _safe_print("  Move the mouse to see the trail effect.")
    _safe_print("=" * 50)

    engine = TrailEngine()
    user_cfg = config.load_config()
    preset_name = user_cfg.get("active_preset", config.DEFAULT_CONFIG["active_preset"])
    preset = config.get_preset(preset_name)
    engine.set_config(preset)
    engine.enabled = user_cfg.get("enabled", True)

    _safe_print(f"[INFO] Active preset: {preset_name}")
    _safe_print(f"[INFO] Trail enabled: {engine.enabled}")

    root = tk.Tk()
    root.withdraw()

    overlay = OverlayWindow(root, engine)
    panel = ControlPanel(root, engine, overlay)

    overlay.start()

    listener_thread = threading.Thread(
        target=mouse_listener,
        args=(overlay,),
        daemon=True,
        name="MouseListener",
    )
    listener_thread.start()

    try:
        root.mainloop()
    except KeyboardInterrupt:
        _safe_print("[INFO] Interrupted by user.")
    finally:
        _safe_print("[INFO] Exiting.")
        overlay.stop()
        try:
            root.destroy()
        except Exception:
            pass
        os._exit(0)


if __name__ == "__main__":
    main()
