import os
import sys

#
# Run sanity test with command line
#
#     dput.py dput-test countries_sqlite specs/countries.csv
#
# To initialize and sanity-test uploading into Postgres or Oracle databases 
# adjust database connection strings below as necessary and run
#
#     dput.py dput-test test_csv_postgres test.csv
#
# or
#
#     dput.py dput-test test_csv_oracle test.csv
#

# MANDATORY constants used by dput.py
CSV_ENCODING = 'cp1251'
CSV_DIALECT = 'excel'
CSV_DELIMITER = ';'
CSV_QUOTECHAR = "\""

IN_DIR = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), 'in')

# Optional constants used in specs below


# Databses to load data into from csv files; see spec below.
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
    }
}

specs = {
    "test_csv_sqlite": {
        #
        # database to load data into from csv file
        #
        "source": "sqlite-source",
        #
        # csv parameters default to the global ones
        #
        #"encoding": "cp1251",
        #"dialect": "excel",
        #"delimiter": ";",
        #"quotechar": "\""
        #
        # optionally validate loaded data
        #
        "validate_statements": [
            """
            update ida_lines set
                istat = 2,
                ierrm = trim(ierrm || ' Empty field.')
            where iload = ?
                and (c1 is null or c2 is null or c3 is null or c4 is null)
            """,
            """
            update ida_lines set
                istat = 2,
                ierrm = trim(ierrm || ' Not ALPHA2 code.')
            where iload = ?
                and length(c2) != 2
            """,
            """
            update ida_lines set
                istat = 2,
                ierrm = trim(ierrm || ' Not ALPHA3 code.')
            where iload = ?
                and length(c3) != 3
            """,
        ],
        #
        # optionally process validated data
        #
        "process_statements": [
            # just teardown
            "delete from ida where iload = ?"
        ]
    },
    "test_csv_postgres": {
        "source": "postgres-source",
        "validate_statements": [
            """
            update ida_lines set
                istat = 2,
                ierrm = trim(ierrm || ' Empty field.')
            where iload = %s
                and (c1 is null or c2 is null or c3 is null or c4 is null)
            """,
            """
            update ida_lines set
                istat = 2,
                ierrm = trim(ierrm || ' Not ALPHA2 code.')
            where iload = %s
                and length(c2) != 2
            """,
            """
            update ida_lines set
                istat = 2,
                ierrm = trim(ierrm || ' Not ALPHA3 code.')
            where iload = %s
                and length(c3) != 3
            """,
        ],
        "process_statements": [
            # just teardown
            "delete from ida where iload = %s"
        ]
    },
    "test_csv_oracle": {
        "source": "oracle-source",
        "validate_statements": [
            """
            update ida_lines set
                istat = 2,
                ierrm = trim(ierrm || ' Empty field.')
            where iload = :1
                and (c1 is null or c2 is null or c3 is null or c4 is null)
            """,
            """
            update ida_lines set
                istat = 2,
                ierrm = trim(ierrm || ' Not ALPHA2 code.')
            where iload = :1
                and length(c2) != 2
            """,
            """
            update ida_lines set
                istat = 2,
                ierrm = trim(ierrm || ' Not ALPHA3 code.')
            where iload = :1
                and length(c3) != 3
            """,
        ],
        "process_statements": [
            # just teardown
            "delete from ida where iload = :1"
        ]
    }
}


sources["sqlite-source"]["init"] = [
    """
create table if not exists ida (
    iload INTEGER not null PRIMARY KEY,
    idate timestamptz not null default current_timestamp,
    istat smallint not null default 0,
    imess varchar(4000),
    entity varchar(50) not null,
    ifile varchar(256) not null,
    iuser varchar(30)
)
    """,
    """
create table if not exists ida_lines (
    iload int not null,
    iline int not null,
    istat smallint not null default 0,
    ierrm varchar(4000) null,
    c1 varchar(4000), c2 varchar(4000), c3 varchar(4000), c4 varchar(4000), c5 varchar(4000),
    c6 varchar(4000), c7 varchar(4000), c8 varchar(4000), c9 varchar(4000), c10 varchar(4000),
    c11 varchar(4000), c12 varchar(4000), c13 varchar(4000), c14 varchar(4000), c15 varchar(4000),
    c16 varchar(4000), c17 varchar(4000), c18 varchar(4000), c19 varchar(4000), c20 varchar(4000),
    c21 varchar(4000), c22 varchar(4000), c23 varchar(4000), c24 varchar(4000), c25 varchar(4000),
    c26 varchar(4000), c27 varchar(4000), c28 varchar(4000), c29 varchar(4000), c30 varchar(4000),
    c31 varchar(4000), c32 varchar(4000), c33 varchar(4000), c34 varchar(4000), c35 varchar(4000),
    c36 varchar(4000), c37 varchar(4000), c38 varchar(4000), c39 varchar(4000), c40 varchar(4000),
    c41 varchar(4000), c42 varchar(4000), c43 varchar(4000), c44 varchar(4000), c45 varchar(4000),
    c46 varchar(4000), c47 varchar(4000), c48 varchar(4000), c49 varchar(4000), c50 varchar(4000),
    c51 varchar(4000), c52 varchar(4000), c53 varchar(4000), c54 varchar(4000), c55 varchar(4000),
    c56 varchar(4000), c57 varchar(4000), c58 varchar(4000), c59 varchar(4000), c60 varchar(4000),
    c61 varchar(4000), c62 varchar(4000), c63 varchar(4000), c64 varchar(4000), c65 varchar(4000),
    c66 varchar(4000), c67 varchar(4000), c68 varchar(4000), c69 varchar(4000), c70 varchar(4000),
    c71 varchar(4000), c72 varchar(4000), c73 varchar(4000), c74 varchar(4000), c75 varchar(4000),
    c76 varchar(4000), c77 varchar(4000), c78 varchar(4000), c79 varchar(4000), c80 varchar(4000),
    c81 varchar(4000), c82 varchar(4000), c83 varchar(4000), c84 varchar(4000), c85 varchar(4000),
    c86 varchar(4000), c87 varchar(4000), c88 varchar(4000), c89 varchar(4000), c90 varchar(4000),
    c91 varchar(4000), c92 varchar(4000), c93 varchar(4000), c94 varchar(4000), c95 varchar(4000),
    c96 varchar(4000), c97 varchar(4000), c98 varchar(4000), c99 varchar(4000), c100 varchar(4000),
    primary key (iload, iline),
    foreign key (iload) references ida(iload) on delete cascade
)
    """,
    "PRAGMA foreign_keys = ON"
]

sources["postgres-source"]["init"] = [
    """
create table if not exists ida (
    iload serial4 not null,
    idate timestamptz not null default now(),
    istat int2 not null default 0,
    imess varchar(4000),
    entity varchar(50) not null,
    ifile varchar(256) not null,
    iuser varchar(30),
    primary key (iload)
)
    """,
    """
create table if not exists ida_lines (
    iload int not null,
    iline int not null,
    istat smallint not null default 0,
    ierrm varchar(4000),
    c1 varchar(4000), c2 varchar(4000), c3 varchar(4000), c4 varchar(4000), c5 varchar(4000),
    c6 varchar(4000), c7 varchar(4000), c8 varchar(4000), c9 varchar(4000), c10 varchar(4000),
    c11 varchar(4000), c12 varchar(4000), c13 varchar(4000), c14 varchar(4000), c15 varchar(4000),
    c16 varchar(4000), c17 varchar(4000), c18 varchar(4000), c19 varchar(4000), c20 varchar(4000),
    c21 varchar(4000), c22 varchar(4000), c23 varchar(4000), c24 varchar(4000), c25 varchar(4000),
    c26 varchar(4000), c27 varchar(4000), c28 varchar(4000), c29 varchar(4000), c30 varchar(4000),
    c31 varchar(4000), c32 varchar(4000), c33 varchar(4000), c34 varchar(4000), c35 varchar(4000),
    c36 varchar(4000), c37 varchar(4000), c38 varchar(4000), c39 varchar(4000), c40 varchar(4000),
    c41 varchar(4000), c42 varchar(4000), c43 varchar(4000), c44 varchar(4000), c45 varchar(4000),
    c46 varchar(4000), c47 varchar(4000), c48 varchar(4000), c49 varchar(4000), c50 varchar(4000),
    c51 varchar(4000), c52 varchar(4000), c53 varchar(4000), c54 varchar(4000), c55 varchar(4000),
    c56 varchar(4000), c57 varchar(4000), c58 varchar(4000), c59 varchar(4000), c60 varchar(4000),
    c61 varchar(4000), c62 varchar(4000), c63 varchar(4000), c64 varchar(4000), c65 varchar(4000),
    c66 varchar(4000), c67 varchar(4000), c68 varchar(4000), c69 varchar(4000), c70 varchar(4000),
    c71 varchar(4000), c72 varchar(4000), c73 varchar(4000), c74 varchar(4000), c75 varchar(4000),
    c76 varchar(4000), c77 varchar(4000), c78 varchar(4000), c79 varchar(4000), c80 varchar(4000),
    c81 varchar(4000), c82 varchar(4000), c83 varchar(4000), c84 varchar(4000), c85 varchar(4000),
    c86 varchar(4000), c87 varchar(4000), c88 varchar(4000), c89 varchar(4000), c90 varchar(4000),
    c91 varchar(4000), c92 varchar(4000), c93 varchar(4000), c94 varchar(4000), c95 varchar(4000),
    c96 varchar(4000), c97 varchar(4000), c98 varchar(4000), c99 varchar(4000), c100 varchar(4000),
    primary key (iload, iline),
    foreign key (iload) references ida(iload) on delete cascade
)
    """
]

sources["oracle-source"]["init"] = [
    """
declare
    table_exists pls_integer;
begin
    select count(*)
    into table_exists
    from all_tables
    where table_name in ('IDA', 'IDA_LINES')
    ;
    if 0 = table_exists then
        execute immediate '
            create table ida (
                iload number(9) not null,
                idate timestamp default current_timestamp not null,
                istat number(1) default 0 not null,
                imess varchar2(4000),
                entity varchar2(50) not null,
                ifile varchar2(256) not null,
                iuser varchar2(30),
                primary key (iload)
            )';
        execute immediate '
            create table ida_lines (
                iload number(9) not null,
                iline number(9) not null,
                istat number(1) default 0 not null,
                ierrm varchar2(4000),
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
                c96 varchar2(4000), c97 varchar2(4000), c98 varchar2(4000), c99 varchar2(4000), c100 varchar2(4000),
                primary key (iload, iline),
                foreign key (iload) references ida(iload) on delete cascade
            )';
        execute immediate 'create sequence ida_seq';
    end if;
end;
    """
]
