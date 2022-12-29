import os
import sys

#
# data sources
#
sources = {
    "sqlite-source": {
        "database": "sqlite",
        "con_string": os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), f'.dbang.db'),
    },
    "postgres-source": {
        "database": "postgres",
        "con_string": "postgresql://username:password@host/database"
    },
    "oracle-source": {
        "database": "oracle",
        "con_string": "username/password@host:1521/ORA",
        "con_kwargs": {"encoding": "UTF-8"}
    },
    "mysql-source": {
        "database": "mysql",
        "con_string": "",
        "con_kwargs": {'host': 'host', 'database': 'database', 'user': 'username', 'password': 'password'}
    }
}

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

sources['sqlite-source']['init'] = [
    "create table if not exists dual as select 'X' as dummy"
]

sources['postgres-source']['init'] = [
    "create table if not exists dual as select 'X' as dummy"
]
