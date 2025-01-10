import os
import sys

from sources import sources

#
# Run sanity test with command line
#     dtest.py conf/dtest-test-postgres.py
# and see data quality report out/dtest-test-postgres.html.
#

#
# SETTINGS USED BY dtest
#
OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'out')
DEBUGGING = True
LOGGING = True
LOG_DIR = os.path.join(os.path.dirname(__file__), '..', 'log')
# defaults to ISO 86101; use '%c' to align with locale
#DATETIME_FORMAT = '%c'
# defaults to ISO 86101; use '%x' to align with locale
#DATE_FORMAT = '%x'
SOURCE = "postgres-source"

#
# SETTINGS USED IN specs
#
pass

specs = {
    "No rows": {
        "tags": ['success'],
        "doc": "Assert 1 != 1",
        "source": "postgres-source",
        "query": "select 42 as answer from dual where 1 != 1"
    },
    "Faulty 42": {
        "tags": ['failure'],
        #"doc": "Get unexpected 42",
        "query": "select 42 as answer from dual"
    },
    "Fault row": {
        "tags": ['failure'],
        "doc": "Get unexpected row.",
        "query": "select 1, 2, 3, 4, 5 from dual",
        "titles": ['col_1', 'col_2', 'col_3', 'col_4', 'col_5']
    },
    "Setup and Upset": {
        "tags": ['setup', 'upset'],
        "doc": "First setup DB stuff and then release it.",
        "setup": "create table if not exists dtest_test as select 1 one from dual",
        "query": "select 1 from dtest_test where one != 1",
        "upset": "drop table if exists dtest_test"
    },
}

sources['postgres-source']['setup'] = sources['postgres-source'].get('setup', []) + [
    "create table if not exists dual as select 'X' as dummy"
]
