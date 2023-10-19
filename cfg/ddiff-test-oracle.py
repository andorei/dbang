import os
import sys

from sources import sources

#
# Specify Oracle connection details for "oracle-source" in sources.py,
# then run sanity test against Oracle DB with command line
#
#     ddiff.py ddiff-test-oracle
#
# and find test data discrepancies report in out/ddiff-test-oracle.html
#


# MANDATORY CONSTANTS used by ddiff.py

# DB where intermediate data is kept and processed
DDIFF_SOURCE = sources['oracle-source']


# OPTIONAL CONSTANTS

# Directory where discrepancies report is saved
#OUT_DIR = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), 'out')

DEBUGGING = True
#LOGSTDOUT = False

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
        "sources": ["ONE", "TWO"],
        "pk": ["answer"],
        "queries": [
            "select 42 as answer from dual",
            "select 42 as answer from dual"
       ]
    },
    "diffs": {
        "sources": ["ONE", "TWO"],
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
    "nested": {
        "sources": ["ONE", "TWO"],
        "pk": ["c1"],
        "queries": [
            "select 1 c1, 2 c2, 3 c3, 4 c4, 5 c5 from dual",
            "select 1 c1, 2 c2, 3 c3, 4 c4, 6 c5 from dual"
        ],
        # level 2
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
            # level 3
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
        "sources": ["ONE", "TWO"],
        "pk": ["c1"],
        "queries": [
            """
            select 1 c1, current_timestamp c2, 3 c3 from dual
            union all
            select 2 c1, current_timestamp c2, 5 c3 from dual
            union all
            select 3 c1, current_timestamp c2, 7 c3 from dual
            union all
            select 5 c1, current_timestamp c2, 1 c3 from dual
            """,
            """
            select 1 c1, current_timestamp + interval '5' second c2, 3 c3 from dual
            union all
            select 2 c1, current_timestamp c2, 6 c3 from dual
            union all
            select 4 c1, current_timestamp c2, 9 c3 from dual
            union all
            select 5 c1, current_timestamp c2, 1 c3 from dual
            """
       ]
    },
}

sources['oracle-source']['setup'] = sources['oracle-source'].get('setup', []) + [
    """
declare
    table_exists pls_integer;
begin
    select count(*)
    into table_exists
    from all_tables
    where table_name in ('DDIFF_')
    ;
    if 0 = table_exists then
        execute immediate '
            create table ddiff_(
                cfg varchar2(4000),
                spec varchar2(4000),
                run number,
                source varchar2(4000),
                c1 varchar2(4000), c2 varchar2(4000), c3 varchar2(4000), c4 varchar2(4000), c5 varchar2(4000),
                c6 varchar2(4000), c7 varchar2(4000), c8 varchar2(4000), c9 varchar2(4000), c10 varchar2(4000),
                c11 varchar2(4000), c12 varchar2(4000), c13 varchar2(4000), c14 varchar2(4000), c15 varchar2(4000),
                c16 varchar2(4000), c17 varchar2(4000), c18 varchar2(4000), c19 varchar2(4000), c20 varchar2(4000),
                c21 varchar2(4000), c22 varchar2(4000), c23 varchar2(4000), c24 varchar2(4000), c25 varchar2(4000),
                c26 varchar2(4000), c27 varchar2(4000), c28 varchar2(4000), c29 varchar2(4000), c30 varchar2(4000),
                c31 varchar2(4000), c32 varchar2(4000), c33 varchar2(4000), c34 varchar2(4000), c35 varchar2(4000),
                c36 varchar2(4000), c37 varchar2(4000), c38 varchar2(4000), c39 varchar2(4000), c40 varchar2(4000),
                c41 varchar2(4000), c42 varchar2(4000), c43 varchar2(4000), c44 varchar2(4000), c45 varchar2(4000),
                c46 varchar2(4000), c47 varchar2(4000), c48 varchar2(4000), c49 varchar2(4000), c50 varchar2(4000)
            )';
    end if;
end;
    """,
    """
declare
    table_exists pls_integer;
begin
    select count(*)
    into table_exists
    from all_tables
    where table_name in ('DDIFF_DIFFS_')
    ;
    if 0 = table_exists then
        execute immediate '
            create table ddiff_diffs_(
                cfg varchar2(4000),
                spec varchar2(4000),
                run number,
                c1 varchar2(4000), c2 varchar2(4000), c3 varchar2(4000), c4 varchar2(4000), c5 varchar2(4000),
                c6 varchar2(4000), c7 varchar2(4000), c8 varchar2(4000), c9 varchar2(4000), c10 varchar2(4000),
                c11 varchar2(4000), c12 varchar2(4000), c13 varchar2(4000), c14 varchar2(4000), c15 varchar2(4000),
                c16 varchar2(4000), c17 varchar2(4000), c18 varchar2(4000), c19 varchar2(4000), c20 varchar2(4000),
                c21 varchar2(4000), c22 varchar2(4000), c23 varchar2(4000), c24 varchar2(4000), c25 varchar2(4000),
                c26 varchar2(4000), c27 varchar2(4000), c28 varchar2(4000), c29 varchar2(4000), c30 varchar2(4000),
                c31 varchar2(4000), c32 varchar2(4000), c33 varchar2(4000), c34 varchar2(4000), c35 varchar2(4000),
                c36 varchar2(4000), c37 varchar2(4000), c38 varchar2(4000), c39 varchar2(4000), c40 varchar2(4000),
                c41 varchar2(4000), c42 varchar2(4000), c43 varchar2(4000), c44 varchar2(4000), c45 varchar2(4000),
                c46 varchar2(4000), c47 varchar2(4000), c48 varchar2(4000), c49 varchar2(4000), c50 varchar2(4000),
                c51 varchar2(4000), c52 varchar2(4000), c53 varchar2(4000), c54 varchar2(4000), c55 varchar2(4000),
                c56 varchar2(4000), c57 varchar2(4000), c58 varchar2(4000), c59 varchar2(4000), c60 varchar2(4000),
                c61 varchar2(4000), c62 varchar2(4000), c63 varchar2(4000), c64 varchar2(4000), c65 varchar2(4000),
                c66 varchar2(4000), c67 varchar2(4000), c68 varchar2(4000), c69 varchar2(4000), c70 varchar2(4000),
                c71 varchar2(4000), c72 varchar2(4000), c73 varchar2(4000), c74 varchar2(4000), c75 varchar2(4000),
                c76 varchar2(4000), c77 varchar2(4000), c78 varchar2(4000), c79 varchar2(4000), c80 varchar2(4000),
                c81 varchar2(4000), c82 varchar2(4000), c83 varchar2(4000), c84 varchar2(4000), c85 varchar2(4000),
                c86 varchar2(4000), c87 varchar2(4000), c88 varchar2(4000), c89 varchar2(4000), c90 varchar2(4000),
                c91 varchar2(4000), c92 varchar2(4000), c93 varchar2(4000), c94 varchar2(4000), c95 varchar2(4000),
                c96 varchar2(4000), c97 varchar2(4000), c98 varchar2(4000), c99 varchar2(4000), c100 varchar2(4000)
            )';
    end if;
end;
    """
]
