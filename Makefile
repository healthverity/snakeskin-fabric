# Snakeskin targets

generate-crypto:
	bin/crypt-generate

run-tests:
	pytest

watch-tests:
	pytest-watch

lint:
	pylint-fail-under --fail_under 9.9 snakeskin

typecheck:
	mypy snakeskin && echo 'Type check passed'

ci: run-tests lint typecheck

inject-version:
	bin/inject-version

build: inject-version
	rm -rf dist && \
	python3 setup.py sdist bdist_wheel

tag:
	bin/tag

upload: build tags
	bin/upload-pkg
