POETRY = poetry run

.PHONY: test

lint:
	$(POETRY) pylint statusline
	#PYLINTRC=test/pylintrc $(POETRY) pylint test
	$(POETRY) mypy statusline test

test:
	$(POETRY) pytest --cov=statusline
