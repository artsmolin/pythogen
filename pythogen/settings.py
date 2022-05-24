from pathlib import Path


CLIENT_TEMPLATE_NAME = "httpx.j2"

CURRENT_DIR_PATH = Path(__file__).parent.absolute()
TEMPLATES_DIR_PATH = CURRENT_DIR_PATH / Path("templates")
