coverage run --omit */venv/*,*/tests/* -m unittest discover
coverage xml
coverage html
