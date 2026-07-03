import os
import sys

#
# Run
#     dfifo.py --fi test.csv --fo dfifo_dummy_csv.xlsx test/dfifo_dummy
# or
#     dfifo.py --fi test.xlsx --fo dfifo_dummy_xlsx.csv test/dfifo_dummy
# and find output file in subdirectory out.
#

#
# SETTINGS USED BY fifo
#
# defaults to False
DEBUGGING = True
# defaults to False
LOGGING = True
# defaults to 1
#PARALLEL_WORKERS = 2

# defaults to current working directory
IN_DIR = os.path.join(os.path.dirname(__file__), '..', 'in')
OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'out')
LOG_DIR = os.path.join(os.path.dirname(__file__), '..', 'log')

# input and output files' encoding defaults to OS locale encoding
ENCODING = 'UTF-8'
# defaults to ISO 86101; use '%c' to align with locale
#DATETIME_FORMAT = '%c'
# defaults to ISO 86101; use '%x' to align with locale
#DATE_FORMAT = '%x'
# defaults to 'excel'
CSV_DIALECT = 'excel'
# defaults to the dialect delimiter
CSV_DELIMITER = ';'


specs = {
    "dummy": {"fi": {"force": True}, "fo": {}},
}
