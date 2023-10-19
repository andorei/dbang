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
        "source": "mysql-source",
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
        #
        # optionally process validated data
        #
        "process_statements": [
            # just teardown
            "delete from ida where iload = %s"
        ]
    },
    "csv_test_test": {
        "source": "mysql-source",
        "file": "test.csv",
        #
        # statement to insert data into user defined table
        #
        "insert_statements": "insert into dput_test (code, name, alpha2, alpha3) values (%s, %s, %s, %s)",
        #
        # tuple of values to insert with the insert statements
        #
        "insert_values": lambda row: (row[3], row[0], row[1], row[2]),
        "process_statements": ["delete from ida where iload = %s"]
    },
    "json_ida_test": {
        "source": "mysql-source",
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
            where iload = %s
                and (c1 is null or c2 is null or c3 is null or c4 is null)
            """,
            """
            update ida_lines set
                istat = 2,
                ierrm = trim(ierrm || ' Not ALPHA2 code.')
            where iload = %s
                and length(c3) != 2
            """,
            """
            update ida_lines set
                istat = 2,
                ierrm = trim(ierrm || ' Not ALPHA3 code.')
            where iload = %s
                and length(c4) != 3
            """,
        ],
        "process_statements": ["delete from ida where iload = %s"]
    },
    "json_test_test": {
        "source": "mysql-source",
        "coding": "UTF-8",
        "file": "test.json",
        "insert_statement": "insert into dput_test (code, name, alpha2, alpha3) values (%s, %s, %s, %s)",
        "insert_values": lambda row: (row["code"], row["name"], row["alpha2"], row["alpha3"]),
        "process_statements": ["delete from ida where iload = %s"]
    },
    "xlsx_ida_test": {
        "source": "mysql-source",
        "file": "test.xlsx",
        "process_statements": ["delete from ida where iload = %s"]
    },
    "xlsx_test_test": {
        "source": "mysql-source",
        "file": "test.xlsx",
        "insert_statement": "insert into dput_test (code, name, alpha2, alpha3) values (%s, %s, %s, %s)",
        "insert_values": lambda row: (row[3], row[0], row[1], row[2]),
        "process_statements": ["delete from ida where iload = %s"]
    },
    "csv_test_error": {
        "source": "mysql-source",
        "file": "test.csv",
        "insert_statement": "insert into dput_test (code, name, alpha2, alpha3) values (%s, %s, %s, %s)",
        "insert_values": lambda row: (row[3], row[0], row[1], row[2]),
        "process_statements": ["update ida set istat = 2, imess = 'Just testing' where iload = %s"]
    },
}


sources["mysql-source"]["setup"] = sources['mysql-source'].get('setup', []) + [
    """
create table if not exists ida (
    iload int not null auto_increment,
    idate timestamp not null default current_timestamp,
    istat smallint not null default 0,
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
    ierrm varchar(4000) null,
    c1 text, c2 text, c3 text, c4 text, c5 text,
    c6 text, c7 text, c8 text, c9 text, c10 text,
    c11 text, c12 text, c13 text, c14 text, c15 text,
    c16 text, c17 text, c18 text, c19 text, c20 text,
    c21 text, c22 text, c23 text, c24 text, c25 text,
    c26 text, c27 text, c28 text, c29 text, c30 text,
    c31 text, c32 text, c33 text, c34 text, c35 text,
    c36 text, c37 text, c38 text, c39 text, c40 text,
    c41 text, c42 text, c43 text, c44 text, c45 text,
    c46 text, c47 text, c48 text, c49 text, c50 text,
    c51 text, c52 text, c53 text, c54 text, c55 text,
    c56 text, c57 text, c58 text, c59 text, c60 text,
    c61 text, c62 text, c63 text, c64 text, c65 text,
    c66 text, c67 text, c68 text, c69 text, c70 text,
    c71 text, c72 text, c73 text, c74 text, c75 text,
    c76 text, c77 text, c78 text, c79 text, c80 text,
    c81 text, c82 text, c83 text, c84 text, c85 text,
    c86 text, c87 text, c88 text, c89 text, c90 text,
    c91 text, c92 text, c93 text, c94 text, c95 text,
    c96 text, c97 text, c98 text, c99 text, c100 text,
    primary key (iload, iline),
    foreign key (iload) references ida(iload) on delete cascade
)
    """,
    """
create table if not exists dput_test (
    code varchar(3) not null,
    name varchar(50) not null,
    alpha2 char(2),
    alpha3 char(3)
)
    """
]

sources["mysql-source"]["upset"] = sources["mysql-source"].get("upset", []) + [
    "drop table if exists dput_test"
]
