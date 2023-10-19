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
        "source": "sqlite-source",
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
        # how many most recent loads preserved in ida tables
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
    "csv_test_test": {
        "source": "sqlite-source",
        "file": "test.csv",
        #
        # statement to insert data into user defined table
        #
        "insert_statement": "insert into dput_test (code, name, alpha2, alpha3) values (?, ?, ?, ?)",
        #
        # tuple of values to insert with the insert statement
        #
        "insert_values": lambda row: (row[3], row[0], row[1], row[2]),
        "process_statements": ["delete from ida where iload = ?"]
    },
    "json_ida_test": {
        "source": "sqlite-source",
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
            where iload = ?
                and (c1 is null or c2 is null or c3 is null or c4 is null)
            """,
            """
            update ida_lines set
                istat = 2,
                ierrm = trim(ierrm || ' Not ALPHA2 code.')
            where iload = ?
                and length(c3) != 2
            """,
            """
            update ida_lines set
                istat = 2,
                ierrm = trim(ierrm || ' Not ALPHA3 code.')
            where iload = ?
                and length(c4) != 3
            """,
        ],
        "process_statements": ["delete from ida where iload = ?"]
    },
    "json_test_test": {
        "source": "sqlite-source",
        "coding": "UTF-8",
        "file": "test.json",
        "insert_statement": "insert into dput_test (code, name, alpha2, alpha3) values (?, ?, ?, ?)",
        "insert_values": lambda row: (row["code"], row["name"], row["alpha2"], row["alpha3"]),
        "process_statements": ["delete from ida where iload = ?"]
    },
    "xlsx_ida_test": {
        "source": "sqlite-source",
        "file": "test.xlsx",
        "process_statements": ["delete from ida where iload = ?"]
    },
    "xlsx_test_test": {
        "source": "sqlite-source",
        "file": "test.xlsx",
        "insert_statement": "insert into dput_test (code, name, alpha2, alpha3) values (?, ?, ?, ?)",
        "insert_values": lambda row: (row[3], row[0], row[1], row[2]),
        "process_statements": ["delete from ida where iload = ?"]
    },
    "csv_test_error": {
        "source": "sqlite-source",
        "file": "test.csv",
        "insert_statement": "insert into dput_test (code, name, alpha2, alpha3) values (?, ?, ?, ?)",
        "insert_values": lambda row: (row[3], row[0], row[1], row[2]),
        "process_statements": ["update ida set istat = 2, imess = 'Just testing' where iload = ?"]
    },
}


sources["sqlite-source"]["setup"] = sources["sqlite-source"].get("setup", []) + [
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
    "PRAGMA foreign_keys = ON",
    """
create table if not exists dput_test (
    code varchar(3) not null,
    name varchar(50) not null,
    alpha2 char(2),
    alpha3 char(3)
)
    """
]

sources["sqlite-source"]["upset"] = sources["sqlite-source"].get("upset", []) + [
    "drop table if exists dput_test"
]