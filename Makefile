
inject-version:
	bin/inject-version

build: inject-version
	rm -rf dist && \
	python3 setup.py sdist bdist_wheel

tag:
	bin/tag

upload: build tags
	bin/upload-pkg
