import os
import sys

from sources import sources


# See details on config file's and spec parameters in doc/dput.md

DEBUGGING = True
LOGGING = True
PARALLEL_WORKERS = 2

IN_DIR = os.path.join(os.path.dirname(__file__), '..', 'in')
LOG_DIR = os.path.join(os.path.dirname(__file__), '..', 'log')

ENCODING = 'cp1251'
CSV_DIALECT = 'excel'
CSV_DELIMITER = ';'

SOURCE = "mysql_source"
#PRESERVE_N_LOADS = 10


#
# test specs' stuff
#
CREATE_TABLE_TEST = """
create table if not exists {} (
    code varchar(3) not null,
    name varchar(50) not null,
    alpha2 char(2),
    alpha3 char(3)
)
"""
CREATE_TABLE_REGION = """
create table if not exists {} (
    region varchar(50) not null,
    contains smallint not null,
    region_id int
)
"""
CREATE_TABLE_COUNTRIES = """
create table if not exists {} (
    code varchar(3) not null,
    name varchar(50) not null,
    region varchar(50),
    region_id int
)
"""

# xxx_ida_test
FIELD_NAMES = ['Code', 'Name']
FIELD_INDEXES = []
FIELD_SEP = ';'

def xxx_01_ida(line_no, line):
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


def xxx_03_ida(line):
    """
    line    - line content, e.g. AFAFG004Afghanistan
    """
    return (line[0:2], line[2:5], line[5:8], line[8:].strip())


specs = {
    "csv_ida_test": {
        "tags": ['csv', 'ida'],
        "file": "test.csv",
        "validate_actions": [
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
        "process_actions": [
            # just teardown instead of processing
            "delete from ida where iload = %s"
        ],
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
            where iload = %s
                and substr(c2, 1, 1) not in ('A', 'E', 'I', 'O', 'U')
            """
        ],
        "process_actions": ["delete from ida where iload = %s"]
    },
    "--commented_out": {
        "tags": ['csv', 'ida', 'commented'],
        "file": "test.csv",
        "process_actions": ["delete from ida where iload = %s"]
    },
    "csv_skip_test": {
        "tags": ['csv', 'ida', 'skip_lines'],
        "file": "test.csv",
        "skip_lines": 1,
        "process_actions": ["delete from ida where iload = %s"]
    },
    "csv_proc_test": {
        "tags": ['csv'],
        "file": "test.csv",
        "validate_actions": 'call validate_dput_test(%s)',
        "process_actions": 'call process_dput_test(%s)',
        # test setup and teardown
        "setup": [
"""
create procedure if not exists validate_dput_test(p_iload int)
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
end
""",
"""
create procedure if not exists process_dput_test(p_iload int)
begin
    delete from ida where iload = p_iload;
end
"""
        ],
        "upset": [
            "drop procedure if exists validate_dput_test",
            "drop procedure if exists process_dput_test"
        ]
    },
    "csv_test_test": {
        "tags": ['csv'],
        "source": "mysql_source",
        "file": "test.csv",
        "args": ['one', 'two'],
        "insert_actions": "insert into dput_csv_test_test (code, name, alpha2, alpha3) values (%s, %s, %s, %s)",
        "insert_data": lambda row: (row[3], row[0], row[1], row[2]),
        "process_actions": "delete from ida where iload = %s",
        # test setup and teardown
        "setup": CREATE_TABLE_TEST.format('dput_csv_test_test'),
        "upset": "drop table dput_csv_test_test"
    },
    "csv_parts_test": {
        "tags": ['csv', 'ida'],
        "file": "test_000???.csv",
        "process_actions": "delete from ida where iload = %s"
    },
    "json_ida_test": {
        "tags": ['ida'],
        "encoding": "UTF-8",
        "file": "test.json",
        "insert_data": lambda row: (row["code"], row["name"], row.get("alpha2"), row.get("alpha3")),
        "validate_actions": [
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
        "process_actions": "delete from ida where iload = %s"
    },
    "json_test_test": {
        "encoding": "UTF-8",
        "file": "test.json",
        "insert_actions": "insert into dput_json_test_test (code, name, alpha2, alpha3) values (%s, %s, %s, %s)",
        "insert_data": lambda row: (row["code"], row["name"], row["alpha2"], row["alpha3"]),
        "process_actions": "delete from ida where iload = %s",
        # test setup and teardown
        "setup": CREATE_TABLE_TEST.format('dput_json_test_test'),
        "upset": "drop table dput_json_test_test"
    },
    "json_parts_test": {
        "tags": ['ida'],
        "file": "test_000???.json",
        "insert_data": lambda row: (row["code"], row["name"], row.get("alpha2"), row.get("alpha3")),
        "process_actions": ["delete from ida where iload = %s"]
    },
    "xlsx_ida_test": {
        "tags": ['ida'],
        "file": "test.xlsx",
        "process_actions": "delete from ida where iload = %s"
    },
    "xlsx_skip_test": {
        "tags": ['ida', 'skip_lines'],
        "file": "test.xlsx",
        "skip_lines": 3,
        "process_actions": "delete from ida where iload = %s"
    },
    "xlsx_test_test": {
        "file": "test.xlsx",
        "insert_actions": "insert into dput_xlsx_test_test (code, name, alpha2, alpha3) values (%s, %s, %s, %s)",
        "insert_data": lambda row: (row[3], row[0], row[1], row[2]),
        "process_actions": "delete from ida where iload = %s",
        # test setup and teardown
        "setup": CREATE_TABLE_TEST.format('dput_xlsx_test_test'),
        "upset": "drop table dput_xlsx_test_test"
    },
    "xlsx_parts_test": {
        "tags": ['ida'],
        "file": "test_000???.xlsx",
        "process_actions": "delete from ida where iload = %s"
    },
    "csv_test_error": {
        "tags": ['csv'],
        "file": "test.csv",
        "insert_actions": "insert into dput_csv_test_error (code, name, alpha2, alpha3) values (%s, %s, %s, %s)",
        "insert_data": lambda row: (row[3], row[0], row[1], row[2]),
        "process_actions": "update ida set istat = 2, imess = 'Just testing' where iload = %s",
        # test setup and teardown
        "setup": CREATE_TABLE_TEST.format('dput_csv_test_error'),
        "upset": "drop table dput_csv_test_error"
    },
    "nested_00_ida": {
        "tags": ['ida', 'csv', 'nested'],
        "file": "test_nested_00.csv",
        "insert_data": \
            lambda row: [(row[0], n) for n in row[1].split(',')] if row[1] else [],
        "process_actions": "delete from ida where iload = %s"
    },
    "nested_01_ida": {
        "tags": ['ida', 'json', 'nested'],
        "file": "test_nested_01.json",
        "encoding": "UTF-8",
        "insert_data": [
            lambda row: (row['region'], len(row['countries'])),
            lambda row: [(n['code'], n['name'], n['alpha2'], n['alpha3']) for n in row['countries']] if row['countries'] else []
        ],
        "process_actions": "delete from ida where iload = %s"
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
        "process_actions": "delete from ida where iload = %s"
    },
    "nested_01_test": {
        "tags": ['json', 'nested'],
        "file": "test_nested_01.json",
        "encoding": "UTF-8",
        "insert_actions": [
            "insert into nested_01_test_region (region, contains) values (%s, %s)",
            "insert into nested_01_test_countries (region, code, name) values (%s, %s, %s)"
        ],
        "insert_data": [
            lambda row: (row['region'], len(row['countries'])),
            lambda row: [(row['region'], n['code'], n['name']) for n in row['countries']] if row['countries'] else []
        ],
        "validate_actions": """
            update ida set istat = 2
            where iload = %s
                and exists (
                    select 1
                    from nested_01_test_region r
                    where contains != (
                            select count(*)
                            from nested_01_test_countries c
                            where r.region = c.region
                        )
                )
            """,
        "process_actions": [
            "delete from ida where iload = %s",
            "delete from nested_01_test_countries where %s is not null",
            "delete from nested_01_test_region where %s is not null"
        ],
        # test setup and teardown
        "setup": [
            CREATE_TABLE_REGION.format('nested_01_test_region'),
            CREATE_TABLE_COUNTRIES.format('nested_01_test_countries')
        ],
        "upset": [
            "drop table nested_01_test_region",
            "drop table nested_01_test_countries"
        ]
    },
    "nested_01_keygen": {
        "tags": ['json', 'nested'],
        "file": "test_nested_01.json",
        "encoding": "UTF-8",
        "insert_actions": [
            "insert into nested_01_keygen_region (region_id, region, contains) values (%s, %s, %s)",
            "insert into nested_01_keygen_countries (region_id, code, name) values (%s, %s, %s)"
        ],
        "insert_data": [
            lambda iload, iline, row: (iload * 1000 + iline, row['region'], len(row['countries'])),
            lambda iload, iline, row: [(iload * 1000 + iline, n['code'], n['name']) for n in row['countries']] if row['countries'] else []
        ],
        "validate_actions": """
            update ida set istat = 2 
            where iload = %s
                and exists (
                    select 1
                    from nested_01_keygen_region r
                    where contains != (
                            select count(*)
                            from nested_01_keygen_countries c
                            where r.region_id = c.region_id
                        )
                )
            """,
        "process_actions": [
            "delete from ida where iload = %s",
            "delete from nested_01_keygen_countries where %s is not null",
            "delete from nested_01_keygen_region where %s is not null"
        ],
        # test setup and teardown
        "setup": [
            CREATE_TABLE_REGION.format('nested_01_keygen_region'),
            CREATE_TABLE_COUNTRIES.format('nested_01_keygen_countries')
        ],
        "upset": [
            "drop table nested_01_keygen_region",
            "drop table nested_01_keygen_countries"
        ]
    },
    "flatten_ida_test": {
        "tags": ['json', 'filter', 'flatten'],
        "file": "test_nested_01.json",
        "encoding": "UTF-8",
        "insert_data": lambda row: [(row['region'], n['code'], n['name']) for n in row['countries']] if row['countries'] else [],
        "process_actions": "delete from ida where iload = %s"
    },
    "xxx_01_ida": {
        "tags": ['text_lines', 'ida'],
        "file": "test_xxx.csv",
        # just pass lines of the file to insert_data function
        "text_lines": True,
        "insert_data": xxx_01_ida,
        "process_actions": "delete from ida where iload = %s"
    },
    "xxx_02_ida": {
        "tags": ['text_lines', 'ida'],
        "file": "test_xxx.csv",
        "text_lines": True,
        "process_actions": "delete from ida where iload = %s"
    },
    "xxx_03_ida": {
        "tags": ['text_lines', 'ida'],
        "file": "test_xxx.dat",
        "text_lines": True,
        "insert_data": xxx_03_ida,
        "process_actions": "delete from ida where iload = %s"
    },
    "zipped_ida_test": {
        "tags": ['zipped', 'ida'],
        "file": "test_zip.zip",
        "process_actions": "delete from ida where iload = %s"
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
            where iload = %s
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
            where iload = %s
            """,
            """
            delete from ida where iload = %s
            """
        ],
        "upset": [
            """
            drop table if exists target_table
            """
        ]
    },
    "csv_zero_test": {
        "tags": ['csv', 'ida', 'zero'],
        "file": "test_zero.csv",
        "process_actions": "delete from ida where iload = %s"
    },
    "json_zero_test": {
        "tags": ['json', 'ida', 'zero'],
        "file": "test_zero.json",
        "insert_data": lambda row: (row["code"], row["name"], row.get("alpha2"), row.get("alpha3")),
        "process_actions": "delete from ida where iload = %s"
    },
    "xlsx_zero_test": {
        "tags": ['xlsx', 'ida', 'zero'],
        "file": "test_zero.xlsx",
        "process_actions": "delete from ida where iload = %s"
    },
    "zip_zero_test": {
        "tags": ['zip', 'ida', 'zero'],
        "file": "test_zero.zip",
        "process_actions": "delete from ida where iload = %s"
    },
    "csv_naive_test": {
        "tags": ['cav', 'ida', 'naive'],
        "file": "test_naive.csv",
        "process_actions": "delete from ida where iload = %s"
    },
}
