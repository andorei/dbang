import os
import sys

from sources import sources


#
# Run sanity tests with command lines
#
#     dput.py dput-test-sqlite
#
# and see log files in/test.*.log
#
# To initialize and sanity-test uploading into Postgres/Oracle/MySQL databases 
# adjust database connection string in sources.py as necessary and run one of
#
#     dput.py dput-test-postgres
#     dput.py dput-test-oracle
#     dput.py dput-test-mysql
#


# MANDATORY constants used by dput.py

ENCODING = 'cp1251'

CSV_DIALECT = 'excel'
CSV_DELIMITER = ';'
CSV_QUOTECHAR = "\""

PRESERVE_N_LOADS = 10


# OPTIONAL CONSTANTS

#IN_DIR = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), 'in')
DEBUGGING = True
#LOGSTDOUT = False


specs = {
    "csv_ida_test": {
        #
        # database to load data into
        #
        "source": "oracle-source",
        #
        # file to load; should be specified here or/and on command line
        #
        "file": "test.csv",
        #
        # the following parameters default to the global ones
        #
        #"encoding": ENCODING,
        #"csv_dialect": CSV_DIALECT,
        #"csv_delimiter": CSV_DELIMITER,
        #"csv_quotechar": CSV_QUOTECHAR,
        #
        # how many last loads preserved in ida tables
        #
        #"preserve_n_loads": PRESERVE_N_LOADS,
        #
        # optionally validate loaded data
        #
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
        #
        # optionally process validated data
        #
        "process_statements": [
            # just teardown
            "delete from ida where iload = :1"
        ]
    },
    "csv_test_test": {
        "source": "oracle-source",
        "file": "test.csv",
        #
        # statement to insert data into user defined table
        #
        "insert_statements": "insert into dput_test (code, name, alpha2, alpha3) values (:1, :2, :3, :4)",
        #
        # tuple of values to insert with the insert statements
        #
        "insert_values": lambda row: (row[3], row[0], row[1], row[2]),
        "process_statements": ["delete from ida where iload = :1"]
    },
    "json_ida_test": {
        "source": "oracle-source",
        "coding": "UTF-8",
        "file": "test.json",
        #
        # tuple of values to insert into ida_lines table
        #
        "insert_values": lambda row: (row["code"], row["name"], row.get("alpha2"), row.get("alpha3")),
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
                and length(c3) != 2
            """,
            """
            update ida_lines set
                istat = 2,
                ierrm = trim(ierrm || ' Not ALPHA3 code.')
            where iload = :1
                and length(c4) != 3
            """,
        ],
        "process_statements": ["delete from ida where iload = :1"]
    },
    "json_test_test": {
        "source": "oracle-source",
        "coding": "UTF-8",
        "file": "test.json",
        "insert_statement": "insert into dput_test (code, name, alpha2, alpha3) values (:1, :2, :3, :4)",
        "insert_values": lambda row: (row["code"], row["name"], row["alpha2"], row["alpha3"]),
        "process_statements": ["delete from ida where iload = :1"]
    },
    "xlsx_ida_test": {
        "source": "oracle-source",
        "file": "test.xlsx",
        "process_statements": ["delete from ida where iload = :1"]
    },
    "xlsx_test_test": {
        "source": "oracle-source",
        "file": "test.xlsx",
        "insert_statement": "insert into dput_test (code, name, alpha2, alpha3) values (:1, :2, :3, :4)",
        "insert_values": lambda row: (row[3], row[0], row[1], row[2]),
        "process_statements": ["delete from ida where iload = :1"]
    },
    "csv_test_error": {
        "source": "oracle-source",
        "file": "test.csv",
        "insert_statement": "insert into dput_test (code, name, alpha2, alpha3) values (:1, :2, :3, :4)",
        "insert_values": lambda row: (row[3], row[0], row[1], row[2]),
        "process_statements": ["update ida set istat = 2, imess = 'Just testing' where iload = :1"]
    },
}


sources["oracle-source"]["setup"] = sources['oracle-source'].get('setup', []) + [
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
    """,
    """
begin
    execute immediate '
create table dput_test (
    code varchar2(3) not null,
    name varchar2(50) not null,
    alpha2 char(2),
    alpha3 char(3)
)';
exception
    when others then
        null;
end;
    """
]

sources["oracle-source"]["upset"] = sources["oracle-source"].get("upset", []) + [
    """
begin
    execute immediate 'drop table dput_test';
exception
    when others then
        null;
end;
    """
]
