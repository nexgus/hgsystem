"""Entry point: ``python -m hgsys [-H host] [-p port] [-T]``."""

import argparse

from pymongo import MongoClient
from PySide6.QtWidgets import QApplication

from .log import setup_logging
from .version import VER_STRING
from .viewmodels.main import MainViewModel
from .views.main_window import MainWindow


def main() -> None:
    """應用程式進入點: 解析 CLI 旗標, 建立 Qt app / Mongo / VM / 主視窗並啟動事件迴圈."""
    parser = argparse.ArgumentParser(
        description="HG System",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--version", action="version", version=f"HG System {VER_STRING}"
    )
    parser.add_argument(
        "-H", "--host", default="localhost", help="MongoDB host address."
    )
    parser.add_argument(
        "-p", "--port", type=int, default=27017, help="MongoDB port number."
    )
    parser.add_argument(
        "-T", "--test", action="store_true", help="Test mode (auto-restart on Update)."
    )
    parser.add_argument(
        "-d", "--debug", action="store_true", help="Enable DEBUG-level console output."
    )
    args = parser.parse_args()

    setup_logging(debug=args.debug)

    app = QApplication([])
    mongo = MongoClient(args.host, args.port)
    vm = MainViewModel(mongo)
    window = MainWindow(vm, test_mode=args.test)
    window.showMaximized()
    window.show()
    try:
        app.exec()
    finally:
        mongo.close()


if __name__ == "__main__":
    main()
