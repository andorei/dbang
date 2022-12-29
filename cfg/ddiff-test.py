import os
import sys

#
# data sources
#
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

#
# dot-source keeps intermediate data in ddiff_ table (see DDL below)
#
sources['.'] = sources['sqlite-source']
#sources['.'] = sources['postgres-source']
#sources['.'] = sources['oracle-source']
# Currently you can't use MySQL as dot-source. Only MySQL 8.0.31 and higher
# versions support EXCEPT clause which is used in queries with ddiff_ table.

#
# next two sources are those with data to test for discrepancies
#
sources["ONE"] = sources["."]
sources["TWO"] = sources["."]

#
# tests to detect data discrepancies between the two data sources
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
    "current_date": {
        "sources": ["ONE", "TWO"],
        "pk": ["today"],
        "queries": [
            "select current_date as today from dual",
            "select current_date as today from dual"
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
                select 1 c1, 2 c2, 3 c3, 4 c4, 5 c5
                from dual
                where 1 = {{argrows[0][0]}}
                """,
                """
                select 1 c1, 2 c2, 3 c3, 4 c4, 6 c5
                from dual
                where 1 = {{argrows[0][0]}}
                """
            ],
            # level 3
            "nested": {
                "pk": ["c1", "c2", "c3"],
                "queries": [
                    """
                    select 1 c1, 2 c2, 3 c3, 4 c4, 5 c5
                    from dual
                    where 1 = {{argrows[0][0]}}
                        and 2 = {{argrows[0][1]}}
                    """,
                    """
                    select 1 c1, 2 c2, 3 c3, 4 c4, 6 c5
                    from dual
                    where 1 = {{argrows[0][0]}}
                        and 2 = {{argrows[0][1]}}
                    """
               ]
            }
        }
    },
}

sources['sqlite-source']['init'] = [
    """
create table if not exists ddiff_(
    run bigint,
    test varchar(30),
    source varchar(30),
    c1 text, c2 text, c3 text, c4 text, c5 text, c6 text, c7 text, c8 text, c9 text, c10 text,
    c11 text, c12 text, c13 text, c14 text, c15 text, c16 text, c17 text, c18 text, c19 text, c20 text,
    c21 text, c22 text, c23 text, c24 text, c25 text, c26 text, c27 text, c28 text, c29 text, c30 text,
    c31 text, c32 text, c33 text, c34 text, c35 text, c36 text, c37 text, c38 text, c39 text, c40 text,
    c41 text, c42 text, c43 text, c44 text, c45 text, c46 text, c47 text, c48 text, c49 text, c50 text
)
    """,
    "create table if not exists dual as select 'X' as dummy"
]

sources['postgres-source']['init'] = [
    """
create table if not exists ddiff_(
    run bigint,
    test varchar(30),
    source varchar(30),
    c1 text, c2 text, c3 text, c4 text, c5 text, c6 text, c7 text, c8 text, c9 text, c10 text,
    c11 text, c12 text, c13 text, c14 text, c15 text, c16 text, c17 text, c18 text, c19 text, c20 text,
    c21 text, c22 text, c23 text, c24 text, c25 text, c26 text, c27 text, c28 text, c29 text, c30 text,
    c31 text, c32 text, c33 text, c34 text, c35 text, c36 text, c37 text, c38 text, c39 text, c40 text,
    c41 text, c42 text, c43 text, c44 text, c45 text, c46 text, c47 text, c48 text, c49 text, c50 text
)
    """,
    "create table if not exists dual as select 'X' as dummy"
]

sources['oracle-source']['init'] = [
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
                run number,
                test varchar2(30),
                source varchar2(30),
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
    """
]
