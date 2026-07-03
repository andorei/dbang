import os
import sys


# See details on config file's and spec parameters in doc/dfifo.md

DEBUGGING = True
LOGGING = True
PARALLEL_WORKERS = 2

IN_DIR = os.path.join(os.path.dirname(__file__), '..', 'in')
OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'out')
LOG_DIR = os.path.join(os.path.dirname(__file__), '..', 'log')

#ENCODING = 'UTF-8'
#CSV_DIALECT = 'excel'
#CSV_DELIMITER = ';'

# defaults to ISO 86101; use '%c' to align with locale
#DATETIME_FORMAT = '%c'
# defaults to ISO 86101; use '%x' to align with locale
#DATE_FORMAT = '%x'

specs = {
    "<descriptive spec name>": {
        #"tags": ['<example>'],
        "fi": {
            "file": "example.csv",
            #"force": False,
            #"skip_lines": 0,
            #"skip_bad_files": False,
            #"encoding": ENCODING,
            #"csv_dialect": CSV_DIALECT,
            #"csv_delimiter": CSV_DELIMITER,
            #"text_lines": False,
            #"transformer": lambda row: (row[3], row[0]) if row[3] else None
        },
        "fo": {
            "file": "example.html",
            #"rows_per_file": 0,
            #"header": [],
            #"text_lines": False,
            #"csv.encoding": ENCODING,
            #"csv.dialect": CSV_DIALECT,
            #"csv.delimiter": CSV_DELIMITER,
            #"csv.dec_separator": '.',
            #"json.encoding": ENCODING,
            #"json.template": "dfifo_sample_out.json.jinja",
            #"html.encoding": ENCODING,
            #"html.dec_separator": '.',
            #"html.title": "Example HTML formatted data",
            #"html.template": "dfifo_sample_out.html.jinja",
        }
    }
}
