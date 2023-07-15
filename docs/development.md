# Development
- Activate environment
  ```shell
  rm -rf .venv || true
  python3 -m venv .venv
  source .venv/bin/activate
  make requirements
  ```
- Make your changes
- Execute `make clients`
- Execute `make tests`
