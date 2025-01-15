import os
import sys

from sources import sources

#
# Run sanity tests with command line
#     dput.py conf/dput-test-sqlite.py all
# and see log file in log/ directory.
#

#
# SETTINGS USED BY dput
#
# defaults to current working directory
IN_DIR = os.path.join(os.path.dirname(__file__), '..', 'in')
# defaults to False
DEBUGGING = True
# defaults to False
LOGGING = True
# defaults to current working directory
LOG_DIR = os.path.join(os.path.dirname(__file__), '..', 'log')
# output files' encoding defaults to OS locale encoding
ENCODING = 'cp1251'
# defaults to 'excel'
#CSV_DIALECT = 'excel'
# defaults to the dialect delimiter
CSV_DELIMITER = ';'
# number of loads preserved per spec defaults to 10
#PRESERVE_N_LOADS = 10
# data source
SOURCE = "sqlite-source"

#
# SETTINGS USED IN specs
#

# special_ida_test
FIELD_NAMES = ['Code', 'Name']
FIELD_INDEXES = []
FIELD_SEP = ';'

def special_01_ida(line_no, line):
    """
    line_no - number of line in individual file
    line    - line content
    """
    global FIELD_NAMES, FIELD_INDEXES, FIELD_SEP
    row = None
    if line_no == 1:
        # Delimiter Character
        FIELD_SEP = line.split('=')[1].strip()
    elif line_no == 2:
        # Field Names
        field_names = line.rstrip('\n').split(sep=FIELD_SEP)
        FIELD_INDEXES = []
        for field_name in FIELD_NAMES:
            FIELD_INDEXES.append(field_names.index(field_name))
    else:
        # Data
        row = line.rstrip('\n').split(sep=FIELD_SEP)
        row = [row[idx] for idx in FIELD_INDEXES]
    return row


def special_03_ida(line):
    """
    line    - line content, e.g. AFAFG004Afghanistan
    """
    return (line[0:2], line[2:5], line[5:8], line[8:].strip())


specs = {
    "csv_ida_test": {
        # optional tags to use in command line instead of spec name
        "tags": ['csv', 'ida'],
        # database to load data into defaults to SOURCE (if set)
        #"source": SOURCE,
        # file to load; should be specified here or/and on command line
        "file": "test.csv",
        # optional args go to columns ida.arg1 ... arg9
        #"args": ['one', 'two', '3', '4', '5', '6', '7', '8', '9'],
        # load data regardless file(s) timestamp(s)
        #"force": False,
        #
        # the following parameters default to the global ones
        #"encoding": ENCODING,
        #"csv_dialect": CSV_DIALECT,
        #"csv_delimiter": CSV_DELIMITER,
        #"skip_lines": 0,
        #"preserve_n_loads": PRESERVE_N_LOADS,
        #
        # optionally initialize data loading
        #"setup": [],
        #
        # optionally validate loaded data
        "validate_actions": [
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
        # optionally process validated data
        "process_actions": [
            # just teardown
            "delete from ida where iload = ?"
        ],
        # optionally finalize data loading
        #"upset": []
    },
    "selected_ida_test": {
        "tags": ['selected', 'csv', 'ida'],
        "file": "test.csv",
        "insert_data": lambda row: (row[3], row[0]) if row[0][0] in 'AEIOU' else None,
        "validate_actions": [
            """
            update ida_lines set
                istat = 2,
                ierrm = 'Not a vowel.'
            where iload = ?
                and substr(c2, 1, 1) not in ('A', 'E', 'I', 'O', 'U')
            """
        ],
        "process_actions": ["delete from ida where iload = ?"]
    },
    "--commented_out": {
        "tags": ['csv', 'ida', 'commented'],
        "file": "test.csv",
        "process_actions": ["delete from ida where iload = ?"]
    },
    "csv_skip_test": {
        "tags": ['csv', 'ida', 'skip_lines'],
        "file": "test.csv",
        "skip_lines": 1,
        "process_actions": ["delete from ida where iload = ?"]
    },
    "--csv_proc_test": {  # there are no stored procedures in sqlite
        "tags": ['csv'],
        "file": "test.csv",
        "validate_actions": 'call validate_dput_test(?)',
        "process_actions": 'call process_dput_test(?)'
    },
    "csv_test_test": {
        "tags": ['csv'],
        "source": "sqlite-source",
        "file": "test.csv",
        "args": ['one', 'two'],
        # statement to insert data into user defined table
        "insert_actions": "insert into dput_test (code, name, alpha2, alpha3) values (?, ?, ?, ?)",
        # row to insert with the above insert statement
        "insert_data": lambda row: (row[3], row[0], row[1], row[2]),
        "process_actions": "delete from ida where iload = ?"
    },
    "csv_parts_test": {
        "tags": ['csv', 'ida'],
        "file": "test_000???.csv",
        "process_actions": "delete from ida where iload = ?"
    },
    "json_ida_test": {
        "tags": ['ida'],
        "encoding": "UTF-8",
        "file": "test.json",
        # row to insert into ida_lines table
        "insert_data": lambda row: (row["code"], row["name"], row.get("alpha2"), row.get("alpha3")),
        "validate_actions": [
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
        "process_actions": "delete from ida where iload = ?"
    },
    "json_test_test": {
        "encoding": "UTF-8",
        "file": "test.json",
        "insert_actions": "insert into dput_test (code, name, alpha2, alpha3) values (?, ?, ?, ?)",
        "insert_data": lambda row: (row["code"], row["name"], row["alpha2"], row["alpha3"]),
        "process_actions": "delete from ida where iload = ?"
    },
    "json_parts_test": {
        "tags": ['ida'],
        "file": "test_000???.json",
        "insert_data": lambda row: (row["code"], row["name"], row.get("alpha2"), row.get("alpha3")),
        "process_actions": ["delete from ida where iload = ?"]
    },
    "xlsx_ida_test": {
        "tags": ['ida'],
        "file": "test.xlsx",
        "process_actions": "delete from ida where iload = ?"
    },
    "xlsx_skip_test": {
        "tags": ['ida', 'skip_lines'],
        "file": "test.xlsx",
        "skip_lines": 3,
        "process_actions": "delete from ida where iload = ?"
    },
    "xlsx_test_test": {
        "file": "test.xlsx",
        "insert_actions": "insert into dput_test (code, name, alpha2, alpha3) values (?, ?, ?, ?)",
        "insert_data": lambda row: (row[3], row[0], row[1], row[2]),
        "process_actions": "delete from ida where iload = ?"
    },
    "xlsx_parts_test": {
        "tags": ['ida'],
        "file": "test_000???.xlsx",
        "process_actions": "delete from ida where iload = ?"
    },
    "csv_test_error": {
        "tags": ['csv'],
        "file": "test.csv",
        "insert_actions": "insert into dput_test (code, name, alpha2, alpha3) values (?, ?, ?, ?)",
        "insert_data": lambda row: (row[3], row[0], row[1], row[2]),
        "process_actions": "update ida set istat = 2, imess = 'Just testing' where iload = ?"
    },
    "nested_00_ida": {
        "tags": ['ida', 'csv', 'nested'],
        "file": "test_nested_00.csv",
        "insert_data": \
            lambda row: [(row[0], n) for n in row[1].split(',')] if row[1] else [],
        "process_actions": "delete from ida where iload = ?"
    },
    "nested_01_ida": {
        "tags": ['ida', 'json', 'nested'],
        "file": "test_nested_01.json",
        "encoding": "UTF-8",
        "insert_data": [
            lambda row: (row['region'], len(row['countries'])),
            lambda row: [(n['code'], n['name'], n['alpha2'], n['alpha3']) for n in row['countries']] if row['countries'] else []
        ],
        "process_actions": "delete from ida where iload = ?"
    },
    "nested_02_ida": {
        "tags": ['ida', 'json', 'nested'],
        "file": "test_nested_02.json",
        "encoding": "UTF-8",
        "insert_data": [
            lambda row: (row['category'], row['doc'], len(row['en_fr']), len(row['en_fr_ru'])),
            lambda row: [(r['en'], r['fr']) for r in row['en_fr']] if row['en_fr'] else [],
            lambda row: row['en_fr_ru']
        ],
        "process_actions": "delete from ida where iload = ?"
    },
    "nested_01_test": {
        "tags": ['json', 'nested'],
        "file": "test_nested_01.json",
        "encoding": "UTF-8",
        "insert_actions": [
            "insert into test_region (region, contains) values (?, ?)",
            "insert into test_countries (region, code, name) values (?, ?, ?)"
        ],
        "insert_data": [
            lambda row: (row['region'], len(row['countries'])),
            lambda row: [(row['region'], n['code'], n['name']) for n in row['countries']] if row['countries'] else []
        ],
        "validate_actions": """
            update ida set istat = 2
            where iload = ?
                and exists (
                    select 1
                    from test_region r
                    where contains != (
                            select count(*)
                            from test_countries c
                            where r.region = c.region
                        )
                )
            """,
        "process_actions": [
            "delete from ida where iload = ?",
            "delete from test_countries where ? is not null",
            "delete from test_region where ? is not null"
        ]
    },
    "nested_01_keygen": {
        "tags": ['json', 'nested'],
        "file": "test_nested_01.json",
        "encoding": "UTF-8",
        "insert_actions": [
            "insert into test_region (region_id, region, contains) values (?, ?, ?)",
            "insert into test_countries (region_id, code, name) values (?, ?, ?)"
        ],
        "insert_data": [
            lambda iload, iline, row: (iload * 1000 + iline, row['region'], len(row['countries'])),
            lambda iload, iline, row: [(iload * 1000 + iline, n['code'], n['name']) for n in row['countries']] if row['countries'] else []
        ],
        "validate_actions": """
            update ida set istat = 2 
            where iload = ?
                and exists (
                    select 1
                    from test_region r
                    where contains != (
                            select count(*)
                            from test_countries c
                            where r.region_id = c.region_id
                        )
                )
            """,
        "process_actions": [
            "delete from ida where iload = ?",
            "delete from test_countries where ? is not null",
            "delete from test_region where ? is not null"
        ]
    },
    "flatten_ida_test": {
        "tags": ['json', 'filter', 'flatten'],
        "file": "test_nested_01.json",
        "encoding": "UTF-8",
        "insert_data": lambda row: [(row['region'], n['code'], n['name']) for n in row['countries']] if row['countries'] else [],
        "process_actions": "delete from ida where iload = ?"
    },
    "special_01_ida": {
        "tags": ['pass_lines', 'ida'],
        "file": "test_special.csv",
        # just pass lines of the file to insert_data function
        "pass_lines": True,
        "insert_data": special_01_ida,
        "process_actions": "delete from ida where iload = ?"
    },
    "special_02_ida": {
        "tags": ['pass_lines', 'ida'],
        "file": "test_special.csv",
        "pass_lines": True,
        "process_actions": "delete from ida where iload = ?"
    },
    "special_03_ida": {
        "tags": ['pass_lines', 'ida'],
        "file": "test_special.dat",
        "pass_lines": True,
        "insert_data": special_03_ida,
        "process_actions": "delete from ida where iload = ?"
    },
    "zipped_ida_test": {
        "tags": ['zipped', 'ida'],
        "file": "test_zip.zip",
        "process_actions": "delete from ida where iload = ?"
    },
    "setup_upset_test": {
        "tags": ['csv', 'ida', 'setup', 'upset'],
        "file": "test.csv",
        "setup": [
            """
            drop table if exists target_table
            """,
            """
            create table if not exists target_table (
                code char(3),
                name varchar(100),
                alpha2 char(2),
                alpha3 char(3)
            )
            """
        ],
        "validate_actions": [
            """
            update ida_lines set
                istat = 2,
                ierrm = trim(ierrm || ' Empty field.')
            where iload = ?
                and (c1 is null or c2 is null or c3 is null or c4 is null)
            """
        ],
        "process_actions": [
            """
            insert into target_table (
                code,
                name,
                alpha2,
                alpha3
            )
            select c4 code,
                c1 name,
                c2 alpha2,
                c3 alpha3
            from ida_lines
            where iload = ?
            """,
            """
            delete from ida where iload = ?
            """
        ],
        "upset": [
            """
            drop table if exists target_table
            """
        ]
    },
}

sources["sqlite-source"]["setup"] = sources["sqlite-source"].get("setup", []) + [
    """
    drop table if exists dput_test
    """,
    """
create table if not exists dput_test (
    code varchar(3) not null,
    name varchar(50) not null,
    alpha2 char(2),
    alpha3 char(3)
)
    """,
    """
    drop table if exists test_region
    """,
    """
create table if not exists test_region (
    region varchar(50) not null,
    contains smallint not null,
    region_id int
)
    """,
    """
    drop table if exists test_countries
    """,
    """
create table if not exists test_countries (
    code varchar(3) not null,
    name varchar(50) not null,
    region varchar(50),
    region_id int
)
    """
]

sources["sqlite-source"]["upset"] = sources["sqlite-source"].get("upset", []) + [
    "drop table if exists dput_test",
    "drop table if exists test_countries",
    "drop table if exists test_region"
]