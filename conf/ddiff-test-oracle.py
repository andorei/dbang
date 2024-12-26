import os
import sys

from sources import sources

#
# Specify Oracle connection details for "oracle-source" in sources.py,
# then run sanity test against Oracle DB with command line
#     ddiff.py conf/ddiff-test-oracle.py
# and find test data discrepancies report in out/ddiff-test-oracle.html
#

#
# SETTINGS USED BY ddiff
#
# defaults to current working directory
OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'out')
# defaults to False
DEBUGGING = True
# defaults to False
LOGGING = True
# defaults to current working directory
LOG_DIR = os.path.join(os.path.dirname(__file__), '..', 'log')
# ddiff database defaults to sqlite database ~/.dbang/ddiff.db
DDIFF_SOURCE = sources['oracle-source']
# data sources
SOURCES = ["ONE", "TWO"]

#
# SETTINGS USED IN specs
#
# Next two sources are those with data to test for discrepancies
sources["ONE"] = sources["oracle-source"]
sources["TWO"] = sources["oracle-source"]

#
# Tests to detect data discrepancies between the two data sources
# QUERIES IN specs MAY USE FEATURES SPECIFIC TO oracle DATABASE
#
specs = {
    # just sanity testing
    "42": {
        "tags": ['success'],
        "sources": ["ONE", "TWO"],
        #"doc": "42 == 42"
        "pk": ["answer"],
        "queries": [
            "select 42 as answer from dual",
            "select 42 as answer from dual"
       ]
    },
    "--commented-out-42": {
        "tags": ['success'],
        "sources": ["ONE", "TWO"],
        #"doc": "42 == 42"
        "pk": ["answer"],
        "queries": [
            "select 42 as answer from dual",
            "select 42 as answer from dual"
       ]
    },
    "diffs": {
        "tags": ['failure'],
        "doc": "Intentionally failed",
        "pk": ["id"],
        "queries": [
            """
            select 1 as id, current_date as today from dual
            union all
            select 2, date '2023-01-01' from dual
            """,
            """
            select 1 as id, current_date as today from dual
            union all
            select 3, date '2023-01-02' from dual
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
            select 1 as id, current_date as today from dual
            union all
            select 2, date '2023-01-01' from dual
            """,
            """
            select 1 as id, current_date as today from dual
            union all
            select 2, date '2023-01-01' from dual
            union all
            select 3, date '2023-01-02' from dual
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
            select 1 as id, current_date as today from dual
            union all
            select 2, date '2023-01-01' from dual
            union all
            select 3, date '2023-01-02' from dual
            """,
            """
            select 1 as id, current_date as today from dual
            union all
            select 2, date '2023-01-01' from dual
            """
       ]
    },
    "nested": {
        "tags": ['failure'],
        "doc": "Intentionally failed",
        "pk": ["c1"],
        "queries": [
            "select 1 c1, 2 c2, 3 c3, 4 c4, 5 c5 from dual",
            "select 1 c1, 2 c2, 3 c3, 4 c4, 6 c5 from dual"
        ],
        #
        # level 2
        #
        "nested": {
            "pk": ["c1", "c2"],
            "queries": [
                """
                select 1 c1, 2 c2, 3 c3, current_timestamp c4, 5 c5
                from dual
                where 1 = {{argrows[0][0]}}
                """,
                """
                select 1 c1, 2 c2, 3 c3, current_timestamp c4, 6 c5
                from dual
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
                    from dual
                    where 1 = {{argrows[0][0]}}
                        and 2 = {{argrows[0][1]}}
                    """,
                    """
                    select 1 c1, 2 c2, 3 c3, current_timestamp c4, 6 c5
                    from dual
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
            select 1 c1, to_char(current_timestamp) c2, 3 c3 from dual
            union all
            select 2 c1, to_char(current_timestamp) c2, 5 c3 from dual
            union all
            select 3 c1, to_char(current_timestamp) c2, 7 c3 from dual
            union all
            select 5 c1, to_char(current_timestamp) c2, 1 c3 from dual
            """,
            """
            select 1 c1, to_char(current_timestamp + interval '5' second) c2, 3 c3 from dual
            union all
            select 2 c1, to_char(current_timestamp) c2, 6 c3 from dual
            union all
            select 4 c1, to_char(current_timestamp) c2, 9 c3 from dual
            union all
            select 5 c1, to_char(current_timestamp) c2, 1 c3 from dual
            """
       ]
    },
    "nested-with-setup-and-upset": {
        "tags": ["setup", "upset"],
        "doc": "First setup DB stuff and then release it.",
        "setups": [
            [
                """
begin 
    execute immediate 'drop table ddiff_test_db1';
exception
    when others then
        if sqlcode = -942 then
            null; -- ORA-00942 table or view does not exist
        end if;
end;
                """,
                """
create table ddiff_test_db1 as
select 1 a, 'hello' b, current_date c
from dual
                """
            ],
            [
                """
begin 
    execute immediate 'drop table ddiff_test_db2';
exception
    when others then
        if sqlcode = -942 then
            null; -- ORA-00942 table or view does not exist
        end if;
end;
                """,
                """
create table ddiff_test_db2 as
select 1 a, 'hello' b, current_date c
from dual
                """
            ]
        ],
        "pk": ["a"],
        "queries": [
            "select a, b, c, 1 d from ddiff_test_db1",
            "select a, b, c, 2 d from ddiff_test_db2"
        ],
        "upsets": [
            """
begin 
    execute immediate 'drop table ddiff_test_db1';
exception
    when others then
        if sqlcode = -942 then
            null; -- ORA-00942 table or view does not exist
        end if;
end;
            """,
            """
begin 
    execute immediate 'drop table ddiff_test_db2';
exception
    when others then
        if sqlcode = -942 then
            null; -- ORA-00942 table or view does not exist
        end if;
end;
            """
        ],
        #
        # level 2
        #
        "setup then upset": {
            "pk": ["a"],
            "queries": [
                "select a, b, c from ddiff_test_db1",
                "select a, b, c from ddiff_test_db2"
            ],
        }
    },
}

sources['oracle-source']['setup'] = sources['oracle-source'].get('setup', []) + [
    "alter session set nls_date_format='yyyy-mm-dd'",
    "alter session set nls_timestamp_format='yyyy-mm-dd hh24:mi:ss'",
    "alter session set nls_timestamp_tz_format='yyyy-mm-dd hh24:mi:ss tzh:tzm'"
]
