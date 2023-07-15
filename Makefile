.PHONY: tests

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

clients:
	# async clients for tests
	python pythogen/entrypoint.py tests/docs/openapi.yaml tests/clients/async_client.py
	python pythogen/entrypoint.py tests/docs/openapi.yaml tests/clients/async_client_with_metrics.py --metrics
	python pythogen/entrypoint.py tests/docs/openapi.yaml tests/clients/async_client_with_headers.py --headers X-API-KEY,X-API-SECRET

	# sync clients for tests
	python pythogen/entrypoint.py tests/docs/openapi.yaml tests/clients/sync_client.py --sync
	python pythogen/entrypoint.py tests/docs/openapi.yaml tests/clients/sync_client_with_metrics.py --sync --metrics

	# clients for examles
	python pythogen/entrypoint.py examples/petstore/openapi.yaml examples/petstore/client_async.py
	python pythogen/entrypoint.py examples/petstore/openapi.yaml examples/petstore/client_sync.py --sync

requirements:
	pip install --upgrade pip
	poetry install --remove-untracked
	make install-pre-commit

tests:
	docker-compose up -d --build mock_server && \
	pytest --cov=pythogen tests/ -sq -v
