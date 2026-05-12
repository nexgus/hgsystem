"""Logger setup. Writes a per-launch file to the OS's conventional log directory."""
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

LOGGER_NAME = "hgsystem"

_current_log_file: Path | None = None


class _ExitOnCriticalHandler(logging.Handler):
    """收到 CRITICAL 層級的 log 後以 exit(1) 結束程式."""

    def __init__(self) -> None:
        super().__init__(level=logging.CRITICAL)

    def emit(self, record: logging.LogRecord) -> None:
        # 讓其他 handler 先完成輸出, 再終止程式
        logging.shutdown()
        sys.exit(1)


class PackagePathFilter(logging.Filter):
    def __init__(self) -> None:
        super().__init__()
        self.pkg_root = Path(__file__).resolve().parent

    def filter(self, record):
        try:
            record.relpath = str(
                Path(record.pathname).resolve().relative_to(self.pkg_root)
            )
        except ValueError:
            record.relpath = record.pathname
        return True


class CustomFormatter(logging.Formatter):
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    green = "\x1b[32;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    PLAIN_FMT = "%(asctime)s [%(levelname)-7.7s] %(message)s"
    DEBUG_FMT = "%(asctime)s [%(levelname)s:%(relpath)s:%(lineno)d] %(message)s"

    def __init__(self, use_color: bool = True) -> None:
        """初始化 formatter.

        Arg(s):
            use_color: 若為 False, 輸出純文字 (無 ANSI escape sequence), 適合 file handler.
        """
        super().__init__()
        if use_color:
            self._formats = {
                logging.DEBUG: self.grey + self.DEBUG_FMT + self.reset,
                logging.INFO: self.green + self.PLAIN_FMT + self.reset,
                logging.WARNING: self.yellow + self.PLAIN_FMT + self.reset,
                logging.ERROR: self.red + self.DEBUG_FMT + self.reset,
                logging.CRITICAL: self.bold_red + self.DEBUG_FMT + self.reset,
            }
        else:
            self._formats = {
                logging.DEBUG: self.DEBUG_FMT,
                logging.INFO: self.PLAIN_FMT,
                logging.WARNING: self.PLAIN_FMT,
                logging.ERROR: self.DEBUG_FMT,
                logging.CRITICAL: self.DEBUG_FMT,
            }

    def format(self, record):
        """格式化單筆 log record."""
        log_fmt = self._formats.get(record.levelno)
        formatter = logging.Formatter(log_fmt)

        return formatter.format(record)


def _default_log_dir() -> Path:
    """OS-conventional log directory.

    - Windows: ``%LOCALAPPDATA%\\hgsystem\\logs``
    - macOS:   ``~/Library/Logs/hgsystem``
    - other:   ``~/.local/state/hgsystem/logs`` (XDG_STATE_HOME fallback)
    """
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA")
        root = Path(base) if base else Path.home() / "AppData" / "Local"
        return root / "hgsystem" / "logs"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Logs" / "hgsystem"
    state = os.environ.get("XDG_STATE_HOME")
    root = Path(state) if state else Path.home() / ".local" / "state"
    return root / "hgsystem" / "logs"


def _next_log_path(log_dir: Path) -> Path:
    """決定本次啟動的 log 檔路徑.

    檔名格式為 ``YYMMDD_NNNN.log``, NNNN 為當日流水號 (從 0001 開始).
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    date_prefix = datetime.now().strftime("%y%m%d")
    max_seq = 0
    for p in log_dir.glob(f"{date_prefix}_*.log"):
        parts = p.stem.split("_")
        if len(parts) == 2 and parts[0] == date_prefix and parts[1].isdigit():
            max_seq = max(max_seq, int(parts[1]))
    return log_dir / f"{date_prefix}_{max_seq + 1:04d}.log"


def setup_logging(debug: bool = False) -> logging.Logger:
    """初始化 logging 系統: 同時掛上 console 與 file handler.

    console 層級:
    - 預設 INFO, ``--debug`` 時為 DEBUG
    file 永遠記錄 DEBUG 以上, 寫入 ``<repo_root>/logs/YYMMDD_NNNN.log``.

    Arg(s):
        debug: 若為 True, console 設為 DEBUG.

    Return(s):
        已設定的 logger.
    """
    global _current_log_file

    logger = logging.getLogger(LOGGER_NAME)
    if logger.handlers:
        return logger
    logger.setLevel(logging.DEBUG)  # 由各 handler 自行過濾層級
    logger.addFilter(PackagePathFilter())

    # console handler: pythonw.exe 無 console, sys.stderr 為 None, 跳過
    if sys.stderr is not None:
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG if debug else logging.INFO)
        ch.setFormatter(CustomFormatter())
        logger.addHandler(ch)

    # file handler
    log_path = _next_log_path(_default_log_dir())
    try:
        fh = logging.FileHandler(log_path, mode="w", encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(CustomFormatter(use_color=False))
        logger.addHandler(fh)
        _current_log_file = log_path
    except Exception as ex:
        logger.error(f"無法建立 log 檔 {log_path}: {ex}")

    # CRITICAL handler: 收到 CRITICAL 後結束程式; 排在最後以便其他 handler 先輸出
    logger.addHandler(_ExitOnCriticalHandler())

    # 捕獲所有未捕獲的 exception (Python 層)
    def _excepthook(exc_type, exc_value, exc_tb):
        if issubclass(exc_type, KeyboardInterrupt):
            if sys.stderr is not None:
                sys.__excepthook__(exc_type, exc_value, exc_tb)
            return

        logger.critical("Uncaptured exception", exc_info=(exc_type, exc_value, exc_tb))

    sys.excepthook = _excepthook

    return logger


def current_log_file() -> Path | None:
    """回傳本次啟動的記錄檔路徑."""
    return _current_log_file


def get_logger() -> logging.Logger:
    """在各模組取得 logger 的便利函式."""
    return logging.getLogger(LOGGER_NAME)
