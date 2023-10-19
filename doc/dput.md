# dput. Loading data from file into database

To load data from your files to your DB first run test spec from test config-file `dput-test-<source>.py` against your DB. Then `dput` will create tables `ida` and `ida_lines` in the DB, and these tables will be used to load data.


* [Loading data into the default tables](#loading-data-into-the-default-tables)
* [Loading data into user-defined table](#loading-data-into-user-defined-table)
* [Loading data from a JSON file](#loading-data-from-a-json-file)


## Loading data into the default tables

Loading data from a file into a DB typically implies

* verifying the data for compliance to the requirement,
* inserting the data into database tables for which the data is destined.

If the data from the file do not comply to the requirements then the data should not be loaded into the target tables, and the user should receive error messages.

`dput` utility

* loads data from `csv`, `xlsx` or `json` file into tables `ida` and `ida_lines` (unless other user-defined table is specified) in a DB as specified in config-file spec;
* executes SQL queries from the spec to verify that the data loaded into `ida_lines` (or other table) comply to the requirements;
* if the verification is OK, executes SQL queries from the spec to insert the data from `ida_lines` (or other table) into target tables;
* if the verification failed, writes error messages to the log file.

Tables `ida` and `ida_lines` are automatically created in DB when running a test config-file `dput-test-<source>.py`. Here is their structure:

```
create table if not exists ida (
    iload serial4 not null,
    idate timestamptz not null default now(),
    istat int2 not null default 0,
    imess varchar(4000),
    entity varchar(50) not null,
    ifile varchar(256) not null,
    iuser varchar(30),
    primary key (iload)
);

create table if not exists ida_lines (
    iload int not null,
    iline int not null,
    istat smallint not null default 0,
    ierrm varchar(4000),
    c1 varchar(4000),
    c2 varchar(4000),
    ...
    ...
    ...
    c100 varchar(4000),
    primary key (iload, iline),
    foreign key (iload) references ida(iload) on delete cascade
);
```

Table `ida` keeps the facts of loads, in particular:

* load identifier `iload`,
* load time `idate`,
* load status `istat`,
* name of a loaded file `ifile`,
* name of a spec `entity`.

Table `ida_lines` keeps all the lines from the file, and also

* load identifier `iload`,
* line number `iline`,
* line status `istat` and
* error message `ierrm` – in case when error occured.

Let's see how `dput` works – using test file `test.csv` and specs from the config-file `dput-test-postgres.py`.

File `test.csv` contains the list of countries with 4 fields

* country name,
* 2-symbol country code,
* 3-symbol country code,
* numeric country code.

Here are the first five and the last five lines from the file:

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

When loading the lines in table `ida_lines` the fields' values will be put in columns `c1`, `с2`, `с3` and `с4`, respectfully. (As table `ida_lines` has 100 columns `c1`, .. `c100` the number of fields in a file to load may not be greater than 100.)

The status of lines `istat` right after loading equals 0 - waiting to be processed.

Here is the test spec for loading countries into PostgreSQL database:

```
specs = {
    ...
    "csv_ida_test": {
        #
        # database to load data into from csv file
        #
        "source": "postgres-source",
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
        #"preserve_n_loads": 10,
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
    ...
}
```

List `"validate_statements"` contains SQL statement to verify data compliance to the requirements. These statements get executed by `dput` after the lines are loaded into table `ida_lines`.

The three `update` statements in the spec above check, respectfully:

* that all 4 fields are not empty,
* that the length of 2-symbol country code is 2,
* that the length of 3-symbol country code is 3.

If the data does not meet requirements the line in `ida_lines` gets marked as erroneous (`istat = 2`), and error message is put into the field `ierrm`. In this case the processing is stopped after executing `"validate_statements"`, and `dput` writes bad line numbers and error messages to the log file.

If `"validate_statements"` do not detect errors then `dput` executes SQL statements from the list `"process_statements"` and inserts the verified data from `ida_lines` into target tables. If when executing `"process_statements"` some lines in `ida_lines` get marked as erroneous the erros will be written to the log file.

In the test spec the list `"process_statements"` contains a single statement that deletes loaded data from tables `ida` and `ida_lines`. Thus, instead of inserting data into target tables, test data is just deleted from the DB.

SQL statements in lists `"validate_statements"` and `"process_statements"` contain a bind variable for a load identifier `iload`. While bind variables for PostgreSQL are designated with `%s`, bind variables for other DBs may be designated differently, depending on the Python database API module for the DB. See test config-files for other databases `dput-test-sqlite.py`, `dput-test-oracle.py`, `dput-test-mysql.py`.

If execution of `"validate_statements"` and `"process_statements"` didn't mark any rows in the table `ida_lines` as erroneous, then `dput` sets the load status in `ida.istat` to 1 - "Processing succeeded".

Data loaded in DB via the interface tables `ida` and `ida_lines` is not deleted from these tables right away. The config-file parameter

```
PRESERVE_N_LOADS = 10
```

tells `dput` to keep 10 last loads for each spec in the interface tables. When user runs the 11-th load the oldest of the previous 10 loads will be deleted. If you set `PRESERVE_N_LOADS` to 0, then `dput` will dete the data from interface tables right after executing `"process_statements"`.

Keeping loaded data in interface tables for a while may turn helpful when you need to manually check what data was loaded by users or what errors were detected.

Test config-files `dput-test-<source>.py` contain comments on all the spec parameters. Read it carefully and familiarize yourself with all the parameters.
 

## Loading data into user-defined table

Instead of loading data rows into table `ida_lines` it is possible to load them into other table. For example, you might have in your DB an interface table where data, once loaded, is processed by stored procedure. To make `dput` load data into such a table you should set spec parameters `"insert_statement"` and `"insert_values"`.

Suppose you have interface table `test` designed to accept data on countries:

```
create table if not exists test (
    code varchar(3) not null,
    name varchar(50) not null,
    alpha2 char(2),
    alpha3 char(3)
)
```

The following spec allows to load data from file `test.csv` into table `test`:

```
specs = {
    "csv_test_test": {
        "source": "postgres-source",
        "file": "test.csv",
        #
        # statement to insert data into user defined table
        #
        insert_statement": """
            insert into test (
                code, name, alpha2, alpha3)
            values (
                %s, %s, %s, %s)
        """,
        #
        # tuple of values to insert with the insert statement
        #
        "insert_values": lambda row: (row[3], row[0], row[1], row[2])
    },
    ...
}
```

Spec parameter `"insert_statement"` defines SQL statement `insert` to insert a row into table `test`. As the order of columns in `insert` statement differs from the order of fields in the CSV-file (see above), the `"insert_values"` parameter defines Python lambda-function which rearranges the fields in the order required by the SQL statement: numeric code, country name, 2-symbol country code, 3-symbol country code.

If you specify columns in the `insert` statement in the order of fields in CSV-file then `"insert_values"` parameter may be omitted:

```
specs = {
    "csv_test_test": {
        "source": "postgres-source",
        "file": "test.csv",
        insert_statement": """
            insert into test (
                name, alpha2, alpha3, code)
            values (
                %s, %s, %s, %s)
        """
    },
    ...
}
```

In this case it is important that each of the 4 fields of a CSV file line has a corresponding column in the table `test`. Whereas the `"insert_values"` lambda-function allows to choose (and rearrange) for insertion any subset of the fields.

Even when loading data in a user-defined table specified in the `"insert_statement"`, the `dput` utility registers the load in the `ida` table with status 0 - waiting for being processed.

If SQL statements in the lists `"validate_statements"` and `"process_statements"` set the load status in the column `ida.istat` to 2 - error, and put an error message in the column `ida.imess`, then `"dput"` writes that error message in the log file. Otherwise the load status is set to 1 - processing succeeded, and success message is written in the log file.


## Loading data from a JSON file

The `"insert_values"` parameter is mandatory in a spec that loads data from a JSON file, even in case when rows are loaded into the default table `ida_lines`. The thing is that the fields of JSON objects – or JSON file "rows" – could be put in any order. Here are the first five and the last five lines from the file `test.json` (in the directory `in`):

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

An example specification to load data from `test.json` into table `ida_lines`:

```
specs = {
    "json_ida_test": {
        "source": "postgres-source",
        "file": "test.json",
        #
        # tuple of values to insert into ida_lines table
        #
        "insert_values": lambda row: (row["code"], row["name"], row.get("alpha2"), row.get("alpha3"))
    },
    ...
```
