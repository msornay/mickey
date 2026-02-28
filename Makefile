.PHONY: test lint deploy

test: lint
	docker build -f Dockerfile.test -t mickey-test . && docker run --rm mickey-test

lint:
	ruff check mickey
	ruff format --check mickey

deploy:
	@echo "mickey is a local CLI tool — no remote deployment configured."
