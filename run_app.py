"""Startpunkt der Desktop-Anwendung (pywebview)."""

from __future__ import annotations

import os
import sys

# WebView2: GPU aus, sonst friert das Fenster auf manchen Rechnern ein.
os.environ.setdefault(
    "WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS",
    "--disable-gpu --force-device-scale-factor=1 --high-dpi-support=1",
)

import webview

# pywebview: Downloads standardmäßig deaktiviert.
webview.settings["ALLOW_DOWNLOADS"] = True

from app.server import start_server


def _gui_backend() -> str | None:
    """Windows: Edge/WebView2. macOS/Linux: Standard-Engine (Cocoa/GTK)."""
    if sys.platform.startswith("win"):
        return "edgechromium"
    return None


def main() -> None:
    _server, port = start_server()
    window = webview.create_window(
        "SmartAssign",
        f"http://127.0.0.1:{port}/",
        width=1440,
        height=900,
        min_size=(1024, 700),
        maximized=True,
    )

    def _lock_zoom(window):  # noqa: ARG001 – pywebview übergibt das Fenster
        # Nach jedem Laden Zoom auf 100 % setzen (falls die Engine etwas anderes will).
        try:
            window.evaluate_js(
                "try { document.body.style.zoom = '100%'; "
                "document.documentElement.style.zoom = '1'; } catch (e) {}"
            )
        except Exception:
            pass

    window.events.loaded += _lock_zoom

    gui = _gui_backend()
    if gui:
        webview.start(gui=gui)
    else:
        webview.start()


if __name__ == "__main__":
    main()
