import os
import sys

from sources import sources

#
# Run sanity test with command line
#     dget.py conf/dget-test-sqlite.py
# and find output files in subdirectory out.
#
# Use --output option to specify output format other than set in spec:
#     dget.py --output xlsx conf/dget-test-sqlite.py
#

#
# SETTINGS USED BY dget
#
# defaults to current working directory
OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'out')
# defaults to False
DEBUGGING = True
# defaults to False
LOGGING = True
# defaults to current working directory
LOG_DIR = os.path.join(os.path.dirname(__file__), '..', 'log')
# output files' encoding defaults to OS locale encoding
ENCODING = 'UTF-8'
# defaults to ISO 86101; use '%c' to align with locale
#DATETIME_FORMAT = '%c'
# defaults to ISO 86101; use '%x' to align with locale
#DATE_FORMAT = '%x'
# defaults to 'excel'
#CSV_DIALECT = 'excel'
# defaults to the dialect delimiter
CSV_DELIMITER = ';'
# number of trace files presrved in helper dir
PRESERVE_N_TRACES = 3
# data source
SOURCE = "sqlite-source"

#
# SETTINGS USED IN specs
#
pass

#specs = {
#    # spec name
#    "example": {
#        # optional tags to use in CLI instead of spec name
#        "tags": ['debug'],
#        # MANDATORY file name where extension determines output format by default.
#        # You can also set filename using conventions for string interpolation with modulo operator %.
#        # Use named replacement fields 'date', 'datetime', 'seqn' and 'user'.
#        "file": "example.html"
#        # or
#        "file": "%(datetime)s_%(seqn)06i_%(user)s_example.json'
#        # optional number of dataset rows to write in a single file; 0 stands for all rows
#        "rows_per_file": 100
#        # name of the data source defaults to SOURCE (if set)
#        "source": SOURCE,
#        # MANDATORY SQL query against the data source
#        "query": "select 'qwerty', 'asdfgh'",
#        # dict with names and default values for bind variables in the query if any
#        "bind_args": {},
#        # Column titles defaults to col names/aliases from the query.
#        # You can also either specify the list of titles explicitly
#        "header": ['Qwerty', 'Asdfgh']
#        # or specify the SQL query returning titles. But not both :)
#        "header": "select 'Col 1 Title', 'Col 2 Title'"
#
#        # optional format specific parameters
#
#        # CSV file encoding defaults to ENCODING
#        "csv.encoding": ENCODING,
#        # CSV dialect defaults to CSV_DIALECT
#        "csv.dialect": CSV_DIALECT,
#        # CSV field delimiter defaults to CSV_DELIMITER
#        "csv.delimiter": CSV_DELIMITER,
#        # CSV decimal separator defaults to '.'
#        "csv.dec_separator": '.',
#
#        # json file encoding defaults to ENCODING
#        "json.encoding": ENCODING,
#        # json jinja template defaults to dget.json.jinja
#        "json.template": "dget.json.jinja"
#
#        # html file encoding defaults to ENCODING
#        "html.encoding": ENCODING,
#        # html decimal separator defaults to '.'
#        "html.dec_separator": '.',
#        # html page title and header default to spec name
#        "html.title": "Example HTML formatted data",
#        # html jinja template defaults to dget.html.jinja
#        "html.template": "dget.html.jinja",
#
#        # no specific parameters for xlsx
#    }

specs = {
    "1x1": {
        "file": "dget-1x1.csv",
        "query": "select 'q' from dual",
        "csv.encoding": 'cp1251'
    },
    "--commented-out-1x1": {
        "tags": ['commented'],
        "file": "dget-1x1.csv",
        "query": "select 'q' from dual",
        "csv.encoding": 'cp1251'
    },
    "1xM-with-header": {
        "file": "dget-1xM-with-header.csv",
        "query": "select 'q', 'w', 'e', 'r', 't', 'y', 1, 2.0, current_date from dual",
        "header": ['Q', 'W', 'E', 'R', 'T', 'Y', 'One', 'Two', 'Today'],
        "csv.encoding": 'cp1251',
        "html.title": "1 row with column titles"
    },
    "NxM-with-comma": {
        "file": "dget-NxM.csv",
        "query": """
            with recursive numbers (n) as (
                select 0 as n from dual
                union all
                select n + 1
                from numbers
                where n < 9
            )
            select 'qwerty', 'привет', null, n, 0.1 + n, current_date, current_timestamp
            from numbers
            """,
        "header": ['Q', 'hello', 'null', 'int', 'float', 'date', 'timestamp'],
        "dec_separator": ',',
        "csv.encoding": 'cp1251',
        "html.title": "Comma as decimal separator"
    },
    "1000": {
        "file": "dget-1000.csv",
        "tags": ['1000'],
        "query": """
            with recursive numbers (n) as (
                select 0 as n from dual
                union all
                select n + 1
                from numbers
                where n < 999
            )
            select 'qwerty', 'привет', null, n, 0.0 + n, current_date, current_timestamp
            from numbers
            """,
        "header": ['Q', 'hello', 'null', 'int', 'float', 'date', 'timestamp'],
        "csv.encoding": 'cp1251',
        "html.title": "1000 rows"
    },
    "1000.zip": {
        "file": "dget-1000.csv.zip",
        "tags": ['1000', 'zip'],
        "query": """
            with recursive numbers (n) as (
                select 0 as n from dual
                union all
                select n + 1
                from numbers
                where n < 999
            )
            select 'qwerty', 'привет', null, n, 0.0 + n, current_date, current_timestamp
            from numbers
            """,
        "header": ['Q', 'hello', 'null', 'int', 'float', 'date', 'timestamp'],
        "csv.encoding": 'cp1251',
        "html.title": "1000 rows"
    },
    "by-100": {
        "file": "dget-%(datetime)s_%(seqn)06i_by-100.csv",
        "rows_per_file": 100,
        "query": """
            with recursive numbers (n) as (
                select 0 as n from dual
                union all
                select n + 1
                from numbers
                where n < 999
            )
            select 'qwerty', 'привет', null, n, 0.0 + n, current_date, current_timestamp
            from numbers
            """,
        "header": ['Q', 'hello', 'null', 'int', 'float', 'date', 'timestamp'],
        "csv.encoding": 'cp1251',
        "html.title": "100 of 1000 rows"
    },
    "by-100.zip": {
        "file": "dget-%(datetime)s_%(seqn)06i_by-100.xlsx.zip",
        "rows_per_file": 100,
        "query": """
            with recursive numbers (n) as (
                select 0 as n from dual
                union all
                select n + 1
                from numbers
                where n < 999
            )
            select 'qwerty', 'привет', null, n, 0.0 + n, current_date, current_timestamp
            from numbers
            """,
        "header": ['Q', 'hello', 'null', 'int', 'float', 'date', 'timestamp'],
        "csv.encoding": 'cp1251',
        "html.title": "100 of 1000 rows"
    },
    "1000-custom": {
        "file": "dget-1000-custom.html",
        "tags": ['1000'],
        "query": """
            with recursive numbers (n) as (
                select 0 as n from dual
                union all
                select n + 1
                from numbers
                where n < 999
            )
            select 'qwerty', 'привет', null, n, 0.0 + n, current_date, current_timestamp
            from numbers
            """,
        "header": ['Q', 'hello', 'null', 'int', 'float', 'date', 'timestamp'],
        "csv.encoding": 'cp1251',
        "html.title": "1000 rows with custom template",
        "html.template": "dget-test.html.jinja",
        "json.template": "dget-test.json.jinja"
    },
    "with-params": {
        "file": "dget-with-params-%(user)s.csv",
        "query": """
            with recursive numbers (n) as (
                select 0 as n from dual
                union all
                select n + 1
                from numbers
                where n < 999
            )
            select :eng, :rus, null, n, 0.0 + n, current_date, current_timestamp
            from numbers
            where n / :mod = round(n / :mod)
            """,
        "bind_args": {"eng": "Hi", "rus": "Привет", "mod": 10.0},
        "header": ['Q', 'hello', 'null', 'int', 'float', 'date', 'timestamp'],
        "csv.encoding": 'cp1251'
    },
}

sources['sqlite-source']['setup'] = sources['sqlite-source'].get('setup', []) + [
    "create table if not exists dual as select 'X' as dummy"
]
