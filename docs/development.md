# Development
- Activate environment
  ```shell
  rm -rf .venv || true
  python3 -m venv .venv
  source .venv/bin/activate
  make requirements
  ```
- Make changes
- Execute `make clients-for-tests && make test-clients`
- Execute `make clients-for-examples`
