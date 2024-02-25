import sys
from typing import Any


FMT = "\033"
RESET = "\033[0m"

FG_BLACK = "\033[30m"
FG_RED = "\033[31m"
FG_GREEN = "\033[32m"
FG_YELLOW = "\033[33m"
FG_BLUE = "\033[34m"
FG_PURPLE = "\033[35m"
FG_CYAN = "\033[36m"
FG_WHITE = "\033[37m"

BG_BLACK = "\033[40m"
BG_RED = "\033[41m"
BG_GREEN = "\033[42m"
BG_YELLOW = "\033[43m"
BG_BLUE = "\033[44m"
BG_PURPLE = "\033[45m"
BG_CYAN = "\033[46m"
BG_WHITE = "\033[47m"

STYLE_BOLD = "\033[1m"
STYLE_UNDERLINE = "\033[4m"


def print_error(title: str, msg: str, invalid_data: Any) -> None:
    print(f"{FMT}{STYLE_BOLD}{BG_RED}{FG_WHITE} {title} {RESET}", file=sys.stderr)
    print(f"\n{msg}", file=sys.stderr)
    if invalid_data:
        print(f"\n{FMT}{STYLE_UNDERLINE}Invalid data:{RESET}", file=sys.stderr)
        print(invalid_data, file=sys.stderr)
