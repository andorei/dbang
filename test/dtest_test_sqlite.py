import os
import sys

from sources import sources


# See details on config file's and spec parameters in doc/dtest.md

DEBUGGING = True
LOGGING = True
PARALLEL_WORKERS = 2

OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'out')
LOG_DIR = os.path.join(os.path.dirname(__file__), '..', 'log')

RUN_REPORT_TEMPLATE = 'dtest_test_run_report.html.jinja'
SPEC_REPORT_TEMPLATE = 'dtest_test_spec_report.html.jinja'

SOURCE = "sqlite_source"

specs = {
    "No rows": {
        "tags": ['success'],
        "doc": "Assert 1 != 1",
        "source": "sqlite_source",
        "query": "select 42 as answer where 1 != 1"
    },
    "--Commented out": {
        "tags": ['success', 'commented'],
        "doc": "Assert 1 != 1",
        "source": "sqlite_source",
        "query": "select 42 as answer where 1 != 1"
    },
    "Faulty 42": {
        "tags": ['failure'],
        #"doc": "Get unexpected 42",
        "query": "select 42 as answer"
    },
    "Fault row": {
        "tags": ['failure'],
        "doc": "Get unexpected row.",
        "query": "select 1, 2, 3, 4, 5",
        "header": ['col_1', 'col_2', 'col_3', 'col_4', 'col_5']
    },
    "Setup and Upset": {
        "tags": ['setup', 'upset'],
        "doc": "First setup DB stuff and then release it.",
        "setup": "create table if not exists dtest_test as select 1 one",
        "query": "select 1 from dtest_test where one != 1",
        "upset": "drop table if exists dtest_test"
    },
}
