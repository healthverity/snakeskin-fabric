
inject-version:
	bin/inject-version

build: inject-version
	rm -rf dist && \
	python3 setup.py sdist bdist_wheel

upload: build
	bin/upload-pkg
