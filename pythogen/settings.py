from pathlib import Path


CLIENT_TEMPLATE_NAME = "main.j2"

CURRENT_DIR_PATH = Path(__file__).parent.absolute()
HTTP_CLIENT_TEMPLATES_DIR_PATH = CURRENT_DIR_PATH / Path("templates/http_client")
HTTP_PACKAGE_TEMPLATES_DIR_PATH = CURRENT_DIR_PATH / Path("templates/http_client_package")
