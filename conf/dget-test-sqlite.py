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
# defaults to OS locale format
#DATE_FORMAT = '%d.%m.%Y'
# defaults to OS locale format
#DATETIME_FORMAT = '%d.%m.%Y %H:%M:%S'
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
#        "titles": ['Qwerty', 'Asdfgh']
#        # or specify the SQL query returning titles. But not both :)
#        "titles": "select 'Col 1 Title', 'Col 2 Title'"
#        # ouput directory defaults to OUT_DIR
#        "out_dir": OUT_DIR,
#        #
#        # optional format specific parameters
#        #
#        "csv": {
#            # output file encoding defaults to ENCODING
#            "encoding": ENCODING,
#            # CSV dialect defaults to CSV_DIALECT
#            "dialect": CSV_DIALECT,
#            # CSV field delimiter defaults to CSV_DELIMITER
#            "delimiter": CSV_DELIMITER,
#            # decimal separator defaults to '.'
#            "dec_separator": '.'
#        },
#        "html": {
#            # should html encoding just always be UTF-8?
#            "encoding": ENCODING,
#            # decimal separator defaults to '.'
#            "dec_separator": '.',
#            # html page title and header default to spec name
#            "title": "Example HTML formatted data",
#            # html jinja template defaults to dget.html.jinja
#            "template": "dget.html.jinja"
#        },
#        "json": {
#            # should json encoding just always be UTF-8?
#            "encoding": ENCODING,
#            # json jinja template defaults to dget.json.jinja
#            "template": "dget.json.jinja"
#        }
#        # no specific parameters for xlsx
#    }

specs = {
    "1x1": {
        "file": "dget-1x1.csv",
        "query": "select 'q' from dual",
        "csv": {"encoding": 'cp1251'}
    },
    "--commented-out-1x1": {
        "tags": ['commented'],
        "file": "dget-1x1.csv",
        "query": "select 'q' from dual",
        "csv": {"encoding": 'cp1251'}
    },
    "1xM-with-titles": {
        "file": "dget-1xM-with-titles.csv",
        "query": "select 'q', 'w', 'e', 'r', 't', 'y', 1, 2.0, current_date from dual",
        "titles": ['Q', 'W', 'E', 'R', 'T', 'Y', 'One', 'Two', 'Today'],
        "csv": {"encoding": 'cp1251'},
        "html": {"title": "1 row with column titles"}
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
        "titles": ['Q', 'hello', 'null', 'int', 'float', 'date', 'timestamp'],
        "csv": {"encoding": 'cp1251', "dec_separator": ','},
        "html": {"title": "Comma as decimal separator", "dec_separator": ','}
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
        "titles": ['Q', 'hello', 'null', 'int', 'float', 'date', 'timestamp'],
        "csv": {"encoding": 'cp1251'},
        "html": {"title": "1000 rows"}
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
        "titles": ['Q', 'hello', 'null', 'int', 'float', 'date', 'timestamp'],
        "csv": {"encoding": 'cp1251'},
        "html": {"title": "100 of 1000 rows"}
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
        "titles": ['Q', 'hello', 'null', 'int', 'float', 'date', 'timestamp'],
        "csv": {"encoding": 'cp1251'},
        "html": {"title": "1000 rows with custom template", "template": "dget-test.html.jinja"},
        "json": {"template": "dget-test.json.jinja"}
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
        "titles": ['Q', 'hello', 'null', 'int', 'float', 'date', 'timestamp'],
        "csv": {"encoding": 'cp1251'}
    },
}

sources['sqlite-source']['setup'] = sources['sqlite-source'].get('setup', []) + [
    "create table if not exists dual as select 'X' as dummy"
]
