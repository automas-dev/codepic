
setup:
	poetry install

build: setup
	poetry build

install: build
	/usr/bin/python3 -m pip install dist/$$(ls dist | grep .whl | tail -n 1)

checks: lint test

lint:
	poetry run ruff check .

format:
	poetry run ruff check --fix .

test:
	poetry run pytest tests

.PHONY: setup build install checks lint format test
