import os
import sys


# MANDATORY constants used by dget.py

CSV_ENCODING = 'cp1251'
CSV_DIALECT = 'excel'
CSV_DELIMITER = ';'

HTML_ENCODING = 'UTF-8'

PY_DATE_FORMAT = '%d.%m.%Y'
PY_DATETIME_FORMAT = '%d.%m.%Y %H:%M:%S'

OUT_DIR = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), 'out')

# Optional constants used in specs below


# Data sources used in specs below
sources = {
    "sqlite-source": {
        "database": "sqlite",
        "con_string": os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), f'.dbang.db')
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

# dot-source just allows specs to refer indirectlty to data sources
sources['.'] = sources['sqlite-source']
#sources['.'] = sources['postgres-source']
#sources['.'] = sources['oracle-source']
#sources['.'] = sources['mysql-source']

#specs = {
#    # output file name with extension
#    "example.html": {
#        # MANDATORY name of the data source
#        "source": "SRC",
#        # MANDATORY SQL query against the data source
#        "query": "select 'qwerty', 'asdfgh'",
#        # ouput directory defaults to OUT_DIR
#        "out_dir": OUT_DIR,
#        # html page title and header default to file name minus extension
#        "title": "Example HTML formatted data",
#        # output file encoding defaults to HTML_ENCODING
#        "encoding": HTML_ENCODING,
#        # decimal separator defaults to '.'
#        "dec_separator": '.',
#        #
#        # column titles default to col names/aliases from the query
#        "titles": ['Qwerty', 'Asdfgh']
#    },
#    "example.csv": {
#        # MANDATORY name of the data source
#        "source": "SRC",
#        # MANDATORY SQL query against the data source
#        "query": "select 'qwerty', 'asdfgh'",
#        # fieled titles default to col names/aliases from the query
#        "titles": ['Qwerty', 'Asdfgh']
#        # ouput directory defaults to OUT_DIR
#        "out_dir": OUT_DIR,
#        # output file encoding defaults to CSV_ENCODING
#        "encoding": CSV_ENCODING,
#        # decimal separator defaults to '.'
#        "dec_separator": '.',
#        #
#        # CSV dialect defaults to CSV_DIALECT
#        "dialect": CSV_DIALECT
#        # CSV field delimiter defaults to CSV_DELIMITER
#        "delimiter": CSV_DELIMITER
#    },

specs = {
    "1 row 1 column.html": {
        "source": ".",
        "query": "select 'q' from dual"
    },
    "1 row 1 column.csv": {
        "source": ".",
        "query": "select 'q' from dual"
    },
    "1 row many columns.html": {
        "source": ".",
        "query": "select 'q', 'w', 'e', 'r', 't', 'y', 1, 2.0, current_date from dual",
        #"directory": os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), 'log'),
        "title": "1 many columns"
    },
    "1 row many columns.csv": {
        "source": ".",
        "query": "select 'q', 'w', 'e', 'r', 't', 'y', 1, 2.0, current_date from dual",
        #"directory": os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), 'log'),
    },
    "1 row with column titles.html": {
        "source": ".",
        "query": "select 'q', 'w', 'e', 'r', 't', 'y', 1, 2.0, current_date from dual",
        "titles": ['Q', 'W', 'E', 'R', 'T', 'Y', 'One', 'Two', 'Today'],
        "title": "1 row with column titles"
    },
    "1 row with column titles.csv": {
        "source": ".",
        "query": "select 'q', 'w', 'e', 'r', 't', 'y', 1, 2.0, current_date from dual",
        "titles": ['Q', 'W', 'E', 'R', 'T', 'Y', 'One', 'Two', 'Today']
    },
    "10 rows 1 column.html": {
        "source": ".",
        "query": """
            with recursive numbers (n) as (
                select 1 as n from dual
                union all
                select n + 1
                from numbers
                where n < 10
            )
            select * from numbers
            """,
        "title": "10 rows 1 column"
    },
    "10 rows 1 column.csv": {
        "source": ".",
        "query": """
            with recursive numbers (n) as (
                select 1 as n from dual
                union all
                select n + 1
                from numbers
                where n < 10
            )
            select * from numbers
            """
    },
    "10 rows 10 columns.html": {
        "source": ".",
        "query": """
            with recursive numbers (n) as (
                select 1 as n from dual
                union all
                select n + 1
                from numbers
                where n < 10
            )
            select 'q', 'w', 'e', 'привет', n, 0.0 + n, current_date 
            from numbers
            """,
        "titles": ['Q', 'W', 'E', 'Привет', 'One', 'Two', 'Dates'],
        "title": "10 rows 10 columns",
        "dec_separator": ','
    },
    "10 rows 10 columns.csv": {
        "source": ".",
        "query": """
            with recursive numbers (n) as (
                select 1 as n from dual
                union all
                select n + 1
                from numbers
                where n < 10
            )
            select 'q', 'w', 'e', 'привет', n, 0.0 + n, current_date 
            from numbers
            """,
        "titles": ['Q', 'W', 'E', 'Привет', 'One', 'Two', 'Dates'],
        "dec_separator": ','
    },
    "1000 rows 10 columns.html": {
        "source": ".",
        "query": """
            with recursive numbers (n) as (
                select 1 as n from dual
                union all
                select n + 1
                from numbers
                where n < 1000
            )
            select 'q', 'w', 'e', 'r', 't', 'y', n, 0.0 + n, current_date 
            from numbers
            """,
        "titles": ['Q', 'W', 'E', 'R', 'T', 'Y', 'One', 'Two', 'Dates'],
        "title": "100000 rows 10 columns"
    },
    "1000 rows 10 columns.csv": {
        "source": ".",
        "query": """
            with recursive numbers (n) as (
                select 1 as n from dual
                union all
                select n + 1
                from numbers
                where n < 1000
            )
            select 'q', 'w', 'e', 'r', 't', 'y', n, 0.0 + n, current_date 
            from numbers
            """,
        "titles": ['Q', 'W', 'E', 'R', 'T', 'Y', 'One', 'Two', 'Dates']
    },
}

sources['sqlite-source']['init'] = [
    "create table if not exists dual as select 'X' as dummy"
]

sources['postgres-source']['init'] = [
    "create table if not exists dual as select 'X' as dummy",
    "set timezone=\'Asia/Vladivostok\'"
]
