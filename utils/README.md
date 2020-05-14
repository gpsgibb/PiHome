# Logging

This directory contains code for logging data. The original (and deprecated) implementation in `logger.py` logs this data to plain text files.

The new implementation writes the logs to a sqlite database. This is achieved using the PonyORM, which is an Object Relational Mapper which allows me to access SQL databases through python. The file `db.py` defines the mapping of the database schema to python, and `logs.py` contains all the logging functionality.

With this new implementation I can register new data types to be recorded, record data, generate statistics from these data, and access the data.

Also included for completeness is `migrate.py`, which migrates the old logfiles to the database.