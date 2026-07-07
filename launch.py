"""One-click launcher for the MATH180 Diode Leakage Current Study dashboard."""

import socket
import sys
import threading
import time
import urllib.request
import webbrowser

from app import app

# macOS AirPlay Receiver often blocks port 5000 — start at 5001 on Darwin
PORT_START = 5001 if sys.platform == 'darwin' else 5000


def find_available_port(start=PORT_START, attempts=10):
    for port in range(start, start + attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(('127.0.0.1', port))
                return port
            except OSError:
                continue
    return start


PORT = find_available_port()


def run_server():
    app.run(host='127.0.0.1', port=PORT, debug=False, use_reloader=False)


def open_browser():
    url = f'http://127.0.0.1:{PORT}'
    for _ in range(5):
        try:
            with urllib.request.urlopen(url, timeout=2):
                webbrowser.open(url)
                return
        except Exception:
            time.sleep(0.5)
    webbrowser.open(url)


if __name__ == '__main__':
    url = f'http://127.0.0.1:{PORT}'
    print('=' * 60)
    print('MATH180 Diode Leakage Current Study — Dashboard')
    print('=' * 60)
    print(f'  Dashboard URL: {url}')
    if sys.platform == 'darwin':
        print('  Tip: Use 127.0.0.1 (not localhost) on macOS')
    print('=' * 60)

    threading.Thread(target=run_server, daemon=True).start()
    time.sleep(2)
    open_browser()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
