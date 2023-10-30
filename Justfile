help:
    just --list


install:
    poetry install --sync --no-interaction --no-root
    poetry run pre-commit install


format:
    poetry run pre-commit run --all

prepare-config config_name="gtp_config.cfg":
    katago genconfig -output {{config_name}}
