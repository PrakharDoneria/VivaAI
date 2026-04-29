.PHONY: install dev test lint

install:
	python -m pip install -r requirements.txt

dev:
	python app.py

test:
	python -m unittest discover -s tests -p 'test_*.py'

lint:
	python -m py_compile app.py config.py routes/*.py models/*.py utils/*.py webrtc/*.py ai/*.py
