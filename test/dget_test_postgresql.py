import os
import sys

from sources import sources


# See details on config file's and spec parameters in doc/dget.md

DEBUGGING = True
LOGGING = True
PARALLEL_WORKERS = 2

OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'out')
LOG_DIR = os.path.join(os.path.dirname(__file__), '..', 'log')

ENCODING = 'UTF-8'
CSV_DIALECT = 'excel'
CSV_DELIMITER = ';'

# defaults to ISO 86101; use '%c' to align with locale
#DATETIME_FORMAT = '%c'
# defaults to ISO 86101; use '%x' to align with locale
#DATE_FORMAT = '%x'

SOURCE = "postgresql_source"
PRESERVE_N_TRACES = 3

specs = {
    "1x1": {
        "file": "dget_1x1.csv",
        "query": "select 'q'",
        "csv.encoding": 'cp1251'
    },
    "--commented_out_1x1": {
        "tags": ['commented'],
        "file": "dget_1x1.csv",
        "query": "select 'q'",
        "csv.encoding": 'cp1251'
    },
    "1xM_with_header": {
        "file": "dget_1xM_with_header.csv",
        "query": "select 'q', 'w', 'e', 'r', 't', 'y', 1, 2.0, current_date",
        "header": ['Q', 'W', 'E', 'R', 'T', 'Y', 'One', 'Two', 'Today'],
        "csv.encoding": 'cp1251',
        "html.title": "1 row with column titles"
    },
    "NxM_with_comma": {
        "file": "dget_NxM.csv",
        "query": """
            with recursive numbers (n) as (
                select 0 as n
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
    "1000_qwerty": {
        "file": "dget_1000_qwerty.csv",
        "tags": ['1000'],
        "query": """
            with recursive numbers (n) as (
                select 0 as n
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
        "file": "dget_1000.csv.zip",
        "tags": ['1000', 'zip'],
        "query": """
            with recursive numbers (n) as (
                select 0 as n
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
    "by_100": {
        "file": "dget_%(datetime)s_%(seqn)06i_by_100.csv",
        "rows_per_file": 100,
        "query": """
            with recursive numbers (n) as (
                select 0 as n
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
    "by_100.zip": {
        "file": "dget_%(datetime)s_%(seqn)06i_by_100.xlsx.zip",
        "rows_per_file": 100,
        "query": """
            with recursive numbers (n) as (
                select 0 as n
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
    "1000_custom": {
        "file": "dget_1000_custom.html",
        "tags": ['1000'],
        "query": """
            with recursive numbers (n) as (
                select 0 as n
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
        "html.template": "dget_test.html.jinja",
        "json.template": "dget_test.json.jinja"
    },
    "with_params": {
        "file": "dget_with_params_%(user)s.csv",
        "query": """
            with recursive numbers (n) as (
                select 0 as n
                union all
                select n + 1
                from numbers
                where n < 999
            )
            select %(eng)s, %(rus)s, null, n, 0.0 + n, current_date, current_timestamp
            from numbers
            where n / %(mod)s = round(n / %(mod)s)
            """,
        "bind_args": {"eng": "Hi", "rus": "Привет", "mod": 10.0},
        "header": ['Q', 'hello', 'null', 'int', 'float', 'date', 'timestamp'],
        "csv.encoding": 'cp1251'
    },
    "naive": {
        "file": "dget_naive.csv",
        "query": """
            with recursive numbers (n) as (
                select 0 as n
                union all
                select n + 1
                from numbers
                where n < 9
            )
            select 'qwerty', '"привет" means "hello"', null, n, 0.1 + n, current_date, current_timestamp
            from numbers
            """,
        "header": ['Q', 'hello', 'null', 'int', 'float', 'date', 'timestamp'],
        "csv.dialect": "naive",
        "csv.encoding": 'cp1251'
    },
}
