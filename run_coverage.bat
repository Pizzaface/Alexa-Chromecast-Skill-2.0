cd src
rem coverage run --omit */venv/*,*/tests/* -m unittest discover tests
coverage run --omit */venv/*,*/tests/* -m unittest discover tests.integration
coverage xml
coverage html
cd ..
