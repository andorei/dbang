import os
import sys

from sources import sources


#
# Specify MySQL connection details for "mysql-source" in sources.py,
# then run sanity test against MySQL DB with command line
#
#     ddiff.py ddiff-test-mysql
#
# and find test data discrepancies report in out/ddiff-test-mysql.html
#


# MANDATORY CONSTANTS used by ddiff.py

# DB where intermediate data is kept and processed

#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# 1) ddiff uses EXCEPT SQL operator which is available since MySQL v8.0.31
# 2) MySQL v8.1 still has a bug... so use another DB as DDIFF_SOURCE
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

#DDIFF_SOURCE = sources['mysql-source']
DDIFF_SOURCE = sources['sqlite-source']


# OPTIONAL CONSTANTS

# Directory where discrepancies report is saved
#OUT_DIR = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), 'out')

DEBUGGING = True
#LOGSTDOUT = False

# Next two sources are those with data to test for discrepancies
sources["ONE"] = sources["mysql-source"]
sources["TWO"] = sources["mysql-source"]

#
# Tests to detect data discrepancies between the two data sources
# QUERIES IN specs MAY USE FEATURES SPECIFIC TO mysql DATABASE
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

sources['mysql-source']['setup'] = sources['mysql-source'].get('setup', []) + [
    """
create table if not exists ddiff_(
    cfg text,
    spec text,
    run bigint,
    source text,
    c1 text, c2 text, c3 text, c4 text, c5 text, c6 text, c7 text, c8 text, c9 text, c10 text,
    c11 text, c12 text, c13 text, c14 text, c15 text, c16 text, c17 text, c18 text, c19 text, c20 text,
    c21 text, c22 text, c23 text, c24 text, c25 text, c26 text, c27 text, c28 text, c29 text, c30 text,
    c31 text, c32 text, c33 text, c34 text, c35 text, c36 text, c37 text, c38 text, c39 text, c40 text,
    c41 text, c42 text, c43 text, c44 text, c45 text, c46 text, c47 text, c48 text, c49 text, c50 text
)
    """,
    """
create table if not exists ddiff_diffs_(
    cfg text,
    spec text,
    run bigint,
    c1 text, c2 text, c3 text, c4 text, c5 text, c6 text, c7 text, c8 text, c9 text, c10 text,
    c11 text, c12 text, c13 text, c14 text, c15 text, c16 text, c17 text, c18 text, c19 text, c20 text,
    c21 text, c22 text, c23 text, c24 text, c25 text, c26 text, c27 text, c28 text, c29 text, c30 text,
    c31 text, c32 text, c33 text, c34 text, c35 text, c36 text, c37 text, c38 text, c39 text, c40 text,
    c41 text, c42 text, c43 text, c44 text, c45 text, c46 text, c47 text, c48 text, c49 text, c50 text,
    c51 text, c52 text, c53 text, c54 text, c55 text, c56 text, c57 text, c58 text, c59 text, c60 text,
    c61 text, c62 text, c63 text, c64 text, c65 text, c66 text, c67 text, c68 text, c69 text, c70 text,
    c71 text, c72 text, c73 text, c74 text, c75 text, c76 text, c77 text, c78 text, c79 text, c80 text,
    c81 text, c82 text, c83 text, c84 text, c85 text, c86 text, c87 text, c88 text, c89 text, c90 text,
    c91 text, c92 text, c93 text, c94 text, c95 text, c96 text, c97 text, c98 text, c99 text, c100 text
)
    """
]
