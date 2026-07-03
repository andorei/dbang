import os
import sys


# See details on config file's and spec parameters in doc/dfifo.md

DEBUGGING = True
LOGGING = True
PARALLEL_WORKERS = 2

IN_DIR = os.path.join(os.path.dirname(__file__), '..', 'in')
OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'out')
LOG_DIR = os.path.join(os.path.dirname(__file__), '..', 'log')

ENCODING = 'UTF-8'
CSV_DIALECT = 'excel'
CSV_DELIMITER = ';'

# defaults to ISO 86101; use '%c' to align with locale
#DATETIME_FORMAT = '%c'
# defaults to ISO 86101; use '%x' to align with locale
#DATE_FORMAT = '%x'


#
# test specs' stuff
#

# See spec xxx_json
FIELD_NAMES = ['Code', 'Name']
FIELD_INDEXES = []
FIELD_SEP = ';'

def xxx(line_no, line):
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
    "csv_csv": {
        "tags": ["csv"],
        "fi": {"file": "test.csv"},
        "fo": {"file": "dfifo_test_csv.csv"}
    },
    "csv_json": {
        "tags": ["csv"],
        "fi": {"file": "test.csv"},
        "fo": {
            "file": "dfifo_test_csv.json",
            "header": ["Название", "А2", "А3", "Код"],
            "json.template": "dfifo_test.json.jinja"
        }
    },
    "csv_html": {
        "tags": ["csv"],
        "fi": {"file": "test.csv"},
        "fo": {
            "file": "dfifo_test_csv.html",
            "header": ["Name", "А2", "А3", "Code"],
            "html.title": "Countries",
            "html.template": "dfifo_test.html.jinja"
        }
    },
    "csv_xlsx": {
        "tags": ["csv"],
        "fi": {"file": "test.csv"},
        "fo": {
            "file": "dfifo_test_csv.xlsx",
            "header": ["Name", "А2", "А3", "Code"]
        }
    },
    "csv_parts_json": {
        "tags": ["csv", "parts"],
        "fi": {"file": "test_000???.csv"},
        "fo": {
            "file": "dfifo_test_csv_parts.json",
            "header": ["Название", "А2", "А3", "Код"]
        }
    },
    "csv_split_json": {
        "tags": ["csv", "split"],
        "fi": {"file": "test.csv"},
        "fo": {
            "file": "dfifo_test_csv_split_%(seqn)06i.json",
            "header": ["Название", "А2", "А3", "Код"],
            "rows_per_file": 100
        }
    },
    "csv_parts_split_json": {
        "tags": ["csv", "parts", "split"],
        "fi": {"file": "test_000???.csv"},
        "fo": {
            "file": "dfifo_test_csv_parts_split_%(seqn)06i.json",
            "header": ["Название", "А2", "А3", "Код"],
            "rows_per_file": 50
        }
    },
    "csv_parts_parts_json": {
        "tags": ["csv", "parts", "parts_parts"],
        "fi": {"file": "test_000???.csv"},
        "fo": {
            "file": "dfifo_test_csv_parts_parts_%(seqn)06i.json",
            "header": ["Название", "А2", "А3", "Код"],
            "rows_per_file": -1
        }
    },
    "csv_parts_parts_empty": {
        "tags": ["csv", "parts", "parts_parts", "empty"],
        "fi": {"file": "test_empty_000???.csv"},
        "fo": {
            "file": "dfifo_test_csv_parts_parts_empty_%(seqn)06i.json",
            "header": ["Название", "А2", "А3", "Код"],
            "rows_per_file": -1
        }
    },
    "csv_parts_parts_error": {
        "tags": ["csv", "parts", "parts_parts", "error"],
        "fi": {
            "file": "test_error_000???.csv",
            "skip_bad_files": True
        },
        "fo": {
            "file": "dfifo_test_csv_parts_parts_error_%(seqn)06i.json",
            "header": ["Название", "А2", "А3", "Код"],
            "rows_per_file": -1
        }
    },
    "csv_selected_csv": {
        "tags": ["csv", "selected"],
        "fi": {
            "file": "test.csv",
            "transformer": lambda row: (row[3], row[0]) if row[0][0] in 'AEIOU' else None
        },
        "fo": {
            "file": "dfifo_test_csv_selected.csv",
            "header": ["code", "name"]
        },
    },
    "json_csv": {
        "tags": ["json"],
        "fi": {
            "file": "test.json",
            "transformer": lambda row: (row["code"], row.get("alpha2"), row.get("alpha3"), row["name"])
        },
        "fo": {"file": "dfifo_test_json.csv"}
    },
    "json_json": {
        "tags": ["json"],
        "fi": {
            "file": "test.json",
            "transformer": lambda row: (row["code"], row.get("alpha2"), row.get("alpha3"), row["name"])
        },
        "fo": {
            "file": "dfifo_test_json.json",
            "header": ["Код", "А2", "А3", "Название"]
        }
    },
    "json_html": {
        "tags": ["json"],
        "fi": {
            "file": "test.json",
            "transformer": lambda row: (row["code"], row.get("alpha2"), row.get("alpha3"), row["name"])
        },
        "fo": {
            "file": "dfifo_test_json.html",
            "header": ["Code", "А2", "А3", "Name"],
            "html.title": "Countries"
        }
    },
    "json_xlsx": {
        "tags": ["json"],
        "fi": {
            "file": "test.json",
            "transformer": lambda row: (row["code"], row.get("alpha2"), row.get("alpha3"), row["name"])
        },
        "fo": {
            "file": "dfifo_test_json.xlsx",
            "header": ["Code", "А2", "А3", "Name"]
        }
    },
    "json_parts_json": {
        "tags": ["csv", "parts"],
        "fi": {
            "file": "test_000???.json",
            "transformer": lambda row: (row["code"], row.get("alpha2"), row.get("alpha3"), row["name"])
        },
        "fo": {
            "file": "dfifo_test_json_parts.json",
            "header": ["Код", "А2", "А3", "Название"]
        }
    },
    "json_split_json": {
        "tags": ["json", "split"],
        "fi": {
            "file": "test.json",
            "transformer": lambda row: (row["code"], row.get("alpha2"), row.get("alpha3"), row["name"])
        },
        "fo": {
            "file": "dfifo_test_json_split_%(seqn)06i.json",
            "header": ["Код", "А2", "А3", "Название"],
            "rows_per_file": 100
        }
    },
    "json_parts_split_json": {
        "tags": ["json", "parts", "split"],
        "fi": {
            "file": "test_000???.json",
            "transformer": lambda row: (row["code"], row.get("alpha2"), row.get("alpha3"), row["name"])
        },
        "fo": {
            "file": "dfifo_test_json_parts_split_%(seqn)06i.json",
            "header": ["Код", "А2", "А3", "Название"],
            "rows_per_file": 50
        }
    },
    "json_parts_parts_json": {
        "tags": ["json", "parts", "parts_parts"],
        "fi": {
            "file": "test_000???.json",
            "transformer": lambda row: (row["code"], row.get("alpha2"), row.get("alpha3"), row["name"])
        },
        "fo": {
            "file": "dfifo_test_json_parts_parts_%(seqn)06i.json",
            "header": ["Код", "А2", "А3", "Название"],
            "rows_per_file": -1
        }
    },
    "json_parts_parts_empty": {
        "tags": ["json", "parts", "parts_parts", "empty"],
        "fi": {
            "file": "test_empty_000???.json",
            "transformer": lambda row: (row["code"], row.get("alpha2"), row.get("alpha3"), row["name"])
        },
        "fo": {
            "file": "dfifo_test_json_parts_parts_empty_%(seqn)06i.json",
            "header": ["Код", "А2", "А3", "Название"],
            "rows_per_file": -1
        }
    },
    "json_parts_parts_error": {
        "tags": ["json", "parts", "parts_parts", "error"],
        "fi": {
            "file": "test_error_000???.json",
            "transformer": lambda row: (row["code"], row.get("alpha2"), row.get("alpha3"), row["name"]),
            "skip_bad_files": True
        },
        "fo": {
            "file": "dfifo_test_json_parts_parts_error_%(seqn)06i.json",
            "header": ["Код", "А2", "А3", "Название"],
            "rows_per_file": -1
        }
    },
    "json_selected_json": {
        "tags": ["json", "selected"],
        "fi": {
            "file": "test.json",
            "transformer": \
                lambda row: (row["code"], row["name"])  if row['name'][0] in 'AEIOU' else None
        },
        "fo": {
            "file": "dfifo_test_json_selected.json",
            "header": ["code", "name"]
        },
    },
    "xlsx_csv": {
        "tags": ["xlsx"],
        "fi": {"file": "test.xlsx"},
        "fo": {"file": "dfifo_test_xlsx.csv"}
    },
    "xlsx_json": {
        "tags": ["xlsx"],
        "fi": {"file": "test.xlsx"},
        "fo": {
            "file": "dfifo_test_xlsx.json",
            "header": ["Название", "А2", "А3", "Код"]
        }
    },
    "xlsx_html": {
        "tags": ["xlsx"],
        "fi": {
            "file": "test.xlsx",
            "transformer": lambda row: (row[3], row[1], row[2], row[0])
        },
        "fo": {
            "file": "dfifo_test_xlsx.html",
            "header": ["Code", "А2", "А3", "Name"],
            "html.title": "Countries"
        }
    },
    "xlsx_xlsx": {
        "tags": ["xlsx"],
        "fi": {
            "file": "test.xlsx",
            "transformer": lambda row: (row[3], row[1], row[2], row[0])
        },
        "fo": {"file": "dfifo_test_xlsx.xlsx"}
    },
    "xlsx_parts_json": {
        "tags": ["xlsx", "parts"],
        "fi": {"file": "test_000???.xlsx"},
        "fo": {
            "file": "dfifo_test_xlsx_parts.json",
            "header": ["Название", "А2", "А3", "Код"]
        }
    },
    "xlsx_split_json": {
        "tags": ["xlsx", "split"],
        "fi": {"file": "test.xlsx"},
        "fo": {
            "file": "dfifo_test_xlsx_split_%(seqn)06i.json",
            "header": ["Название", "А2", "А3", "Код"],
            "rows_per_file": 100
        }
    },
    "xlsx_parts_split_json": {
        "tags": ["xlsx", "parts", "split"],
        "fi": {"file": "test_000???.xlsx"},
        "fo": {
            "file": "dfifo_test_xlsx_parts_split_%(seqn)06i.json",
            "header": ["Название", "А2", "А3", "Код"],
            "rows_per_file": 50
        }
    },
    "xlsx_parts_parts_json": {
        "tags": ["xlsx", "parts", "parts_parts"],
        "fi": {"file": "test_000???.xlsx"},
        "fo": {
            "file": "dfifo_test_xlsx_parts_parts_%(seqn)06i.json",
            "header": ["Название", "А2", "А3", "Код"],
            "rows_per_file": -1
        }
    },
    "xlsx_parts_parts_empty": {
        "tags": ["xlsx", "parts", "parts_parts", "empty"],
        "fi": {"file": "test_empty_000???.xlsx"},
        "fo": {
            "file": "dfifo_test_xlsx_parts_parts_empty_%(seqn)06i.json",
            "header": ["Название", "А2", "А3", "Код"],
            "rows_per_file": -1
        }
    },
    "xlsx_parts_parts_error": {
        "tags": ["xlsx", "parts", "parts_parts", "error"],
        "fi": {
            "file": "test_error_000???.xlsx",
            "skip_bad_files": True
            },
        "fo": {
            "file": "dfifo_test_xlsx_parts_parts_error_%(seqn)06i.json",
            "header": ["Название", "А2", "А3", "Код"],
            "rows_per_file": -1
        }
    },
    "xlsx_selected_xlsx": {
        "tags": ["xlsx", "selected"],
        "fi": {
            "file": "test.xlsx",
            "transformer": lambda row: (row[3], row[0]) if row[0][0] in 'AEIOU' else None
        },
        "fo": {
            "file": "dfifo_test_xlsx_selected.xlsx",
            "header": ["code", "name"]
        },
    },
    "xxx_csv": {
        "tags": ["xxx"],
        "fi": {
            "file": "test_xxx.csv",
            "text_lines": True,
            "transformer": xxx
        },
        "fo": {
            "file": "dfifo_test_xxx.csv",
            "header": ["code", "name"]
        }
    },
    "xxx_json": {
        "tags": ["xxx"],
        "fi": {
            "file": "test_xxx.csv",
            "text_lines": True,
            "transformer": xxx
        },
        "fo": {
            "file": "dfifo_test_xxx.json",
            "header": ["code", "name"]
        }
    },
    "xxx_html": {
        "tags": ["xxx"],
        "fi": {
            "file": "test_xxx.csv",
            "text_lines": True,
            "transformer": xxx
        },
        "fo": {
            "file": "dfifo_test_xxx.html",
            "header": ["Код", "Название"],
            "html.title": "Страны мира"
        }
    },
    "xxx_xlsx": {
        "tags": ["xxx"],
        "fi": {
            "file": "test_xxx.csv",
            "text_lines": True,
            "transformer": xxx
        },
        "fo": {
            "file": "dfifo_test_xxx.xlsx",
            "header": ["Code", "Name"]
        }
    },
    "xxx_parts_json": {
        "tags": ["xxx", "parts"],
        "fi": {
            "file": "test_xxx_000???.csv",
            "text_lines": True,
            "transformer": xxx
        },
        "fo": {
            "file": "dfifo_test_xxx_parts.json",
            "header": ["Код", "Название"]
        }
    },
    "xxx_split_json": {
        "tags": ["xxx", "split"],
        "fi": {
            "file": "test_xxx.csv",
            "text_lines": True,
            "transformer": xxx
        },
        "fo": {
            "file": "dfifo_test_xxx_split_%(seqn)06i.json",
            "header": ["Код", "Название"],
            "rows_per_file": 100
        }
    },
    "xxx_parts_split_json": {
        "tags": ["xxx", "parts", "split"],
        "fi": {
            "file": "test_xxx_000???.csv",
            "text_lines": True,
            "transformer": xxx
        },
        "fo": {
            "file": "dfifo_test_xxx_parts_split_%(seqn)06i.json",
            "header": ["Код", "Название"],
            "rows_per_file": 50
        }
    },
    "xxx_parts_parts_json": {
        "tags": ["xxx", "parts", "parts_parts"],
        "fi": {
            "file": "test_xxx_000???.csv",
            "text_lines": True,
            "transformer": xxx
        },
        "fo": {
            "file": "dfifo_test_xxx_parts_parts_%(seqn)06i.json",
            "header": ["Код", "Название"],
            "rows_per_file": -1
        }
    },
    "xxx_parts_parts_empty": {
        "tags": ["xxx", "parts", "parts_parts", "empty"],
        "fi": {
            "file": "test_xxx_empty_000???.csv",
            "text_lines": True,
            "transformer": xxx
        },
        "fo": {
            "file": "dfifo_test_xxx_parts_parts_%(seqn)06i.json",
            "header": ["Код", "Название"],
            "rows_per_file": -1
        }
    },
    "xxx_parts_parts_error": {
        "tags": ["xxx", "parts", "parts_parts", "error"],
        "fi": {
            "file": "test_xxx_error_000???.csv",
            "text_lines": True,
            "transformer": xxx,
            "skip_bad_files": True
        },
        "fo": {
            "file": "dfifo_test_xxx_error_%(seqn)06i.json",
            "header": ["Код", "Название"],
            "rows_per_file": -1
        }
    },
    "csv_zero_json": {
        "tags": ["csv", "zero"],
        "fi": {"file": "test_zero.csv"},
        "fo": {
            "file": "dfifo_test_zero_csv.json",
            "header": ["Название", "А2", "А3", "Код"]
        }
    },
    "json_zero_json": {
        "tags": ["json", "zero"],
        "fi": {
            "file": "test_zero.json",
            "transformer": lambda row: (row["code"], row.get("alpha2"), row.get("alpha3"), row["name"])
        },
        "fo": {
            "file": "dfifo_test_zero_json.json",
            "header": ["Код", "А2", "А3", "Название"]
        }
    },
    "xlsx_zero_json": {
        "tags": ["xlsx", "zero"],
        "fi": {"file": "test_zero.xlsx"},
        "fo": {
            "file": "dfifo_test_zero_xlsx.json",
            "header": ["Название", "А2", "А3", "Код"]
        }
    },
    "zip_zero_json": {
        "tags": ["zip", "zero"],
        "fi": {"file": "test_zero.zip"},
        "fo": {
            "file": "dfifo_test_zero_zip.json",
            "header": ["Название", "А2", "А3", "Код"]
        }
    },
    # empty input file -> no output json file
    "csv_empty_json": {
        "tags": ["csv", "empty"],
        "fi": {"file": "test_empty.csv"},
        "fo": {
            "file": "dfifo_test_empty_csv.json",
            "header": ["Название", "А2", "А3", "Код"]
        }
    },
    "json_empty_json": {
        "tags": ["json", "empty"],
        "fi": {
            "file": "test_empty.json",
            "transformer": lambda row: (row["code"], row.get("alpha2"), row.get("alpha3"), row["name"])
        },
        "fo": {
            "file": "dfifo_test_empty_json.json",
            "header": ["Код", "А2", "А3", "Название"]
        }
    },
    "xlsx_empty_json": {
        "tags": ["xlsx", "empty"],
        "fi": {"file": "test_empty.xlsx"},
        "fo": {
            "file": "dfifo_test_empty_xlsx.json",
            "header": ["Название", "А2", "А3", "Код"]
        }
    },
    # empty input file -> no output csv file
    "csv_empty_csv": {
        "tags": ["csv", "empty"],
        "fi": {"file": "test_empty.csv"},
        "fo": {
            "file": "dfifo_test_empty_csv.csv",
            "header": ["Название", "А2", "А3", "Код"]
        }
    },
    "json_empty_csv": {
        "tags": ["json", "empty"],
        "fi": {
            "file": "test_empty.json",
            "transformer": lambda row: (row["code"], row.get("alpha2"), row.get("alpha3"), row["name"])
        },
        "fo": {
            "file": "dfifo_test_empty_json.csv",
            "header": ["Код", "А2", "А3", "Название"]
        }
    },
    "xlsx_empty_csv": {
        "tags": ["xlsx", "empty"],
        "fi": {"file": "test_empty.xlsx"},
        "fo": {
            "file": "dfifo_test_empty_xlsx.csv",
            "header": ["Название", "А2", "А3", "Код"]
        }
    },
    # empty input file -> no output xlsx file
    "csv_empty_xlsx": {
        "tags": ["csv", "empty"],
        "fi": {"file": "test_empty.csv"},
        "fo": {
            "file": "dfifo_test_empty_csv.xlsx",
            "header": ["Название", "А2", "А3", "Код"]
        }
    },
    "json_empty_xlsx": {
        "tags": ["json", "empty"],
        "fi": {
            "file": "test_empty.json",
            "transformer": lambda row: (row["code"], row.get("alpha2"), row.get("alpha3"), row["name"])
        },
        "fo": {
            "file": "dfifo_test_empty_xlsx.csv",
            "header": ["Код", "А2", "А3", "Название"]
        }
    },
    "xlsx_empty_xlsx": {
        "tags": ["xlsx", "empty"],
        "fi": {"file": "test_empty.xlsx"},
        "fo": {
            "file": "dfifo_test_empty_xlsx.xlsx",
            "header": ["Название", "А2", "А3", "Код"]
        }
    },
    # empty zipped input file -> no output file
    "zip_zero_json": {
        "tags": ["zip", "empty"],
        "fi": {"file": "test_empty.zip"},
        "fo": {
            "file": "dfifo_test_empty_zip.json",
            "header": ["Название", "А2", "А3", "Код"]
        }
    },
    "zip_zero_csv": {
        "tags": ["zip", "empty"],
        "fi": {"file": "test_empty.zip"},
        "fo": {
            "file": "dfifo_test_empty_zip.csv",
            "header": ["Название", "А2", "А3", "Код"]
        }
    },
    "zip_zero_xlsx": {
        "tags": ["zip", "empty"],
        "fi": {"file": "test_empty.zip"},
        "fo": {
            "file": "dfifo_test_empty_zip.xlsx",
            "header": ["Название", "А2", "А3", "Код"]
        }
    },
    "csv_text_csv": {
        "tags": ["csv", "text"],
        "fi": {
            "file": "test.csv",
            "text_lines": True
        },
        "fo": {
            "file": "dfifo_test_text.csv",
            "text_lines": True
        }
    },
    "json_text_json": {
        "tags": ["json", "text"],
        "fi": {
            "file": "test.json",
            "text_lines": True
        },
        "fo": {
            "file": "dfifo_test_text.json",
            "text_lines": True
        }
    },
    "xxx_text_xxx": {
        "tags": ["xxx", "text"],
        "fi": {
            "file": "test_xxx.dat",
            "text_lines": True
        },
        "fo": {
            "file": "dfifo_test_text.dat",
            "text_lines": True
        }
    },
    "csv_nested_00_csv": {
        "tags": ['csv', 'unnest'],
        "fi": {
            "file": "test_nested_00.csv",
            "transformer": \
                lambda row: [(row[0], n) for n in row[1].split(',')] if row[1] else [],
        },
        "fo": {
            "file": "dfifo_test_unnested_00.csv",
            "header": ["level", "name"],
        }
    },
    "csv_nested_00_json": {
        "tags": ['csv', 'unnest'],
        "fi": {
            "file": "test_nested_00.csv",
            "transformer": \
                lambda row: [(row[0], n) for n in row[1].split(',')] if row[1] else [],
        },
        "fo": {
            "file": "dfifo_test_unnested_00.json",
            "header": ["level", "name"],
        }
    },
    "json_nested_01_csv": {
        "tags": ['json', 'unnest'],
        "fi": {
            "file": "test_nested_01.json",
            "encoding": "UTF-8",
            "transformer": \
                lambda row: [(row['region'], n['code'], n['name'], n['alpha2'], n['alpha3']) for n in row['countries']] if row['countries'] else [(row['region'], None, None, None, None)]
        },
        "fo": {
            "file": "dfifo_test_unnested_01.csv"
        }
    },
    "json_nested_01_json": {
        "tags": ['json', 'unnest'],
        "fi": {
            "file": "test_nested_01.json",
            "encoding": "UTF-8",
            "transformer": \
                lambda row: [(row['region'], n['code'], n['name'], n['alpha2'], n['alpha3']) for n in row['countries']] if row['countries'] else [(row['region'], None, None, None, None)]
        },
        "fo": {
            "file": "dfifo_test_unnested_01.json",
            "header": ['region', 'code', 'name', 'alpha2', 'alpha3']
        }
    },
    "dat_xxx_csv": {
        "tags": ["xxx", "dat"],
        "fi": {
            "file": "test_xxx.dat",
            "text_lines": True,
            "transformer": lambda line: (line[0:2], line[2:5], line[5:8], line[8:].strip())
        },
        "fo": {
            "file": "dfifo_test_dat_xxx.csv"
        }
    },
    "--template": {
        "fi": {
            "file": "test.csv",
        },
        "fo": {
            "file": "dfifo_test.json"
        }
    },
}
