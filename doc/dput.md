# dput. Loading Data from File into Database

	version 0.3

To load data from your files to your DB first run test spec from test config file `dput-test-<source>.py` against your DB. Then `dput` will create tables `ida` and `ida_lines` in the DB, and these tables will be used to load data.

The `dput` utility loads data from CSV, XLSX, JSON files and other text files according to a spec in config file. Data may be loaded from a single file or from a series of files. If input files are zipped then they are automatically unzipped before loading data.

* [Test Files to Load](#test-files-to-load)
* [Basic Usage](#basic-usage)
* [Loading Procedure](#loading-procedure)
* [Loading Data into the Default Table](#loading-data-into-the-default-table)
* [Loading Selected Rows and Fields](#loading-selected-rows-and-fields)
* [Loading Data from JSON file](#loading-data-from-json-file)
* [Loading Data into User-Defined Table](#loading-data-into-user-defined-table)
* [Loading Data with Unpacking Nested List](#loading-data-with-unpacking-nested-list)
* [Loading Data into Multiple User-Defined Tables](#loading-data-into-multiple-user-defined-tables)
* [Loading Nested Tables into the Default Table](#loading-nested-tables-into-the-default-table)
* [Loading Special Text Files](#loading-special-text-files)
* [Three Types of `insert_data` Functions](#three-types-of-insert_data-functions)
* [Command Line Arguments](#command-line-arguments)
* [Config File Parameters](#config-file-parameters)
* [Spec Parameters](#spec-parameters)

## Test Files to Load

Files for test loads are found in the `in` directory. Let's look at them to better understand the following explanations.

Files `test` with extensions `.xlsx`, `.csv`, `.json` and `.dat` contain the list of countries with 4 fields:

* country name,
* 2-symbol country code,
* 3-symbol country code,
* numeric country code.

The file series with names `test_000001`,  `test_000002`,  `test_000003` and extensions `.csv`, `.xlsx` или `.json` contain the same list of countries divided into 3 parts.

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

Here are example specs for SQLite to load data from test data files into table `ida_lines`.

The `"file"` parameter sets the name of a file (found in the `IN_DIR` directory) and its format:

```
# hello-dput.py

IN_DIR = os.path.join(os.path.dirname(__file__), '..', 'in')
SOURCE = sources['sqlite-source']

specs = {
    "hello-csv": {
        "file": "test.csv"
    },
    "hello-xlsx": {
        "file": "test.xlsx"
    },
    "hello-json": {
        "file": "test.json",
        "insert_data": lambda row: (row["code"], row["name"], row["alpha2"], row["alpha3"])
    },
    "hello-zip": {
        "file": "test_zip.zip"
    },
    "hello-series": {
        "file": "test_000???.csv",
        "insert_data": lambda row: (row[3], row[0], row[1])
    },
    ...
}
```

The `"file"` parameter in spec `"hello-zip"` tells `dput` to first unzip the file and then load it. A `zip` archive should contain a single file with the same name as `zip`-file and one of extensions `.csv`, `.xlsx` and `.json`.

The `"file"` parameter in spec `"hello-series"` sets [glob-pattern](https://docs.python.org/3/library/glob.html) for a series of files to load. The matched files will be loaded in alphabetical order.

The `"insert_data"` parameter in spec `"hello-json"` defines function to transform JSON object into data row – a list or tuple of values – to be inserted into a database table. The function's input argument is a Python `dict` representing a JSON object. 

The `"insert_data"` parameter in spec `"hello-series"` demonstrates the possibility of selecting and rearranging fields of CSV-file. The function's input argument is a list or tuple of values of CSV-file fields.

## Loading Procedure

Data from `xlsx`, `csv` and other text files are loaded line by line in the order of lines in a file; from a `json` file – object by object in the order of JSON objects in JSON array.

The procedure of loading data with `dput` optionally includes:

1. checking if a line meets a certain condition to be loaded;
2. building a list of fields to insert into a database table  – when data comes from `json` file or when we only need some of the fields;
3. checking if all the rows inserted into a database table meet certain conditions, including consistency with existent data,
4. copying (and transforming) rows from an interface table into target database tables where the data belong.

If rows loaded into interface table do not meet integrity or consistency requirements, they will not be loaded into target database tables and a user will get error message(s).

That said the simplest spec for `dput` 
* only contains file name to load,
* does not evoke steps 1–4 described above,
* allows loading all fields of all rows from input files into the default interface table `ida_lines`.

Tables `ida` and `ida_lines` are automatically created in a database when executing specs from test config files and are afterward used by default for all user defined specifications. Here is their structure (in PostgreSQL DB):

```
create table if not exists ida (
    iload serial not null,
    idate timestamptz not null default now(),
    istat smallint not null default 0,
    imess varchar(4000),
    entity varchar(50) not null,
    ifile varchar(256) not null,
    iuser varchar(30),
    arg1 varchar(4000),
    arg2 varchar(4000),
    ...
    arg9 varchar(4000),
    primary key (iload)
);

create table if not exists ida_lines (
    iload int not null,
    iline int not null,
    ntable smallint not null default -1,
    nline int not null default -1,
    istat smallint not null default 0,
    ierrm varchar(4000),
    c1 varchar(4000),
    c2 varchar(4000),
    ...
    ...
    ...
    c100 varchar(4000),
    primary key (iload, iline, ntable, nline),
    foreign key (iload) references ida (iload) on delete cascade
);
```


Table `ida` keeps the facts of loads, in particular:

* load identifier `iload`,
* load time `idate`,
* load status `istat`,
* name of a loaded file `ifile`,
* name of a spec `entity`,
* optional message `imess` written on load completion.

Table `ida_lines` keeps all the lines from the file, and also

* load identifier `iload`,
* line number `iline`,
* "nested table" number `ntable`,
* "nested table" line number `nline`,
* line status `istat` and
* error message `ierrm` – in case when error occurred.

In order to load data in other table(s) than `ida_lines` you have to explicitly provide SQL `insert` statement (or stored procedure call) in a spec. See further details in [Loading Data into User-Defined Table](#loading-data-into-user-defined-table).

Data loaded in DB via the interface tables `ida` and `ida_lines` is not deleted from these tables right away. The config file parameter

```
PRESERVE_N_LOADS = 10
```

tells `dput` to keep 10 last loads for each spec in the interface tables. When user runs the 11-th load the oldest of the previous 10 loads will be deleted. If you set `PRESERVE_N_LOADS` to 0, then `dput` will delete the data from interface tables right after executing a spec.

Keeping loaded data in interface tables for a while may turn helpful when you need to manually check what data was loaded by users or what errors were detected.

Test config files `dput-test-<source>.py` contain comments on all the spec parameters. Read it carefully and familiarize yourself with all the parameters.

## Loading Data into the Default Table

Let's see how `dput` works – using test file `test.csv` and specs from the config file `dput-test-postgres.py`:

```
specs = {
    ...
    "csv_ida_test": {
        "source": "postgres-source",
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
            # just teardown
            "delete from ida where iload = %s"
        ]
    },
    ...
}
```

According to the above spec, `dput` utility

1. loads data from file `test.csv` into table `ida_lines` in the database specified in parameter `"source"`, and inserts into table `ida` a row with load metadata;
2. executes SQL statements from `"validate_actions"` list to verify that rows loaded into `ida_lines` comply to the requirements;
3. if the verification is success then
	* executes SQL statements from `"process_actions"` list (here might be calls to stored procedures) to copy data from `ida_lines` into target tables;
	else
	* writes error messages to the log file.

When loading data in table `ida_lines` the four fields' values will be put in columns `c1`, `с2`, `с3` and `с4`, respectfully. As table `ida_lines` has 100 columns `c1`, .. `c100`, the number of fields in a file to load may not be greater than 100.

The status of lines `istat` right after loading (step 1) equals 0 - Waiting to be processed.

List `"validate_actions"` contains SQL statement to verify data compliance to the requirements. These statements get executed by `dput` (step 2) after the lines are loaded into table `ida_lines`.

The three `update` statements in the spec above check, respectfully:

* that all 4 fields are not empty,
* that the length of 2-symbol country code is 2,
* that the length of 3-symbol country code is 3.

If the data does not meet requirements the line in `ida_lines` gets marked as erroneous (`istat = 2`), and error message is put into the field `ierrm`. In this case the processing is stopped after executing `"validate_actions"`, and `dput` writes bad line numbers and error messages to the log file.

If `"validate_actions"` do not detect errors then `dput` executes SQL statements from the list `"process_actions"` (step 3) and inserts the verified data from `ida_lines` into target tables. In the test spec the list `"process_actions"` contains a single statement that deletes loaded data from tables `ida` and `ida_lines`. Thus, instead of inserting data into target tables, test data is just deleted from the DB.

SQL statements in lists `"validate_actions"` and `"process_actions"` contain a bind variable for a load identifier `iload`. While bind variables for PostgreSQL are designated with `%s`, bind variables for other DBs may be designated differently, depending on the Python DB-API module for a database. See test config files for other databases `dput-test-sqlite.py`, `dput-test-oracle.py`, `dput-test-mysql.py`.

If at least one row in `ida_lines` were marked as erroneous, then `dput` sets the load status `ida.istat` to 2 - Error. If all the loaded rows were processed successfully then `dput` sets the load status `ida.istat` to 1 - Processing succeeded.

## Loading Selected Rows and Fields

Optional spec parameter `"skip_lines"` specifies number of lines to skip at the beginning of an input file.  For example, value `1` makes `dput` skip the first line (presumably a header) when loading `csv` or `xlsx` files.

Optional spec parameter `"insert_data"` defines a function that allows
* load only explicitly chosen fields,
* load only rows that meet a certain condition.

The `"insert_data"` parameter either sets a lambda-function or a regular Python function defined in the same config file.

Specification `"selected_ida_test"` below demonstrates just such a selective loading:

```
"selected_ida_test": {
    "file": "test.csv",
    #
    # tuple of values to insert into ida_lines table
    #
    "insert_data": lambda row: (row[3], row[0]) if row[0][0] in 'AEIOU' else None
}
```

Function set with parameter `"insert_data"`,
* is called for each line of input file,
* gets as an argument a list or a tuple of all fields' values of a line,
* returns a list or a tuple of fields' values that should be loaded,
* or return `None`, in which case the line is skipped and not loaded.

The lambda-function in the above spec returns a tuple `(<numeric counrty code>, <contry name>)` for lines where the country name starts with a vowel, and `None` for other lines. Thus, only some fields of some lines are going to be loaded.

## Loading Data from JSON file

The `"insert_data"` parameter is mandatory in a spec that loads data from a JSON file, even in case when rows are loaded into the default table `ida_lines`. The thing is that the fields of JSON objects – or JSON file "rows" – could be put in any order (see [Test Files to Load](#test-files-to-load)).

An example specification to load data from `test.json` into table `ida_lines`:

```
"json_ida_test": {
	"file": "test.json",
	#
	# tuple of values to insert into ida_lines table
	#
	"insert_data": lambda row: (row["code"], row["name"], row["alpha2"], row["alpha3"])
}
```

## Loading Data into User-Defined Table

Instead of loading data rows into table `ida_lines` it is possible to load them into other table. To make `dput` load data into such a table, you should set spec parameters `"insert_actions"` and `"insert_data"`.

Suppose you have interface table `test` designed to accept data on countries:

```
create table if not exists test (
    code varchar(3) not null,
    name varchar(50) not null,
    alpha2 char(2),
    alpha3 char(3)
)
```

The following spec allows loading data from file `test.csv` into table `test`:

```
"csv_test_test": {
	"file": "test.csv",
	"insert_actions": """
		insert into test (code, name, alpha2, alpha3)
		values (%s, %s, %s, %s)
	""",
	"insert_data": lambda row: (row[3], row[0], row[1], row[2])
}
```

Spec parameter `"insert_actions"` defines SQL statement `insert` to insert a row into table `test`. As the order of columns in `insert` statement differs from the order of fields in the CSV-file (see [Test Files to Load](#test-files-to-load)), the `"insert_data"` parameter defines a Python lambda-function which rearranges the fields in the order required by the SQL statement.

If you specify columns in the `insert` statement in the order of fields in CSV-file, then `"insert_data"` parameter may be omitted:

```
"csv_test_test": {
	"file": "test.csv",
	insert_statement": """
		insert into test (name, alpha2, alpha3, code)
		values (%s, %s, %s, %s)
	"""
}
```

In this case, it is important that each of the four fields of a CSV file line has a corresponding column in the table `test`. Whereas, the `"insert_data"` lambda-function allows choosing (and rearrange) for insertion any subset of the fields.

Even when loading data in a user-defined table specified in the `"insert_actions"`, the `dput` utility registers the load in the `ida` table with status 0 - waiting for being processed.

If SQL statements in the lists `"validate_actions"` and `"process_actions"` set the load status in the column `ida.istat` to 2 - error, and put an error message in the column `ida.imess`, then `"dput"` writes that error message in the log file. Otherwise, the load status is set to 1 - processing succeeded, and a success message is written in the log file.

## Loading Data with Unpacking Nested List

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

The second field is actually a nested data structure. This list should be unnested, or unpacked, in order to load into a database table rows without any nested structures. To achieve this, the `"insert_data"` parameter of spec `"nested_00_ida"` defines the function that gets a tuple as input and returns a list of tuples each representing a row to load:

```
"nested_00_ida": {
    "file": "test_nested_00.csv",
    "insert_data": \
        lambda row: [
            (row[0], n) for n in row[1].split(',')
        ] if row[1] else []
}
```

Here is the result of loading data into table `ida_lines` with spec `nested_00_ida`:

```
|iload|iline|ntable|nline|c1 |c2    |
|-----|-----|------|-----|---|------|
|42   |1    |0     |1    |1  |ABC   |
|42   |1    |0     |2    |1  |Bonus |
|42   |1    |0     |3    |1  |Cosmos|
|42   |1    |0     |4    |1  |Domus |
|42   |1    |0     |5    |1  |Eidos |
|42   |2    |0     |1    |2  |Focus |
|42   |2    |0     |2    |2  |Iris  |
|42   |3    |0     |1    |3  |Lotus |
```

Notice that
* column `iline` contains line number from the input file, 
* column `ntable` contains number of unpacked nested structure (or "nested table"),
* column `nline` contains element number of unpacked structure (or row number of "nested table").

## Loading Data into Multiple User-Defined Tables

Files of JSON format allow representing nested data structures that map onto more than one table in a relational database.

For example, test data file `test_nested_01.json` contains seven JSON objects with two fields:
* `"region"` – name of a world region or a continent,
* `"countries"` – array of JSON objects representing countries of a region.

Here are the first two JSON objects in the file:

```
{
    "region": "Nowhere",
    "countries": []
},
{
    "region": "Antarctica",
    "countries": [
		{"name": "Antarctica", "alpha2": "AQ", "alpha3": "ATA", "code": "010"},
		{"name": "Bouvet Island", "alpha2": "BV", "alpha3": "BVT", "code": "074"}
    ]
},
{
    "region": "Africa",
    "countries": [
		{"name": "Comoros", "alpha2": "KM", "alpha3": "COM", "code": "174"},
		{"name": "Djibouti", "alpha2": "DJ", "alpha3": "DJI", "code": "262"},
		...
```

The data in the files naturally maps onto two tables:
1. (parent) table of regions, and
2. (child) table of countries referring to the table of regions.

In order to load data of a single line (JSON object) into multiple tables, you need to provide for each table an `insert` statement and values to insert:

```
"nested_01_test": {
    "file": "test_nested_01.json",
    "insert_actions": [
        "insert into test_region (region, contains) values (?, ?)",
        "insert into test_countries (region, code, name) values (?, ?, ?)"
    ],
    "insert_data": [
        lambda row: (row['region'], len(row['countries'])),
        lambda row: [
                (row['region'], n['code'], n['name']) \
                for n in row['countries']
            ] if row['countries'] else []
    ]
}
```
Here, spec parameters `"insert_actions"` and `"insert_data"` are a list of strings and a list of functions, respectfully. Each `insert` statement in the `"insert_actions"` list has a corresponding function in the `"insert_data"` list.

Notice that the first function returns a tuple representing a row for the (parent) table of regions. While the second function returns a list of tuples representing a set of rows for the (child) table of countries.

Loading data of a single input line into multiple tables may be useful not only for JSON files. Files `csv` and `xlsx` as well may contain in a single line data that maps onto more than one table. Data in such files might be called denormalized – from the relational point of view.

## Loading Nested Tables into the Default Table

In order to load nested structures into default interface table `ida_lines` you should assign spec parameter `"insert_data"` a list of functions, one for each table: a parent one and child ones.

Let's load the above described file `test_nested_01.json` into table `ida_lines`:

```
"nested_01_ida": {
    "file": "test_nested_01.json",
    "insert_data": [
        lambda row: (row['region'], len(row['countries'])),
        lambda row: [
            (n['code'], n['name'], n['alpha2'], n['alpha3']) \
                for n in row['countries']
            ] if row['countries'] else []
    ]
}
```

The first function in the list produces a row for parent table, the second – a set of rows for "nested table" №1, the third (if it were defined) – a set of rows for "nested table" №2, etc.

Here are the first 10 rows inserted into table `ida_lines` with spec `nested_01_ida`:

```
|iload|iline|ntable|nline|c1        |c2               |c3 |c4 |
|-----|-----|------|-----|----------|-----------------|---|---|
|41   |1    |-1    |-1   |Nowhere   |0                |   |   |
|41   |2    |-1    |-1   |Antarctica|2                |   |   |
|41   |2    |1     |1    |010       |Antarctica       |AQ |ATA|
|41   |2    |1     |2    |074       |Bouvet Island    |BV |BVT|
|41   |3    |-1    |-1   |Africa    |59               |   |   |
|41   |3    |1     |1    |174       |Comoros          |KM |COM|
|41   |3    |1     |2    |262       |Djibouti         |DJ |DJI|
|41   |3    |1     |3    |226       |Equatorial Guinea|GQ |GNQ|
|41   |3    |1     |4    |232       |Eritrea          |ER |ERI|
|41   |3    |1     |5    |324       |Guinea           |GN |GIN|
```

Notice that
* column `iline` contains line number from the input file,
* column `ntable` contains number of unpacked nested structure ("nested table"), or `-1` for the parent table,
* column `nline` contains element number of unpacked structure (row number of "nested table"), or `-1` for the parent table.

## Loading Special Text Files

Sometimes you need to load in a database data that is represented in text files of a special format, for example,
* a file, where a few lines at the beginning describe data that follows, or
* a file, where lines have fields of fixed length without any delimiters.

Spec parameter `"pass_lines": True` tells `dput` to pass lines from input text file "as is" to function specified in spec parameter `"insert_data"`. Lines are passed as Python strings without any attempted splitting into fields.

Then, the `"insert_data"` function parses the string and returns a list or a tuple of fields' values to load into a database table.

Test data file `test_special.dat` contains data on world countries in lines of the following format:
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

Spec `"special_03_ida"` allows loading into table `ida_lines` four separate fields extracted from input lines with function `special_03_data` (it as well might be a lambda-function):

```
...

def special_03_ida(line):
    """
    line    - line content, e.g. AFAFG004Afghanistan
    """
    return (line[0:2], line[2:5], line[5:8], line[8:].strip())


specs = {
	...
    "special_03_ida": {
        "file": "test_special.dat",
        "pass_lines": True,
        "insert_data": special_03_ida
    },
	...
}
```

## Three Types of `insert_data` Functions

Spec parameter `"insert_data"` may set functions of three kinds:

| Function kind               | Description                                                                                                                                        |
| --------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| `<func>(row)`               | `row` - list or tuple of fields' values, or line from input file as is if `"pass_lines": True`                                                     |
| `<func>(line_no, row)`      | `line_no` - number of line from a file, `row` - list or tuple of fields' values, or line from input file as is if `"pass_lines": True`             |
| `<func>(iload, iline, row)` | `iload` - load ID, `iline` - number of loaded line, `row` - list or tuple of fields' values, or line from input file as is if `"pass_lines": True` |

When loading data from a single file, the number of file line `line_no` and the number of loaded line `iline` are the same.

However, when loading data from a series of files, the number of file line `line_no` resets with each new file, while the number of loaded line `iline` keeps incrementing through all lines of all files of a series.

Functions `<func>(line_no, row)` allow processing text files where first few lines contain metadata describing data that follows. See spec `"special_01_ida"` in test config files.

Functions `<func>(iload, iline, row)` allow loading data into multiple logically linked tables (i.e. a parent and child ones) by generating unique values for a parent table primary key and foreign key columns of child tables. Unique values are generated, combining `iload` and `iline` values. See spec `"nested_01_keygen"` in test config files.

## Command Line Arguments

```
$ ./dput.py -h
usage: dput.py [-h] [-a ARG] [-d] [-f] [-t] [-u USER] [-v] cfg_file spec [in_file]

Load data from file into DB, as specified in cfg-file spec.

positional arguments:
  cfg_file              cfg-file name
  spec                  spec name
  in_file               input file name

options:
  -h, --help            show this help message and exit
  -a ARG, --arg ARG     pass one or more arguments to SQL query
  -d, --delete          delete loaded data file(s)
  -f, --force           load data file(s) unconditionally
  -t, --trace           enable tracing
  -u USER, --user USER  set data loader username
  -v, --version         show program's version number and exit

Thanks for using dput.py!
```

The mandatory arguments are config file name `cfg_file` and spec name `spec`.

To execute all specs from the config file use keyword `all` instead of spec name.

If `in_file` is provided then the data will be loaded from the specified file instead of the one defined with spec parameter `"file"`. The input data format is determined by file name extension – the same as with spec parameter `"file"`.

Option `-a` or `--arg` allows loading 1 to 9 arguments in the row of table `ida` which keeps track of all loads done with `dput`. The loaded arguments are available to the SQL statements defined in spec parameters `"validate_actions"` and `"process_actions"`. To make it possible to load arguments in table `ida` you have to define a list of default values for the arguments with spec parameter `"args"`.

Option `-d` or `--delete` instructs the `dput` utility to delete input file(s) after executing the spec. An input file will not be deleted if errors occur while executing the spec.

Option `-f` or `--force` instructs the `dput` utility to load data from files even in case when data from these files had been already loaded. The `dput` utility registers paths and modification times of loaded files in a special file `~/.<cfg-file>.json` and by default only loads file(s) that had not been loaded earlier.

Option `-u` or `--user` allows setting username that will be loaded in the row of table `ida`.

Option `-t` or `--trace` instructs the `dput` to create a trace file in directory `~/.dbang`. This is an empty file named `dput#<spec>#<user>#<timestamp>#<status>`, where `<status>` is either 0 - running, or 1 - succeeded, or 2 - failed.

## Config File Parameters

Config file parameters are variables with names in uppercase that define context for executing specs from that config file. See also [Config Files Structure](conf.md).

The `dput` config file parameters are described below.

| Parameter           | Default Value                            | Description                                          |
| ------------------- | ---------------------------------------- | ---------------------------------------------------- |
| `DEBUGGING`         | `False`                                  | Debugging mode?                                      |
| `LOGGING`           | = DEBUGGING                              | Write to log file?                                   |
| `LOG_DIR`           | `./`                                     | Path to the directory with log files.                |
| `IN_DIR`            | `./`                                     | Path to the directory with input files to load.      |
| `ENCODING`*         | `locale.getpreferredencoding()`          | Input file(s) encoding.                              |
| `CSV_DIALECT`*      | `excel`                                  | CSV dialect as defined in Python module `csv`.       |
| `CSV_DELIMITER`*    | `csv.get_dialect(CSV_DIALECT).delimiter` | CSV fields delimiter.                                |
| `PRESERVE_N_LOADS`  | `10`                                     | Number of loads per spec to preserve in table `ida`. |
| `PRESERVE_N_TRACES` | `10`                                     | Number of trace files per spec to preserve.          |
| `SOURCE`*           |                                          | Name of a data source defined in `sources.py`.       |
\* config file parameter marked with asterisk may be overridden at spec level with a corresponding spec parameter.

## Spec Parameters

Specs are found in a config file in the `specs` dictionary and contain **spec parameters**. See also [Config Files Structure](conf.md).

Spec parameters for `dput` utility are described below. If not explicitly described as mandatory, a spec parameter is optional and may be omitted.

| Spec Parameter       | Description                                                                                                                                                                                                    |
| -------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `"tags"`             | List of tags attached to the spec.                                                                                                                                                                             |
| `"source"`           | Name of a data source defined in `sources.py`. This parameter overrides config file parameter `SOURCE`.                                                                                                        |
| `"doc"`              | Short description/comment on the spec.                                                                                                                                                                         |
| `"setup"`            | List of SQL statements to be executed at a spec startup.                                                                                                                                                       |
| `"upset"`            | List of SQL statements to be executed at a spec completion.                                                                                                                                                    |
| `"force"`            | Load data from files unconditionally.                                                                                                                                                                          |
| **`"file"`**         | **MANDATORY** name of the input file(s) to load. The file name extension determines the input data format. Use [glob-pattern](https://docs.python.org/3/library/glob.html) to set names for a series of files. |
| **`"args"`**         | List of default values for the arguments to be loaded into table `ida`.                                                                                                                                        |
| `"encoding"`         | Input file encoding. At spec level this parameter overrides config file parameter `ENCODING`.                                                                                                                  |
| `"csv_dialect"`      | CSV dialect as defined in Python module `csv`. At spec level this parameter overrides config file parameter `CSV_DIALECT`.                                                                                     |
| `"csv_delimiter"`    | CSV fields delimiter. At spec level this parameter overrides config file parameter `CSV_DELIMITER`.                                                                                                            |
| `"skip_lines"`       | Number of lines (`int`) to skip at the beginning of input files.                                                                                                                                               |
| **`"insert_data"`**  | List of Python functions to transform a line from input file (passed as a single`str` or as a `list` of fields) to a list of values for columns of a database table.                                           |
| `"pass_lines"`       | Pass lines from input files to Python functions specified in `"insert_data"` as plain strings (`str`)?                                                                                                         |
| `"insert_actions"`   | List of SQL statements or stored procedures calls that insert data into one or more database table(s).                                                                                                         |
| `"validate_actions"` | List of SQL statements or stored procedures calls that check data loaded into intermediate database table(s) for correctness.                                                                                  |
| `"process_actions"`  | List of SQL statements or stored procedures calls that moves or copies loaded data from intermediate table(s) to target table(s).                                                                               |
