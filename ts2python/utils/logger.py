from datetime import datetime
from ts2python.utils.config import SUCCESS_C, ERROR_C, END_C


def info(msg: str) -> None:
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    print(f"[{current_time}] - [LOG] - {msg}", flush=True)


def success(msg: str) -> None:
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    print(f"{SUCCESS_C}[{current_time}] - [SUCCESS] - {msg}{END_C}", flush=True)


def error(msg: str) -> None:
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    print(f"{ERROR_C}[{current_time}] - [ERROR] - {msg}{END_C}", flush=True)
