.PHONY: doc test
doc:
	pydoc-markdown > docs/configurations.md
	python ./bibli_ls/cli.py --default-config > docs/default-config.toml

test:
	pip install . && python3 -m pytest
