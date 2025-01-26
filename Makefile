.PHONY: doc test
doc:
	pydoc-markdown > docs/configurations.md
	uv run bibli_ls --default-config > docs/default-config.toml

test:
	pip install . && python3 -m pytest
