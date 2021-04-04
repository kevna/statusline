POETRY := poetry run

.PHONY: test

lint:
	$(POETRY) pylint statusline
	cd test && $(POETRY) pylint test
	$(POETRY) mypy statusline test

REPORT := term-missing:skip-covered
test:
	$(POETRY) pytest --cov=statusline --cov-report=$(REPORT)
