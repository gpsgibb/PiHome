# Utilities

This directory contains utilities. At present these are reading from a config file and logging.

## Config files

Codes are able to load configuration from a top level `config.yaml` config file using the `GetConfig` function in `GetConfig.py`. This returns the contents of `config.yaml` as a dictionary. The optional `key` parameter passed to it allows you to select a certain entry from config dictionary (e.g. config for a specific component).

## Logging

The new implementation writes the logs to a sqlite database. This is achieved using the PonyORM, which is an Object Relational Mapper which allows me to access SQL databases through python. The file `db.py` defines the mapping of the database schema to python, and `logger.py` contains all the logging functionality.

With this new implementation I can register new data types to be recorded, record data, generate statistics from these data, and access the data.

Also included for completeness is `migrate.py`, which migrates the old plain text logfiles I used to use for logging to the database.