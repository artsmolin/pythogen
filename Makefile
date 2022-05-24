install-pre-commit:
	@pre-commit install && pre-commit install --hook-type commit-msg

format: install-pre-commit
	pre-commit run --all-files

clients-for-tests:
	python pythogen/entrypoint.py tests/docs/openapi.yaml tests/clients/async_client.py
	python pythogen/entrypoint.py tests/docs/openapi.yaml tests/clients/sync_client.py --sync

requirements:
	pip install --upgrade pip
	poetry install --remove-untracked
	make install-pre-commit

test:
	pytest

test-clients:
	docker-compose up -d --build mock_server ;\
	docker-compose up --build tests ;\
	test_status_code=$$? ;\
	# docker-compose logs mock_server;\
	docker-compose down --remove-orphans ;\
	exit $$test_status_code
