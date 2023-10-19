import os
import sys

from sources import sources


#
# Run sanity test with command line
#
#     dget.py dget-test
#
# and find output files in subdirectory out.
#


# MANDATORY constants used by dget.py

ENCODING = 'UTF-8'  # 'cp1251'

PY_DATE_FORMAT = '%d.%m.%Y'
PY_DATETIME_FORMAT = '%d.%m.%Y %H:%M:%S'

CSV_DIALECT = 'excel'
CSV_DELIMITER = ';'


# OPTIONAL CONSTANTS

#OUT_DIR = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), 'out')
DEBUGGING = True
#LOGSTDOUT = False

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
#        # output file encoding defaults to ENCODING
#        "encoding": ENCODING,
#        # decimal separator defaults to '.'
#        "dec_separator": '.',
#        #
#        # Column titles defaults to col names/aliases from the query.
#        # You can also either specify the list of titles explicilty
#        "titles": ['Qwerty', 'Asdfgh']
#        # or specify the SQL query returning titles. But not both :)
#        "titles": "select 'Col 1 Title', 'Col 2 Title'"
#    },
#    "example.csv": {
#        # MANDATORY name of the data source.
#        "source": "SRC",
#        # MANDATORY SQL query against the data source.
#        "query": "select 'qwerty', 'asdfgh'",
#        # Field titles defaults to col names/aliases from the query.
#        # You can also either specify the list of titles explicilty
#        "titles": ['Qwerty', 'Asdfgh']
#        # or specify the SQL query returning titles. But not both :)
#        "titles": "select 'Col 1 Title', 'Col 2 Title'"
#        # Ouput directory defaults to OUT_DIR.
#        "out_dir": OUT_DIR,
#        # Output file encoding defaults to ENCODING.
#        "encoding": ENCODING,
#        # Decimal separator defaults to '.'
#        "dec_separator": '.',
#        #
#        # CSV dialect defaults to CSV_DIALECT
#        "dialect": CSV_DIALECT
#        # CSV field delimiter defaults to CSV_DELIMITER
#        "delimiter": CSV_DELIMITER
#    },

specs = {
    "dget-1x1.csv": {
        "encoding": 'cp1251',
        "source": ".",
        "query": "select 'q' from dual"
    },
    "dget-1x1.xlsx": {
        "source": ".",
        "query": "select 'q' from dual"
    },
    "dget-1x1.html": {
        "source": ".",
        "query": "select 'q' from dual"
    },
    "dget-1xM with titles.csv": {
        "encoding": 'cp1251',
        "source": ".",
        "query": "select 'q', 'w', 'e', 'r', 't', 'y', 1, 2.0, current_date from dual",
        "titles": ['Q', 'W', 'E', 'R', 'T', 'Y', 'One', 'Two', 'Today']
    },
    "dget-1xM with titles.xlsx": {
        "source": ".",
        "query": "select 'q', 'w', 'e', 'r', 't', 'y', 1, 2.0, current_date from dual",
        "titles": ['Q', 'W', 'E', 'R', 'T', 'Y', 'One', 'Two', 'Today']
    },
    "dget-1xM with titles.html": {
        "source": ".",
        "query": "select 'q', 'w', 'e', 'r', 't', 'y', 1, 2.0, current_date from dual",
        "titles": ['Q', 'W', 'E', 'R', 'T', 'Y', 'One', 'Two', 'Today'],
        "title": "1 row with column titles"
    },
    "dget-NxM.csv": {
        "encoding": 'cp1251',
        "source": ".",
        "query": """
            with recursive numbers (n) as (
                select 0 as n from dual
                union all
                select n + 1
                from numbers
                where n < 9
            )
            select 'qwerty', 'привет', null, n, 0.0 + n, current_date, current_timestamp
            from numbers
            """,
        "titles": ['Q', 'hello', 'null', 'int', 'float', 'date', 'timestamp'],
        "dec_separator": ','
    },
    "dget-NxM.xlsx": {
        "source": ".",
        "query": """
            with recursive numbers (n) as (
                select 0 as n from dual
                union all
                select n + 1
                from numbers
                where n < 9
            )
            select 'qwerty', 'привет', null, n, 0.0 + n, current_date, current_timestamp
            from numbers
            """,
        "titles": ['Q', 'hello', 'null', 'int', 'float', 'date', 'timestamp'],
        "dec_separator": ','
    },
    "dget-NxM.html": {
        "source": ".",
        "query": """
            with recursive numbers (n) as (
                select 0 as n from dual
                union all
                select n + 1
                from numbers
                where n < 9
            )
            select 'qwerty', 'привет', null, n, 0.0 + n, current_date, current_timestamp
            from numbers
            """,
        "titles": ['Q', 'hello', 'null', 'int', 'float', 'date', 'timestamp'],
        "title": "Comma as decimal separator",
        "dec_separator": ','
    },
    "dget-NxM.json": {
        "source": ".",
        "query": """
            with recursive numbers (n) as (
                select 0 as n from dual
                union all
                select n + 1
                from numbers
                where n < 9
            )
            select 'qwerty', 'привет', null, n, 0.0 + n, current_date, current_timestamp
            from numbers
            """,
        "titles": ['Q', 'hello', 'null', 'int', 'float', 'date', 'timestamp']
    },
    "dget-10000.csv": {
        "encoding": 'cp1251',
        "source": ".",
        "query": """
            with recursive numbers (n) as (
                select 0 as n from dual
                union all
                select n + 1
                from numbers
                where n < 9999
            )
            select 'qwerty', 'привет', null, n, 0.0 + n, current_date, current_timestamp
            from numbers
            """,
        "titles": ['Q', 'hello', 'null', 'int', 'float', 'date', 'timestamp']
    },
    "dget-10000.xlsx": {
        "source": ".",
        "query": """
            with recursive numbers (n) as (
                select 0 as n from dual
                union all
                select n + 1
                from numbers
                where n < 9999
            )
            select 'qwerty', 'привет', null, n, 0.0 + n, current_date, current_timestamp
            from numbers
            """,
        "titles": ['Q', 'hello', 'null', 'int', 'float', 'date', 'timestamp']
    },
    "dget-10000.html": {
        "source": ".",
        "query": """
            with recursive numbers (n) as (
                select 0 as n from dual
                union all
                select n + 1
                from numbers
                where n < 9999
            )
            select 'qwerty', 'привет', null, n, 0.0 + n, current_date, current_timestamp
            from numbers
            """,
        "titles": ['Q', 'hello', 'null', 'int', 'float', 'date', 'timestamp'],
        "title": "10000 rows"
    },
    "dget-10000.json": {
        "source": ".",
        "query": """
            with recursive numbers (n) as (
                select 0 as n from dual
                union all
                select n + 1
                from numbers
                where n < 9999
            )
            select 'qwerty', 'привет', null, n, 0.0 + n, current_date, current_timestamp
            from numbers
            """,
        "titles": ['Q', 'hello', 'null', 'int', 'float', 'date', 'timestamp']
    },
    "dget-10000-custom.html": {
        "source": ".",
        "query": """
            with recursive numbers (n) as (
                select 0 as n from dual
                union all
                select n + 1
                from numbers
                where n < 9999
            )
            select 'qwerty', 'привет', null, n, 0.0 + n, current_date, current_timestamp
            from numbers
            """,
        "titles": ['Q', 'hello', 'null', 'int', 'float', 'date', 'timestamp'],
        "title": "10000 rows with custom template",
        "template": "dget-test.html.jinja"
    },
    "dget-10000-custom.json": {
        "source": ".",
        "query": """
            with recursive numbers (n) as (
                select 0 as n from dual
                union all
                select n + 1
                from numbers
                where n < 9999
            )
            select 'qwerty', 'привет', null, n, 0.0 + n, current_date, current_timestamp
            from numbers
            """,
        "titles": ['Q', 'hello', 'null', 'int', 'float', 'date', 'timestamp'],
        "template": "dget-test.json.jinja"
    },
}

sources['sqlite-source']['setup'] = sources['sqlite-source'].get('setup', []) + [
    "create table if not exists dual as select 'X' as dummy"
]

sources['postgres-source']['setup'] = sources['postgres-source'].get('setup', []) + [
    "create table if not exists dual as select 'X' as dummy"
]
