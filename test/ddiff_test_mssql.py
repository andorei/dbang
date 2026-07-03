import os
import sys

from sources import sources


# See details on config file's and spec parameters in doc/ddiff.md

DEBUGGING = True
LOGGING = True
PARALLEL_WORKERS = 2

OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'out')
LOG_DIR = os.path.join(os.path.dirname(__file__), '..', 'log')

SOURCES = ["ONE", "TWO"]
sources["ONE"] = sources["mssql_source"]
sources["TWO"] = sources["mssql_source"]
DDIFF_SOURCE = sources["mssql_source"]

RUN_REPORT_TEMPLATE = 'ddiff_test_run.html.jinja'
SPEC_REPORT_TEMPLATE = 'ddiff_test_spec.html.jinja'

specs = {
    "42": {
        "tags": ['success'],
        "sources": ["ONE", "TWO"],
        #"doc": "42 == 42"
        "pk": ["answer"],
        "queries": [
            "select 42 as answer",
            "select 42 as answer"
       ]
    },
    "--commented-out-42": {
        "tags": ['success', 'commented'],
        "sources": ["ONE", "TWO"],
        #"doc": "42 == 42"
        "pk": ["answer"],
        "queries": [
            "select 42 as answer",
            "select 42 as answer"
       ]
    },
    "diffs": {
        "tags": ['failure'],
        "op": "=",
        "doc": "Intentionally failed",
        "pk": ["id"],
        "queries": [
            """
            select 1 as id, current_date as today
            union all
            select 2, cast('2023-01-01' as date)
            """,
            """
            select 1 as id, current_date as today
            union all
            select 3, cast('2023-01-02' as date)
            """
       ]
    },
    "diffs.lt": {
        "tags": ['success'],
        "op": "<",
        "doc": "Dataset 1 is subset of or equal to Dataset 2",
        "pk": ["id"],
        "queries": [
            """
            select 1 as id, current_date as day
            union all
            select 2, cast('2023-01-01' as date)
            """,
            """
            select 1 as id, current_date as day
            union all
            select 2, cast('2023-01-01' as date)
            union all
            select 3, cast('2023-01-02' as date)
            """
       ]
    },
    "diffs.gt": {
        "tags": ['success'],
        "op": ">",
        "doc": "Dataset 1 is equal to or superset of Dataset 2",
        "pk": ["id"],
        "queries": [
            """
            select 1 as id, current_date as day
            union all
            select 2, cast('2023-01-01' as date)
            union all
            select 3, cast('2023-01-02' as date)
            """,
            """
            select 1 as id, current_date as day
            union all
            select 2, cast('2023-01-01' as date)
            """
       ]
    },
    "nested": {
        "tags": ['failure'],
        "doc": "Intentionally failed",
        "pk": ["c1"],
        "queries": [
            "select 1 c1, 2 c2, 3 c3, 4 c4, 5 c5",
            "select 1 c1, 2 c2, 3 c3, 4 c4, 6 c5"
        ],
        #
        # level 2
        #
        "nested": {
            "pk": ["c1", "c2"],
            "queries": [
                """
                select 1 c1, 2 c2, 3 c3, current_timestamp c4, 5 c5
                where 1 = {{argrows[0][0]}}
                """,
                """
                select 1 c1, 2 c2, 3 c3, current_timestamp c4, 6 c5
                where 1 = {{argrows[0][0]}}
                """
            ],
            #
            # level 3
            #
            "nested": {
                "pk": ["c1", "c2", "c3"],
                "queries": [
                    """
                    select 1 c1, 2 c2, 3 c3, current_timestamp c4, 5 c5
                    where 1 = {{argrows[0][0]}}
                        and 2 = {{argrows[0][1]}}
                    """,
                    """
                    select 1 c1, 2 c2, 3 c3, current_timestamp c4, 6 c5
                    where 1 = {{argrows[0][0]}}
                        and 2 = {{argrows[0][1]}}
                    """
               ]
            }
        }
    },
    "current": {
        "tags": ['failure'],
        "doc": "Intentionally failed",
        "pk": ["c1"],
        "queries": [
            """
            select 1 c1, current_timestamp c2, 3 c3
            union all
            select 2 c1, current_timestamp c2, 5 c3
            union all
            select 3 c1, current_timestamp c2, 7 c3
            union all
            select 5 c1, current_timestamp c2, 1 c3
            """,
            """
            select 1 c1, current_timestamp c2, 3 c3
            union all
            select 2 c1, current_timestamp c2, 6 c3
            union all
            select 4 c1, current_timestamp c2, 9 c3
            union all
            select 5 c1, current_timestamp c2, 1 c3
            """
       ]
    },
    "nested-with-setup-and-upset": {
        "tags": ['setup', 'upset'],
        "doc": "First setup DB stuff and then release it.",
        "setups": [
            """
if object_id('ddiff_test_db1', 'U') is null
select 1 a, 'hello' b, current_date c into ddiff_test_db1
            """,
            """
if object_id('ddiff_test_db2', 'U') is null
select 1 a, 'hello' b, current_date c into ddiff_test_db2
            """,
        ],
        "pk": ["a"],
        "queries": [
            "select a, b, c, 1 d from ddiff_test_db1",
            "select a, b, c, 2 d from ddiff_test_db2"
        ],
        "upsets": [
            "drop table if exists ddiff_test_db1",
            "drop table if exists ddiff_test_db2"
        ],
        #
        # level 2
        #
        "nested-with-setup-and-upset": {
            "pk": ["a"],
            "queries": [
                "select a, b, c from ddiff_test_db1",
                "select a, b, c from ddiff_test_db2"
            ],
        }
    },
}
