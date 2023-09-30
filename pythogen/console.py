from typing import Any

from rich.console import Console


err_c = Console(stderr=True)


def print_error(title: str, msg: str, invalid_data: Any) -> None:
    err_c.print(title, style="bold red")
    err_c.print(f"\n{msg}")
    if invalid_data:
        err_c.print("\nInvalid data:")
        err_c.print("-------------")
        err_c.print(invalid_data)
