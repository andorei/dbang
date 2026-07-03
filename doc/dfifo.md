# dfifo. Transformimg Data from Files to Files

	version 0.4.0

The `dfifo` utility reads input data like `dput` and writes output data like `dget`.

It reads CSV, XLSX, JSON files and other text files according to a spec in config file, and writes data to CSV, XLSX, JSON or HTML files. Data may be read from/written to a single file or a series of files. Input and/or output files may be optionally zipped.

* [Test Files](#test-files)
* [Basic Usage](#basic-usage)
* [Selecting Rows and Fields](#selecting-rows-and-fields)
* [Processing Data from JSON file](#processing-data-from-json-file)
* [Unpacking Nested List](#unpacking-nested-list)
* [Processing Special Text Files](#processing-special-text-files)
* [Three Types of `transformer` Functions](#three-types-of-transformer-functions)
* [Command Line Arguments](#command-line-arguments)
* [Config File Parameters](#config-file-parameters)
* [Spec Parameters](#spec-parameters)

## Test Files

Test files are found in the `in` directory. Let's look at them to better understand the explanations that follow.

Files `test` with extensions `.xlsx`, `.csv`, `.json` and `.dat` contain the list of countries with 4 fields:

* country name,
* 2-symbol country code,
* 3-symbol country code,
* numeric country code.

The file series with names `test_000001`,  `test_000002`,  `test_000003` and extensions `.csv`, `.xlsx` or `.json` contain the same list of countries divided into 3 parts.

Here are the first five and the last five lines from file `test.csv`:

```
Afghanistan;AF;AFG;004
Aland Islands;AX;ALA;248
Albania;AL;ALB;008
Algeria;DZ;DZA;012
American Samoa;AS;ASM;016
...
Wallis and Futuna Islands;WF;WLF;876
Western Sahara;EH;ESH;732
Yemen;YE;YEM;887
Zambia;ZM;ZMB;894
Zimbabwe;ZW;ZWE;716
```

The first five and the last five lines from file `test.json`:

```
[
{"name": "Afghanistan", "alpha2": "AF", "alpha3": "AFG", "code": "004"},
{"alpha2": "AX", "alpha3": "ALA", "code": "248", "name": "Aland Islands"},
{"alpha3": "ALB", "code": "008", "name": "Albania", "alpha2": "AL"},
{"code": "012", "alpha2": "DZ",  "name": "Algeria", "alpha3": "DZA"},
{"name": "American Samoa", "code": "016", "alpha2": "AS", "alpha3": "ASM"},
...
{"name": "Wallis and Futuna Islands", "alpha2": "WF", "alpha3": "WLF", "code": "876"},
{"alpha2": "EH", "name": "Western Sahara", "alpha3": "ESH", "code": "732"},
{"alpha2": "YE", "alpha3": "YEM", "name": "Yemen", "code": "887"},
{"alpha2": "ZM", "alpha3": "ZMB", "code": "894", "name": "Zambia"},
{"code": "716", "name": "Zimbabwe", "alpha2": "ZW", "alpha3": "ZWE"}
]
```

Notice that fields of JSON objects have no particular order.

## Basic Usage

Below are specifications from config file `dfifo_test.py`. In a `dfifo` spec
* dictionary `fi` contains parameters for input file found in directory `IN_DIR`,
* dictionary `fo` contains parameters for output file saved in directory `OUT_DIR`,

The extensions of input and output files in parameter `"file"` determine file format.

```
IN_DIR = os.path.join(os.path.dirname(__file__), '..', 'in')
OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'out')

specs = {
    "csv_xlsx": {
        "fi": {"file": "test.csv"},
        "fo": {
            "file": "dfifo_test_csv.xlsx",
            "header": ["Name", "А2", "А3", "Code"]
        }
    },
    "csv_parts_json": {
        "fi": {"file": "test_000???.csv"},
        "fo": {
            "file": "dfifo_test_csv_parts.json",
            "header": ["Name", "А2", "А3", "Code"]
        }
    },
    "csv_split_json": {
        "fi": {"file": "test.csv"},
        "fo": {
            "file": "dfifo_test_csv_split_%(seqn)06i.json",
            "header": ["Name", "А2", "А3", "Code"],
            "rows_per_file": 100
        }
    },
    "csv_selected_csv": {
        "fi": {
            "file": "test.csv",
            "transformer": \
                lambda row: (row[3], row[0]) if row[0][0] in 'AEIOU' else None
        },
        "fo": {
            "file": "dfifo_test_csv_selected.csv",
            "header": ["code", "name"]
        },
    }
    ...
}
```

Parameter `"fo/header"` sets 
* column titles for XLSX output file,
* names for JSON name/value pairs for JSON output file,
* field names for the first line of CSV output file.

The `"file"` parameter in spec `"csv_parts_json"` sets [glob-pattern](https://docs.python.org/3/library/glob.html) for a series of files to load. The matched files will be loaded in alphabetical order.

The `"file"` parameter in spec `"csv_split_json"` sets [`printf`-style template](https://docs.python.org/3/library/stdtypes.html#printf-style-string-formatting) for generating name(s) of output file(s). The template may contain the following parenthesized names:
* `date` – current date in ISO format `'%Y-%m-%d`,
* `datetime` – current date and time in format `'%Y-%m-%d-%H-%M-%S'`:
* `seqn` – number of file in a series of output files,
* `user` – either username set in CLI with option `--user`, or the name of OS user executing `dfifo`.

The `"rows_per_file"` parameter sets the number of rows to write to a single file. Given that the input file `test.csv` contains 200+ lines, the execution of spec `"csv_split_json"` will create 3 files named according to template in parameter `"file"`.

Parameter `"fi/transformer"` in spec `"csv_selected_csv"` defines a function to convert a tuple of values representing a CSV line into a tuple of values that goes to the output file.

Data from XLSX, CSV and other text files are processed line by line in the order of lines in a file; from a JSON file – object by object in the order of JSON objects in JSON array.

The processing data with `dfifo` optionally includes:

1. checking if a line meets a certain condition to be passed on to the output file;
2. building a list of fields to pass on to the output file  – when data comes from JSON file or when we only need some of the fields.

That said the simplest spec for `dfifo`
* only contains input and output file names,
* reads all fields of all rows from input file(s) and writes them to the output file(s).

See test config file `test/dfifo_test.py` to familiarize yourself with all the parameters.

## Selecting Rows and Fields

Optional spec parameter `"skip_lines"` specifies number of lines to skip at the beginning of an input file.  For example, value `1` makes `dfifo` skip the first line (presumably a header) when reading CSV or XLSX files.

Optional spec parameter `"fi/transformer"` defines a function that allows
* select a subset of data fields,
* select only rows that meet a certain condition.

The `"fi/transformer"` parameter either sets a lambda-function or a regular Python function defined in the same config file.

The specification below demonstrates just such a selection:

```
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
}
```

Function set with parameter `"fi/transformer"` generally
* is called for each line of input file,
* gets as an argument a list or a tuple of all fields' values of a line, or a text line as is if `"fi/text_lines"` is set to `True`,
* should return a list or a tuple of fields' values that should go to the output file, or a text line as is if `"fo/text_lines"` is set to `True`,
* or return `None`, in which case the line is skipped and does not go to the output file.

The lambda-function in the above spec returns a tuple `(<numeric country code>, <contry name>)` for lines where the country name starts with a vowel, and `None` for other lines. Thus only some fields of some lines go to the output file.

## Processing Data from JSON file

The `"fi/transformer"` parameter is mandatory in a spec that reads data from a JSON file. The thing is that the fields of JSON objects could be found in a file in any order (see [Test Files](#test-files)).

An example specification to transform data from JSON file into CSV file:

```
"json_csv": {
    "tags": ["json"],
    "fi": {
        "file": "test.json",
        "transformer": lambda row: (row["code"], row.get("alpha2"), row.get("alpha3"), row["name"])
    },
    "fo": {"file": "dfifo_test_json.csv"}
}
```

## Unpacking Nested List

Each line of test data file `test_nested_00.csv` has two fields:
1. Floor number,
2. List of stores on the floor.

Here is the file content:

```
1;ABC,Bonus,Cosmos,Domus,Eidos
2;Focus,Iris
3;Lotus
4;
```

The second field is actually a nested data structure. This list should be unnested, or unpacked, in order to pass on to the output file rows without any nested structures. To achieve this, the `"transformer"` parameter below defines the function that gets a tuple as input and returns a list of tuples each representing a row:

```
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
}
```

Here is the content of the output file:

```
[
{"level": "1", "name": "ABC"},
{"level": "1", "name": "Bonus"},
{"level": "1", "name": "Cosmos"},
{"level": "1", "name": "Domus"},
{"level": "1", "name": "Eidos"},
{"level": "2", "name": "Focus"},
{"level": "2", "name": "Iris"},
{"level": "3", "name": "Lotus"}
]
```

## Processing Special Text Files

Sometimes you need to transform data from text files of a special format into one of conventional formats, for example,
* an input file, where a few lines at the beginning describe data that follows, or
* an input file, where lines have fields of fixed length without any delimiters.

Spec parameter `"text_lines": True` tells `dfifo` to pass lines from input text file "as is" to function specified in spec parameter `"fi/transformer"`. Lines are passed as Python strings without any attempted splitting into fields.

Then, the `"fi/transformer"` function parses the string and returns a list or a tuple of fields' values to pass on to the output file.

Test data file `test_xxx.dat` contains data on world countries in lines of the following format:
1. 2-letter country code – positions from 1 to 2,
2. 3-letter country code – positions from 3 to 5,
3. 3-digit country code – positions from 6 to 8,
4. country name – positions from 9 to the end of line.

Here are the first five and the last five lines from the file:

```
AFAFG004Afghanistan
AXALA248Aland Islands
ALALB008Albania
DZDZA012Algeria
ASASM016American Samoa
...
WFWLF876Wallis and Futuna Islands
EHESH732Western Sahara
YEYEM887Yemen
ZMZMB894Zambia
ZWZWE716Zimbabwe
```

The spec below transfers to the output CSV file four separate fields extracted from input lines with function `"fi/transformer"`:

```
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
```

## Three Types of `transformer` Functions

Functions set with parameter `"fi/transformer"` may be of three kinds:

| Function kind                 | Description                                                                                                                                                                     |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `<func>(row)`                 | `row` - a list or a tuple of fields' values, or a line from input file as is if `"fi/text_lines": True`                                                                         |
| `<func>(line_no, row)`        | `line_no` - number of line from a file, `row` - a list or a tuple of fields' values, or a line from input file as is if `"fi/text_lines": True`                                 |
| `<func>(run_no, row_no, row)` | `run_no` - run ID, `row_no` - number of a line through series of files, `row` - a list or a tuple of fields' values, or a line from input file as is if `"fi/text_lines": True` |

When reading data from a single file, the number of file line `line_no` and the number of read line `row_no` are the same.

However, when reading data from a series of files, the number of file line `line_no` resets with each new file, while the number of read line `row_no` keeps incrementing through all files of a series.

Functions `<func>(line_no, row)` allow processing text files where first few lines contain metadata describing data that follows. See spec `"xxx_csv"` in test config files.

Functions `<func>(run_no, row_no, row)` allow processing series of input files.

## Command Line Arguments

```
$ ./dfifo.py --help
usage: dfifo.py [-h] [-v] [-d] [-f] [-i FI] [-o FO] [-u USER] cfg_file [spec]

Save data from input file(s) to output file(s), as specified in cfg-file specs.

positional arguments:
  cfg_file              cfg-file name
  spec                  spec name, defaults to "all"

options:
  -h, --help            show this help message and exit
  -v, --version         show program's version number and exit
  -d, --delete          delete processed input file(s)
  -f, --force           process input file(s) unconditionally
  -i FI, --fi FI        input file(s)
  -o FO, --fo FO        output file(s)
  -u USER, --user USER  set username

Thanks for using dfifo.py!
```

The mandatory argument is config file name `cfg_file`.

If `spec` is provided then the utility executes only the named spec or specs with the given tag. If `spec` is omitted then all specs from the config file are executed.

Option `-d` or `--delete` instructs the `dfifo` utility to delete input file(s) after executing the spec. An input file will not be deleted if errors occur while executing the spec.

Option `-f` or `--force` instructs the `dfifo` utility to read data from files even in case when these files had been already processed by the utility. The `dfifo` registers modification times of loaded files in a special file `~/.<cfg-file>.json` and by default only reads file(s) that had not been processed earlier.

Option `-i` or `--fi` overrides input file name specified in spec parameter `fi/file`. File name extension determines the data format.

Option `-o` or `--fo` overrides output file name specified in spec parameter `fo/file`. File name extension determines the data format.

Option `-u` or `--user` allows setting username that may be used as a part of output file name.

## Config File Parameters

Config file parameters are variables with names in uppercase that define context for executing specs from that config file. See also [Config Files Structure](config.md).

The `dfifo` config file parameters are described below.

| Parameter          | Default Value                            | Description                                                |
| ------------------ | ---------------------------------------- | ---------------------------------------------------------- |
| `DEBUGGING`        | `False`                                  | Debugging mode?                                            |
| `LOGGING`          | = DEBUGGING                              | Write to log file?                                         |
| `PARALLEL_WORKERS` | 1                                        | Number of threads to run specs in parallel.                |
| `LOG_DIR`          | `./`                                     | Path to the directory with log files.                      |
| `IN_DIR`           | `./`                                     | Path to the directory with input files to load.            |
| `OUT_DIR`          | `./`                                     | Path to the directory with output files.                   |
| `ENCODING`*        | `locale.getpreferredencoding()`          | Input file(s) encoding.                                    |
| `CSV_DIALECT`*     | `excel`                                  | CSV dialect as defined in Python module `csv`, or `naive`. |
| `CSV_DELIMITER`*   | `csv.get_dialect(CSV_DIALECT).delimiter` | CSV fields delimiter.                                      |
\* config file parameter marked with asterisk may be overridden at spec level with a corresponding spec parameter.

Additionally to CSV dialects in Python module `csv`, `CSV_DIALECT` parameter accepts `"naive"` dialect. This dialect writes and reads field values as they are, without any screening and/or quoting. Absence of field delimiters in field values is a responsibility of those who use such files.

## Spec Parameters

Specs are found in a config file in the `specs` dictionary and contain **spec parameters**. See also [Config Files Structure](config.md).

Spec parameters for `dfifo` utility are described below. If not explicitly described as mandatory, a spec parameter is optional and may be omitted.

| Spec Parameter            | Description                                                                                                                                                                                                                                                                 |
| ------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `"tags"`                  | List of tags attached to the spec.                                                                                                                                                                                                                                          |
| `"doc"`                   | Short description/comment on the spec.                                                                                                                                                                                                                                      |
| `"fi/force"`              | Read data from input files unconditionally.                                                                                                                                                                                                                                 |
| `"fi/file"`               | Name of the input file(s), where extension determines the data format. Use [glob-pattern](https://docs.python.org/3/library/glob.html) to set names for a series of files. Might be overridden with `--fi` command line key.                                                |
| `"fi/skip_lines"`         | Number of lines (`int`) to skip at the beginning of input files.                                                                                                                                                                                                            |
| `"fi/skip_bad_files"`     | Continue processing a series of files if a file with errors occurred.                                                                                                                                                                                                       |
| `"fi/encoding"`           | Input file encoding. At spec level this parameter overrides config file parameter `ENCODING`.                                                                                                                                                                               |
| `"fi/csv_dialect"`        | CSV dialect as defined in Python module `csv`. At spec level this parameter overrides config file parameter `CSV_DIALECT`.                                                                                                                                                  |
| `"fi/csv_delimiter"`      | CSV fields delimiter. At spec level this parameter overrides config file parameter `CSV_DELIMITER`.                                                                                                                                                                         |
| `"fi/text_lines"`         | Read lines of input files as is regardless input files extension?                                                                                                                                                                                                           |
| `"fi/transformer"`        | A function of a list of Python functions to transform a line from input file into a line for output file.                                                                                                                                                                   |
| `"fo/file"`               | Name of the output file(s), where extension determines the data format. Use [`printf`-style template](https://docs.python.org/3/library/stdtypes.html#printf-style-string-formatting) to set names for a series of files. Might be overridden with `--fo` command line key. |
| `"fo/rows_per_file"`      | Number of rows (`int`) written to a separate file – in order to put data into a series of files of small size; -1 means a n output file for each input file.                                                                                                                |
| `"fo/header"`             | A list of field names.                                                                                                                                                                                                                                                      |
| `"fo/text_lines"`         | Write lines of input files as is regardless output files extension?                                                                                                                                                                                                         |
| `"fo/csv.encoding"`       | CSV output file encoding. At spec level this parameter overrides config file parameter `ENCODING`.                                                                                                                                                                          |
| `"fo/csv.dialect"`        | CSV dialect as defined in Python module `csv`. At spec level this parameter overrides config file parameter `CSV_DIALECT`.                                                                                                                                                  |
| `"fo/csv.delimiter"`      | CSV fields delimiter. At spec level this parameter overrides config file parameter `CSV_DELIMITER`.                                                                                                                                                                         |
| `"fo/csv.dec_separator"`  | Decimal separator for numbers in CSV file. The default is `.` (dot).                                                                                                                                                                                                        |
| `"fo/json.encoding"`      | JSON output file encoding. At spec level this parameter overrides config file parameter `ENCODING`.                                                                                                                                                                         |
| `"fo/json.template"`      | Name of Jinja2 template file used to build JSON output file. The default is the embedded template like the one in file `dfifo_sample.json.jinja`.                                                                                                                           |
| `"fo/html.encoding"`      | HTML output file encoding. At spec level this parameter overrides config file parameter `ENCODING`.                                                                                                                                                                         |
| `"fo/html.template"`      | Name of Jinja2 template file used to build HTML output file. The default is the embedded template like the one in file `dfifo_sample.html.jinja`.                                                                                                                           |
| `"fo/html.title"`         | Title for HTML file. The default is spec name.                                                                                                                                                                                                                              |
| `"fo/html.dec_separator"` | Decimal separator for numbers in HTML file. The default is `.` (dot).                                                                                                                                                                                                       |
