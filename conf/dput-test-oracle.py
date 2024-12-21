import os
import sys

from sources import sources

#
# Run sanity tests with command lines
#     dput.py conf/dput-test-oracle.py all
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
SOURCE = "oracle-source"

#
# SETTINGS USED IN specs
#

# special_ida_test
FIELD_NAMES = ['Code', 'Name']
FIELD_INDEXES = []
FIELD_SEP = ';'

def special_ida_test(line_no, line):
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
        #
        # the following parameters default to the global ones
        #"encoding": ENCODING,
        #"csv_dialect": CSV_DIALECT,
        #"csv_delimiter": CSV_DELIMITER,
        #"csv_quotechar": CSV_QUOTECHAR,
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
        # optionally process validated data
        "process_actions": [
            # just teardown
            "delete from ida where iload = :1"
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
                ierrm = trim(ierrm || ' Empty field.')
            where iload = :1
                and substr(c1, 1, 1) not in ('A', 'E', 'I', 'O', 'U')
            """
        ],
        "process_actions": ["delete from ida where iload = :1"]
    },
    "--commented_out": {
        "tags": ['csv', 'ida', 'commented'],
        "file": "test.csv",
        "process_actions": ["delete from ida where iload = :1"]
    },
    "csv_skip_test": {
        "tags": ['csv', 'ida', 'skip_header'],
        "file": "test.csv",
        "skip_header": 1,
        "process_actions": "delete from ida where iload = :1"
    },
    "csv_proc_test": {
        "tags": ['csv'],
        "file": "test.csv",
        "validate_actions": 'begin validate_dput_test(:1); end;',
        "process_actions": 'begin process_dput_test(:1); end;'
    },
    "csv_test_test": {
        "tags": ['csv'],
        "source": "oracle-source",
        "file": "test.csv",
        "args": ['one', 'two'],
        # statement to insert data into user defined table
        "insert_actions": "insert into dput_test (code, name, alpha2, alpha3) values (:1, :2, :3, :4)",
        # row to insert with the above insert statement
        "insert_data": lambda row: (row[3], row[0], row[1], row[2]),
        "process_actions": "delete from ida where iload = :1"
    },
    "csv_parts_test": {
        "tags": ['csv', 'ida'],
        "file": "test_000???.csv",
        "process_actions": "delete from ida where iload = :1"
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
        "process_actions": "delete from ida where iload = :1"
    },
    "json_test_test": {
        "encoding": "UTF-8",
        "file": "test.json",
        "insert_actions": "insert into dput_test (code, name, alpha2, alpha3) values (:1, :2, :3, :4)",
        "insert_data": lambda row: (row["code"], row["name"], row["alpha2"], row["alpha3"]),
        "process_actions": "delete from ida where iload = :1"
    },
    "json_parts_test": {
        "tags": ['ida'],
        "file": "test_000???.json",
        "insert_data": lambda row: (row["code"], row["name"], row.get("alpha2"), row.get("alpha3")),
        "process_actions": "delete from ida where iload = :1"
    },
    "xlsx_ida_test": {
        "tags": ['ida'],
        "file": "test.xlsx",
        "process_actions": "delete from ida where iload = :1"
    },
    "xlsx_skip_test": {
        "tags": ['ida', 'skip_header'],
        "file": "test.xlsx",
        "skip_header": 3,
        "process_actions": "delete from ida where iload = :1"
    },
    "xlsx_test_test": {
        "file": "test.xlsx",
        "insert_actions": "insert into dput_test (code, name, alpha2, alpha3) values (:1, :2, :3, :4)",
        "insert_data": lambda row: (row[3], row[0], row[1], row[2]),
        "process_actions": "delete from ida where iload = :1"
    },
    "xlsx_parts_test": {
        "tags": ['ida'],
        "file": "test_000???.xlsx",
        "process_actions": "delete from ida where iload = :1"
    },
    "csv_test_error": {
        "tags": ['csv'],
        "file": "test.csv",
        "insert_actions": "insert into dput_test (code, name, alpha2, alpha3) values (:1, :2, :3, :4)",
        "insert_data": lambda row: (row[3], row[0], row[1], row[2]),
        "process_actions": "update ida set istat = 2, imess = 'Just testing' where iload = :1"
    },
    "nested_01_ida": {
        "tags": ['ida', 'json', 'nested'],
        "file": "test_nested_01.json",
        "encoding": "UTF-8",
        "insert_data": [
            lambda row: (row['region'], len(row['countries'])),
            lambda row: [(n['code'], n['name'], n['alpha2'], n['alpha3']) for n in row['countries']] if row['countries'] else []
        ],
        "process_actions": "delete from ida where iload = :1"
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
        "process_actions": "delete from ida where iload = :1"
    },
    "nested_01_test": {
        "tags": ['json', 'nested'],
        "file": "test_nested_01.json",
        "encoding": "UTF-8",
        "insert_actions": [
            "insert into test_region (region, contains) values (:1, :2)",
            "insert into test_countries (region, code, name) values (:1, :2, :3)"
        ],
        "insert_data": [
            lambda row: (row['region'], len(row['countries'])),
            lambda row: [(row['region'], n['code'], n['name']) for n in row['countries']] if row['countries'] else []
        ],
        "validate_actions": """
            update ida set istat = 2
            where iload = :1
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
            "delete from ida where iload = :1",
            "delete from test_countries where :1 is not null",
            "delete from test_region where :1 is not null"
        ]
    },
    "nested_02_test": {
        "tags": ['json', 'nested'],
        "file": "test_nested_01.json",
        "encoding": "UTF-8",
        "insert_actions": [
            "insert into test_region (iload, iline, region, contains) values (:1, :2, :3, :4)",
            "insert into test_countries (iload, iline, code, name) values (:1, :2, :3, :4)"
        ],
        "insert_data": [
            lambda iload, iline, row: (iload, iline, row['region'], len(row['countries'])),
            lambda iload, iline, row: [(iload, iline, n['code'], n['name']) for n in row['countries']] if row['countries'] else []
        ],
        "validate_actions": """
            update ida set istat = 2 
            where iload = :1
                and exists (
                    select 1
                    from test_region r
                    where contains != (
                            select count(*)
                            from test_countries c
                            where r.iload = c.iload
                                and r.iline = c.iline
                        )
                )
            """,
        "process_actions": [
            "delete from ida where iload = :1",
            "delete from test_countries where :1 is not null",
            "delete from test_region where :1 is not null"
        ]
    },
    "flatten_ida_test": {
        "tags": ['json', 'filter', 'flatten'],
        "file": "test_nested_01.json",
        "encoding": "UTF-8",
        "insert_data": lambda row: [(row['region'], n['code'], n['name']) for n in row['countries']] if row['countries'] else [],
        "process_actions": "delete from ida where iload = :1"
    },
    "special_ida_test": {
        "tags": ['pass_lines', 'ida'],
        "file": "test_special.csv",
        # just pass lines of the file to insert_data function
        "pass_lines": True,
        "insert_data": special_ida_test,
        "process_actions": "delete from ida where iload = :1"
    },
    "lines_ida_test": {
        "tags": ['pass_lines', 'ida'],
        "file": "test_special.csv",
        # just pass lines of the file to a column (that should be big enough)
        "pass_lines": True,
        "process_actions": "delete from ida where iload = :1"
    },
    "zipped_ida_test": {
        "tags": ['zipped', 'ida'],
        "file": "test_zip.zip",
        "process_actions": "delete from ida where iload = :1"
    },
    "setup_upset_test": {
        "tags": ['csv', 'ida', 'setup', 'upset'],
        "file": "test.csv",
        "setup": [
            """
            begin
                execute immediate 'drop table target_table';
            exception
                when others then
                    if sqlcode = -942 then
                        null; -- ORA-00942 table or view does not exist
                    end if;
            end;
            """,
            """
            create table target_table (
                code char(3),
                name varchar2(100),
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
            where iload = :1
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
            where iload = :1
            """,
            """
            delete from ida where iload = :1
            """
        ],
        "upset": [
            """
            begin
                execute immediate 'drop table target_table';
            exception
                when others then
                    if sqlcode = -942 then
                        null; -- ORA-00942 table or view does not exist
                    end if;
            end;
            """
        ]
    },
}

sources["oracle-source"]["setup"] = sources['oracle-source'].get('setup', []) + [
    """
begin
    execute immediate 'drop table dput_test';
exception
    when others then
        if sqlcode = -942 then
            null; -- ORA-00942 table or view does not exist
        end if;
end;
    """,
    """
create table dput_test (
    code varchar2(3) not null,
    name varchar2(50) not null,
    alpha2 char(2),
    alpha3 char(3)
)
    """,
    """
begin
    execute immediate 'drop table test_region';
exception
    when others then
        if sqlcode = -942 then
            null; -- ORA-00942 table or view does not exist
        end if;
end;
    """,
    """
create table test_region (
    region varchar2(50) not null,
    contains number(3) not null,
    iload number(9),
    iline number(9)
)
    """,
    """
begin
    execute immediate 'drop table test_countries';
exception
    when others then
        if sqlcode = -942 then
            null; -- ORA-00942 table or view does not exist
        end if;
end;
    """,
    """
create table test_countries (
    code varchar2(3) not null,
    name varchar2(50) not null,
    region varchar2(50),
    iload number(9),
    iline number(9)
)
    """,
    """
create or replace procedure validate_dput_test(p_iload number)
as
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
    """,
    """
create or replace procedure process_dput_test(p_iload number)
as
begin
    delete from ida where iload = p_iload;
end;
    """
]

sources["oracle-source"]["upset"] = sources["oracle-source"].get("upset", []) + [
    """
begin
    execute immediate 'drop table dput_test';
exception
    when others then
        if sqlcode = -942 then
            null; -- ORA-00942 table or view does not exist
        end if;
end;
    """,
    """
begin
    execute immediate 'drop table test_countries';
exception
    when others then
        if sqlcode = -942 then
            null; -- ORA-00942 table or view does not exist
        end if;
end;
    """,
    """
begin
    execute immediate 'drop table test_region';
exception
    when others then
        if sqlcode = -942 then
            null; -- ORA-00942 table or view does not exist
        end if;
end;
    """,
    """
begin
    execute immediate 'drop procedure validate_dput_test';
exception
    when others then
        if sqlcode = -4043 then
            -- ORA-04043 object <OBJECT> does not exist
            null;
        end if;
end;
    """,
    """
begin
    execute immediate 'drop procedure process_dput_test';
exception
    when others then
        if sqlcode = -4043 then
            -- ORA-04043 object <OBJECT> does not exist
            null;
        end if;
end;
    """
]
