import os
import sys

from sources import sources

#
# Run sanity tests with command line
#     dput.py conf/dput-test-postgres.py all
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
SOURCE = "postgres-source"

#
# SETTINGS USED IN specs
#
pass

specs = {
    "csv_ida_test": {
        # optional tags to use in command line instead of spec name
        "tags": ['csv', 'ida'],
        # database to load data into defaults to SOURCE (if set)
        #"source": SOURCE,
        # file to load; should be specified here or/and on command line
        "file": "test.csv",
<<<<<<< HEAD
        # optional args go to columns ida.arg1 ... arg9
=======
        #
        # optional args go to ida.arg1 ... arg9
        #
>>>>>>> 2c0015bc478159487a94de627f47bc7997a032a0
        #"args": ['one', 'two', '3', '4', '5', '6', '7', '8', '9'],
        #
        # the following parameters default to the global ones
        #"encoding": ENCODING,
        #"csv_dialect": CSV_DIALECT,
        #"csv_delimiter": CSV_DELIMITER,
        #"csv_quotechar": CSV_QUOTECHAR,
<<<<<<< HEAD
        #"skip_lines": 0,
        #"preserve_n_loads": PRESERVE_N_LOADS,
        #
        # optionally validate loaded data
        "validate_actions": [
=======
        #
        # how many lines to skip at the beginning of the file
        #
        #"skip_header": 0,
        #
        # how many most recent loads preserved in ida tables
        #
        #"preserve_n_loads": PRESERVE_N_LOADS,
        #
        # optionally validate loaded data
        #
        "validation_actions": [
>>>>>>> 2c0015bc478159487a94de627f47bc7997a032a0
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
        # optionally process validated data
<<<<<<< HEAD
=======
        #
>>>>>>> 2c0015bc478159487a94de627f47bc7997a032a0
        "process_actions": [
            # just teardown
            "delete from ida where iload = %s"
        ]
    },
    "csv_skip_test": {
        "tags": ['csv', 'ida', 'skip_lines'],
        "file": "test.csv",
<<<<<<< HEAD
        "skip_lines": 1,
        "process_actions": "delete from ida where iload = %s"
=======
        "skip_header": 1,
        "process_actions": ["delete from ida where iload = %s"]
>>>>>>> 2c0015bc478159487a94de627f47bc7997a032a0
    },
    "csv_proc_test": {
        "tags": ['csv'],
        "file": "test.csv",
<<<<<<< HEAD
        "validate_actions": 'call validate_dput_test(%s)',
        "process_actions": 'call process_dput_test(%s)'
=======
        "validation_actions": ['call validate_dput_test(%s)'],
        "process_actions": ['call process_dput_test(%s)']
>>>>>>> 2c0015bc478159487a94de627f47bc7997a032a0
    },
    "csv_test_test": {
        "tags": ['csv'],
        "source": "postgres-source",
        "file": "test.csv",
        "args": ['one', 'two'],
        # statement to insert data into user defined table
<<<<<<< HEAD
        "insert_actions": "insert into dput_test (code, name, alpha2, alpha3) values (%s, %s, %s, %s)",
        # row to insert with the above insert statements
        "insert_data": lambda row: (row[3], row[0], row[1], row[2]),
        "process_actions": "delete from ida where iload = %s"
=======
        #
        "insert_action": "insert into dput_test (code, name, alpha2, alpha3) values (%s, %s, %s, %s)",
        #
        # tuple of values to insert with the insert statements
        #
        "insert_values": lambda row: (row[3], row[0], row[1], row[2]),
        "process_actions": ["delete from ida where iload = %s"]
>>>>>>> 2c0015bc478159487a94de627f47bc7997a032a0
    },
    "csv_parts_test": {
        "tags": ['csv', 'ida'],
        "file": "test_000???.csv",
<<<<<<< HEAD
        "process_actions": "delete from ida where iload = %s"
=======
        "process_actions": ["delete from ida where iload = %s"]
>>>>>>> 2c0015bc478159487a94de627f47bc7997a032a0
    },
    "json_ida_test": {
        "tags": ['ida'],
        "encoding": "UTF-8",
        "file": "test.json",
<<<<<<< HEAD
        # row to insert into ida_lines table
        "insert_data": lambda row: (row["code"], row["name"], row.get("alpha2"), row.get("alpha3")),
        "validate_actions": [
=======
        #
        # tuple of values to insert into ida_lines table
        #
        "insert_values": lambda row: (row["code"], row["name"], row.get("alpha2"), row.get("alpha3")),
        "validation_actions": [
>>>>>>> 2c0015bc478159487a94de627f47bc7997a032a0
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
<<<<<<< HEAD
        "process_actions": "delete from ida where iload = %s"
=======
        "process_actions": ["delete from ida where iload = %s"]
>>>>>>> 2c0015bc478159487a94de627f47bc7997a032a0
    },
    "json_test_test": {
        "encoding": "UTF-8",
        "file": "test.json",
<<<<<<< HEAD
        "insert_actions": "insert into dput_test (code, name, alpha2, alpha3) values (%s, %s, %s, %s)",
        "insert_data": lambda row: (row["code"], row["name"], row["alpha2"], row["alpha3"]),
        "process_actions": "delete from ida where iload = %s"
=======
        "insert_action": "insert into dput_test (code, name, alpha2, alpha3) values (%s, %s, %s, %s)",
        "insert_values": lambda row: (row["code"], row["name"], row["alpha2"], row["alpha3"]),
        "process_actions": ["delete from ida where iload = %s"]
>>>>>>> 2c0015bc478159487a94de627f47bc7997a032a0
    },
    "json_parts_test": {
        "tags": ['ida'],
        "file": "test_000???.json",
<<<<<<< HEAD
        "insert_data": lambda row: (row["code"], row["name"], row.get("alpha2"), row.get("alpha3")),
        "process_actions": "delete from ida where iload = %s"
=======
        "insert_values": lambda row: (row["code"], row["name"], row.get("alpha2"), row.get("alpha3")),
        "process_actions": ["delete from ida where iload = %s"]
>>>>>>> 2c0015bc478159487a94de627f47bc7997a032a0
    },
    "xlsx_ida_test": {
        "tags": ['ida'],
        "file": "test.xlsx",
<<<<<<< HEAD
        "process_actions": "delete from ida where iload = %s"
=======
        "process_actions": ["delete from ida where iload = %s"]
>>>>>>> 2c0015bc478159487a94de627f47bc7997a032a0
    },
    "xlsx_skip_test": {
        "tags": ['ida', 'skip_lines'],
        "file": "test.xlsx",
<<<<<<< HEAD
        "skip_lines": 3,
        "process_actions": "delete from ida where iload = %s"
    },
    "xlsx_test_test": {
        "file": "test.xlsx",
        "insert_actions": "insert into dput_test (code, name, alpha2, alpha3) values (%s, %s, %s, %s)",
        "insert_data": lambda row: (row[3], row[0], row[1], row[2]),
        "process_actions": "delete from ida where iload = %s"
=======
        "skip_header": 3,
        "process_actions": ["delete from ida where iload = %s"]
    },
    "xlsx_test_test": {
        "file": "test.xlsx",
        "insert_action": "insert into dput_test (code, name, alpha2, alpha3) values (%s, %s, %s, %s)",
        "insert_values": lambda row: (row[3], row[0], row[1], row[2]),
        "process_actions": ["delete from ida where iload = %s"]
>>>>>>> 2c0015bc478159487a94de627f47bc7997a032a0
    },
    "xlsx_parts_test": {
        "tags": ['ida'],
        "file": "test_000???.xlsx",
<<<<<<< HEAD
        "process_actions": "delete from ida where iload = %s"
=======
        "process_actions": ["delete from ida where iload = %s"]
>>>>>>> 2c0015bc478159487a94de627f47bc7997a032a0
    },
    "csv_test_error": {
        "tags": ['csv'],
        "file": "test.csv",
<<<<<<< HEAD
        "insert_actions": "insert into dput_test (code, name, alpha2, alpha3) values (%s, %s, %s, %s)",
        "insert_data": lambda row: (row[3], row[0], row[1], row[2]),
        "process_actions": "update ida set istat = 2, imess = 'Just testing' where iload = %s"
=======
        "insert_action": "insert into dput_test (code, name, alpha2, alpha3) values (%s, %s, %s, %s)",
        "insert_values": lambda row: (row[3], row[0], row[1], row[2]),
        "process_actions": ["update ida set istat = 2, imess = 'Just testing' where iload = %s"]
>>>>>>> 2c0015bc478159487a94de627f47bc7997a032a0
    },
    "nested_01_ida": {
        "tags": ['ida', 'json', 'nested'],
        "file": "test_nested_01.json",
        "encoding": "UTF-8",
<<<<<<< HEAD
        "insert_data": [
            lambda row: (row['region'], len(row['countries'])),
            lambda row: [(n['code'], n['name'], n['alpha2'], n['alpha3']) for n in row['countries']] if row['countries'] else []
        ],
        "process_actions": "delete from ida where iload = %s"
=======
        "insert_values": lambda row: (row['region'], len(row['countries'])),
        "nested_insert_rows": [
            lambda row: [(n['code'], n['name'], n['alpha2'], n['alpha3']) for n in row['countries']] if row['countries'] else []
        ],
        "process_actions": ["delete from ida where iload = %s"]
>>>>>>> 2c0015bc478159487a94de627f47bc7997a032a0
    },
    "nested_02_ida": {
        "tags": ['ida', 'json', 'nested'],
        "file": "test_nested_02.json",
        "encoding": "UTF-8",
<<<<<<< HEAD
        "insert_data": [
            lambda row: (row['category'], row['doc'], len(row['en_fr']), len(row['en_fr_ru'])),
            lambda row: [(r['en'], r['fr']) for r in row['en_fr']] if row['en_fr'] else [],
            lambda row: row['en_fr_ru']
        ],
        "process_actions": "delete from ida where iload = %s"
=======
        "insert_values": lambda row: (row['category'], row['doc'], len(row['en_fr']), len(row['en_fr_ru'])),
        "nested_insert_rows": [
            lambda row: [(r['en'], r['fr']) for r in row['en_fr']] if row['en_fr'] else [],
            lambda row: row['en_fr_ru']
        ],
        "process_actions": ["delete from ida where iload = %s"]
>>>>>>> 2c0015bc478159487a94de627f47bc7997a032a0
    },
    "nested_01_test": {
        "tags": ['json', 'nested'],
        "file": "test_nested_01.json",
        "encoding": "UTF-8",
<<<<<<< HEAD
        "insert_actions": [
            "insert into test_region (region, contains) values (%s, %s)",
            "insert into test_countries (region, code, name) values (%s, %s, %s)"
        ],
        "insert_data": [
            lambda row: (row['region'], len(row['countries'])),
            lambda row: [(row['region'], n['code'], n['name']) for n in row['countries']] if row['countries'] else []
        ],
        "process_actions": "delete from ida where iload = %s"
=======
        "insert_action": "insert into test_region (region, contains) values (%s, %s)",
        "insert_values": lambda row: (row['region'], len(row['countries'])),
        "nested_insert_actions": [
            "insert into test_countries (region, code, name) values (%s, %s, %s)"
        ],
        "nested_insert_rows": [
            lambda row: [(row['region'], n['code'], n['name']) for n in row['countries']] if row['countries'] else []
        ],
        "process_actions": ["delete from ida where iload = %s"]
>>>>>>> 2c0015bc478159487a94de627f47bc7997a032a0
    },
    "ff_ida_test": {
        "tags": ['json', 'filter', 'flatten'],
        "file": "test_nested_01.json",
        "encoding": "UTF-8",
<<<<<<< HEAD
        "insert_data": lambda row: [(row['region'], n['code'], n['name']) for n in row['countries']] if row['countries'] else [],
        "process_actions": "delete from ida where iload = %s"
=======
        "insert_rows": lambda row: [(row['region'], n['code'], n['name']) for n in row['countries']] if row['countries'] else [],
        "process_actions": ["delete from ida where iload = %s"]
>>>>>>> 2c0015bc478159487a94de627f47bc7997a032a0
    },
}

sources["postgres-source"]["setup"] = sources['postgres-source'].get('setup', []) + [
    """
create table if not exists dput_test (
    code varchar(3) not null,
    name varchar(50) not null,
    alpha2 char(2),
    alpha3 char(3)
)
    """,
    """
create table if not exists test_region (
    region varchar(50) not null,
    contains smallint not null
)
    """,
    """
create table if not exists test_countries (
    region varchar(50) not null,
    code varchar(3) not null,
    name varchar(50) not null
)
    """,
    """
create or replace procedure validate_dput_test(p_iload int)
language plpgsql
as $$
begin
    update ida_lines set
        istat = 2,
        ierrm = trim(ierrm || ' Empty field.')
    where iload = p_iload
        and (c1 is null or c2 is null or c3 is null or c4 is null)
    ;
    update ida_lines set
        istat = 2,
        ierrm = trim(ierrm || ' Not ALPHA2 code.')
    where iload = p_iload
        and length(c2) != 2
    ;
    update ida_lines set
        istat = 2,
        ierrm = trim(ierrm || ' Not ALPHA3 code.')
    where iload = p_iload
        and length(c3) != 3
    ;
end;
$$
    """,
    """
create or replace procedure process_dput_test(p_iload int)
language sql
as $$
delete from ida where iload = p_iload
$$
    """
]

sources["postgres-source"]["upset"] = sources["postgres-source"].get("upset", []) + [
    "drop table if exists dput_test",
    "drop table if exists test_countries",
    "drop table if exists test_region",
    "drop procedure if exists validate_dput_test(int)",
    "drop procedure if exists process_dput_test(int)"
]
