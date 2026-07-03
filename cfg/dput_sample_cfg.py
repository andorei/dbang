import os
import sys

from sources import sources


# See details on config file's and spec parameters in doc/dput.md

DEBUGGING = True
LOGGING = True
PARALLEL_WORKERS = 2

IN_DIR = os.path.join(os.path.dirname(__file__), '..', 'in')
LOG_DIR = os.path.join(os.path.dirname(__file__), '..', 'log')

#ENCODING = 'UTF-8'
#CSV_DIALECT = 'excel'
#CSV_DELIMITER = ';'

SOURCE = "<source_one>"
#PRESERVE_N_LOADS = 10

specs = {
    "<descriptive spec name>": {
        #"tags": ['<example>'],

        "file": "<example.csv>",
        #"args": [],
        #"force": False,
        #"encoding": ENCODING,
        #"csv_dialect": CSV_DIALECT,
        #"csv_delimiter": CSV_DELIMITER,
        #"skip_lines": 0,
        #"text_lines": False,

        #"source": SOURCE,
        #"setup": [],
        #"insert_data": lambda row: (row[2], row[3]),
        #"insert_actions": "insert into <table_name> (code, name) values (?, ?)",
        #"validate_actions": [],
        #"process_actions": [],
        #"upset": [],

        #"preserve_n_loads": PRESERVE_N_LOADS
    },
}
