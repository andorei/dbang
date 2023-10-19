import os
import sys

from sources import sources


#
# Run sanity test with command line
#
#     dtest.py dtest-test
#
# and see data quality report out/dtest-test.html.
#


# OPTIONAL CONSTANTS

#OUT_DIR = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), 'out')

DEBUGGING = True
#LOGSTDOUT = False

# dot-source just allows tests to refer indirectlty to data sources
sources['.'] = sources['sqlite-source']
#sources['.'] = sources['postgres-source']
#sources['.'] = sources['oracle-source']
#sources['.'] = sources['mysql-source']


specs = {
    "No rows": {
        "source": ".",
        "query": "select 42 as answer from dual where 1 != 1"
    },
    "Faulty 42": {
        "source": ".",
        "query": "select 42 as answer from dual"
    },
    "Fault row": {
        "source": ".",
        "query": "select 1, 2, 3, 4, 5 from dual",
        "titles": ['col_1', 'col_2', 'col_3', 'col_4', 'col_5']
    }
}

sources['sqlite-source']['setup'] = sources['sqlite-source'].get('setup', []) + [
    "create table if not exists dual as select 'X' as dummy"
]

sources['postgres-source']['setup'] = sources['postgres-source'].get('setup', []) + [
    "create table if not exists dual as select 'X' as dummy"
]
