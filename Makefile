clean:
	@rm -rf build dist .eggs *.egg-info
	@rm -rf .coverage coverage.xml htmlcov report.xml .tox
	@find . -type d -name '.mypy_cache' -exec rm -rf {} +
	@find . -type d -name '__pycache__' -exec rm -rf {} +
	@find . -type d -name '*pytest_cache*' -exec rm -rf {} +
	@find . -type f -name "*.py[co]" -exec rm -rf {} +

install-pre-commit:
	@pre-commit install && pre-commit install --hook-type commit-msg

format: install-pre-commit clean
	pre-commit run --all-files

clients-for-tests:
	python pythogen/entrypoint.py tests/docs/openapi.yaml tests/clients/async_client.py
	python pythogen/entrypoint.py tests/docs/openapi.yaml tests/clients/sync_client.py --sync

clients-for-examples:
	python pythogen/entrypoint.py examples/petstore/openapi.yaml examples/petstore/client_async.py
	python pythogen/entrypoint.py examples/petstore/openapi.yaml examples/petstore/client_sync.py --sync

requirements:
	pip install --upgrade pip
	poetry install --remove-untracked
	make install-pre-commit

test:
	pytest --cov=pythogen tests/ -sq

test-clients:
	docker-compose up -d --build mock_server ;\
	docker-compose up --build tests ;\
	test_status_code=$$? ;\
	# docker-compose logs mock_server;\
	docker-compose down --remove-orphans ;\
	exit $$test_status_code
