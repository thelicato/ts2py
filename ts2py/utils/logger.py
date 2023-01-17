from datetime import datetime
from ts2py.utils.config import SUCCESS_C, ERROR_C, END_C


class Logger:
    verbose = False

    def __new__(cls):
        if not hasattr(cls, "instance"):
            cls.instance = super(Logger, cls).__new__(cls)
        return cls.instance

    def set_verbose(self, verbose: bool):
        self.verbose = verbose

    def info(self, msg: str) -> None:
        if self.verbose:
            now = datetime.now()
            current_time = now.strftime("%H:%M:%S")
            print(f"[{current_time}] - [LOG] - {msg}", flush=True)

    def success(self, msg: str) -> None:
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        print(f"{SUCCESS_C}[{current_time}] - [SUCCESS] - {msg}{END_C}", flush=True)

    def error(self, msg: str) -> None:
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        print(f"{ERROR_C}[{current_time}] - [ERROR] - {msg}{END_C}", flush=True)
