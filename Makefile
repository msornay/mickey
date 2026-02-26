.PHONY: test deploy

test:
	docker build -f Dockerfile.test -t mickey-test . && docker run --rm mickey-test

deploy:
	@echo "mickey is a local CLI tool — no remote deployment configured."
