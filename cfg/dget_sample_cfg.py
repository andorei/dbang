import os
import sys

from sources import sources


# See details on config file's and spec parameters in doc/dget.md

DEBUGGING = True
LOGGING = True
PARALLEL_WORKERS = 2

OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'out')
LOG_DIR = os.path.join(os.path.dirname(__file__), '..', 'log')

#ENCODING = 'UTF-8'
#CSV_DIALECT = 'excel'
#CSV_DELIMITER = ';'

# defaults to ISO 86101; use '%c' to align with locale
#DATETIME_FORMAT = '%c'
# defaults to ISO 86101; use '%x' to align with locale
#DATE_FORMAT = '%x'

SOURCE = "<source_one>"
#PRESERVE_N_TRACES = 10

specs = {
    "<descriptive spec name>": {
        #"tags": ["example"],
        #"source": SOURCE,
        #"setup": [],
        "query": "select 'hello' hello, 'world' world",
        #"bind_args": {},
        "file": "example.html"
        #"rows_per_file": 100
        #"header": []
        #"csv.encoding": ENCODING,
        #"csv.dialect": CSV_DIALECT,
        #"csv.delimiter": CSV_DELIMITER,
        #"csv.dec_separator": '.',
        #"json.encoding": ENCODING,
        #"json.template": "dget_sample_out.json.jinja"
        #"html.encoding": ENCODING,
        #"html.dec_separator": '.',
        #"html.title": "<descriptive HTML title>",
        #"html.template": "dget_sample_out.html.jinja",
        #"upset": []
    }
}
