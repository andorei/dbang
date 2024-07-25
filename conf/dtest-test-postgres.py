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
        "doc": "Get unexpected row",
        "query": "select 1, 2, 3, 4, 5 from dual",
        "titles": ['col_1', 'col_2', 'col_3', 'col_4', 'col_5']
    }
}

sources['postgres-source']['setup'] = sources['postgres-source'].get('setup', []) + [
    "create table if not exists dual as select 'X' as dummy"
]
