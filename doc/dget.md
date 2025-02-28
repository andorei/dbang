# dget. Getting Data from Database into File

	version 0.3

The `dget` utility retrieves data from DB and writes it to CSV, XLSX, JSON or HTML file, according to the config file spec. Retrieved data may be written into a single file or a series of files, each with a specified number of rows. Optionally, the output files may individually be zipped.

* [Basic Usage](#basic-usage)
* [Query with Parameters](#query-with-parameters)
* [Dynamic Query](#dynamic-query)
* [User-Defined File Templates](#user-defined-file-templates)
* [Case #1](#case-1)
* [Case #2](#case-2)
* [Case #3](#case-3)
* [Command Line Arguments](#command-line-arguments)
* [Config File Parameters](#config-file-parameters)
* [Spec Parameters](#spec-parameters)

## Basic Usage

Here are example specs for SQLite where 1000 rows with two fields are retrieved from DB and are written to a file.

The `"file"` parameter sets the file name and its format:

```
# hello-dget.py

SOURCE = sources['sqlite-source']
QUERY = \
	"""
	with recursive numbers (n) as (
		select 0 as n from dual
		union all
		select n + 1
		from numbers
		where n < 999
	)
	select 'Hello world!' as hello,
	    42 as answer
	from numbers
	"""

specs = {
    "hello1": {
        "file": "hello_world.csv",
        "query": QUERY,
        "header": "select 'Привет', 'Ответ' from dual"
    },
    "hello2": {
        "file": "hello_world.xlsx",
        "query": QUERY
    },
    "hello3": {
        "file": "hello_world.json",
        "query": QUERY,
        "header": ["Hello", "Answer"]
    },
    "hello4": {
        "file": "hello_world.html.zip",
        "query": QUERY,
        "header": ["Hello", "Answer"]
    },
    "hello5": {
        "file": "hello_%(user)s_%(datetime)s_%(seqn)06i.csv",
        "rows_per_file": 100,
        "query": QUERY
    },
    ...
}

sources['sqlite-source']['setup'] = sources['sqlite-source'].get('setup', []) + [
    "create table if not exists dual as select 'X' as dummy"
]
```

The `"file"` parameter in spec `"hello4"` tells `dget` to put data into a HTML file and compress it into `zip`.

The `"file"` parameter in spec `"hello5"` sets [`printf`-style template](https://docs.python.org/3/library/stdtypes.html#printf-style-string-formatting) for generating name(s) of output file(s). The template may contain the following parenthesized names:
* `date` – current date in ISO format `'%Y-%m-%d`,
* `datetime` – current date and time in format `'%Y-%m-%d-%H-%M-%S'`:
* `seqn` – number of file in a series of output files,
* `user` – either username set in CLI with option `--user`, or the name of OS user executing `dget`.

The `"rows_per_file"` parameter sets the number of rows to write to a single file. Given that the query returns 1000 rows, the execution of spec `"hello5"` will create 10 files named according to template in parameter `"file"`.

Optional parameter `"header"` allows setting column titles:

* as a list of strings, like in spec `"hello4"`,
* or as a query against DB, which returns strings, like in spec `"hello1"`.

If parameter `"header"` is omitted then `dget` uses column aliases from the `"query"`, like in spec `"hello2"`.

Test config file `dget-test-<source>.py` contains comments on all the spec parameters. Read it carefully and familiarize yourself with all the parameters.

## Query with Parameters

This spec shows a query with parameters:

```
# hello-dget.py

SOURCE = sources['sqlite-source']

specs = {
	"hello9": {
        "file": "hello_param.csv",
        "query": """
            with recursive numbers (n) as (
		        select 0 as n from dual
		        union all
		        select n + 1
		        from numbers
		        where n < 999
	        )
            select 'Hello '||:name||'!' as hello,
	            :num as answer
	        from numbers
	    """,
        "bind_args": {"name": "world", "num": 42.0}
    }
}
```

Spec parameter `"bind_args"` is a dictionary where keys are names of bind variables used in the `"query"` and values are default values for the bind variables. The data types of default values implicitly define data types of bind variables.

To pass non-default values to the query bind variables, use CLI option `-a`, or `--arg`:

```
dget.py -a Andrei -a 101 hello-dget hello9
```

In the above example named bind variables in SQL query for SQLite are designated with colon before a name. For other databases bind variables may be designated otherwise  – it depends on Python DB-API module for a database. To see examples for databases other than SQLite go to test config files `dget-test-sqlite.py`, `dget-test-oracle.py`, `dget-test-mysql.py`.

## Dynamic Query

`dget` allows to first dynamically generate a query and then execute it to retrieve data that will go to a file.

If `select` statement defined in the `"query"` spec parameter returns the only string value with alias `query`, then `dget` uses this string value as a query to execute.

For example, the query against PostgreSQL DB in the next spec produces a query to get the number of rows in all the tables in current schema which names end with `_h`:

```
specs = {
    "rowcount": {
         "source": "postgres-source",
         "file": "rowcount.html",
         "query": """
                select
                    string_agg(
                        'select '''||tablename||''' tablename, count(*) row_count from '||tablename,
                        chr(10)||'union all'||chr(10)
                        order by tablename
                    ) query
                from pg_tables
                where schemaname = current_schema
                    and tablename like '%_h'
                """
        }
```

`dget` will execute the query returned by the `"query"` from the spec and will write the result set into the file:

```
select 'bc_h' tablename, count(*) row_count from bc_h
union all
select 'cc_h' tablename, count(*) row_count from cc_h
union all
select 'cn_h' tablename, count(*) row_count from cn_h
union all
select 'emp_h' tablename, count(*) row_count from emp_h
;

tablename row_count
--------- ---------
bc_h         329387
cc_h           2400
cn_h            137
emp_h          1202
```

Any metadata that you keep in your DB, including system catalog, may be used to dynamically build queries. So make use of the described feature to leverage your metadata.

## User-Defined File Templates

JSON and HTML files are built by default using jinja2 templates `dget.json.jinja` and `dget.html.jinja`, respectively, located in `conf` directory. You may create your own jinja2 templates, using the same variables as in the default templates. To use your own template in a config file specification set its name in the spec parameter `"template"`.

## Case #1

You must have heard about self-service business intelligence (SSBI). What might it look like in a simple case?

Day after day company's IT department gets requests to download from DB into `xlsx` file

* all articles of category Shoes and of season Spring-Summer 23,
* all articles with special transportation conditions,
* new articles introduced during the last month,
* new articles managed by manager Smith,
* etc.

These and other similar requests can be satisfied with a single download of articles with all the required attributes: category, season, transportation conditions, date of sales start, manager name. You only need to periodically download the data into a file available to all the interested parties.

Now a person who needs the list of all articles belonging to Shoes category and Spring-Summer 23 season has to just open the file in Excel and filter the spreadsheet by columns Category and Season. Other employees should do the same way.

To download the article data periodically you should write a `dget` spec with appropriate SQL query and schedule execution of `dget.py` with that spec on a periodic basis (using `crontab` on Linux or Task Scheduler on Windows).

## Case #2

Put the result of SQL query into HTML file and send it to the addressees as a table in the body of email message.

The data in HTML-table might represent

* errors registered in a log table during last hour,
* periodic report (on users' activity, on status of business-processes, etc.),
* notification on a special event that requires user's attention.

If a HTML file to be sent is too big to insert its content into the message body you might instead attach it to the email message.

Composing email messages and sending them to interested parties is what `hedwig` utility does for you (according to specs in a config file).

## Case #3

You may use `dget` at the backend of a web application to get data from databases in a required format.

## Command Line Arguments

```
$ ./dget.py -h
usage: dget.py [-h] [-v] [-a ARG] [-u USER] [-t] cfg_file [spec] [out_file]

Retrieve data from DB into file, as specified in cfg-file specs.

positional arguments:
  cfg_file              cfg-file name
  spec                  spec name, defaults to "all"
  out_file              output file name

options:
  -h, --help            show this help message and exit
  -v, --version         show program's version number and exit
  -a ARG, --arg ARG     pass one or more arguments to SQL query
  -u USER, --user USER  set username
  -t, --trace           enable tracing

Thanks for using dget.py!
```

The only mandatory argument is config file name `cfg_file`.

If `spec` is provided then the utility executes only the named spec or specs with the given tag. If `spec` is omitted then all specs from the config file are executed.

If `out_file` is provided then the data is put into the specified file instead of the one defined with spec parameter `"file"`. The output file format is determined by its extension – the same as with spec parameter `"file"`.

Option `-a` or `--arg` allows passing one or more arguments to SQL query defined with spec parameter `"query"`. The allowed query parameters and their default values should be specified with spec parameter `"bind_args"`.

Option `-u` or `--user` allows setting username that may be used as a part of an output file name. 

Option `-t` or `--trace` instructs the `dget` to create a trace file in directory `~/.dbang`. This is an empty file named `dget#<spec>#<user>#<timestamp>#<status>`, where `<status>` is either 0 - running, or 1 - succeeded, or 2 - failed.

## Config File Parameters

Config file parameters are variables with names in uppercase that define context for executing specs from that config file. See also [Config Files Structure](conf.md).

The `dget` config file parameters are described below.

| Parameter           | Default Value                            | Description                                    |
| ------------------- | ---------------------------------------- | ---------------------------------------------- |
| `DEBUGGING`         | `False`                                  | Debugging mode?                                |
| `LOGGING`           | = DEBUGGING                              | Write to log file?                             |
| `LOG_DIR`           | `./`                                     | Path to the directory with log files.          |
| `OUT_DIR`           | `./`                                     | Path to the directory with output files.       |
| `ENCODING`*         | `locale.getpreferredencoding()`          | Output file(s) encoding.                       |
| `DATETIME_FORMAT`   | `"%Y-%m-%d %H:%M:%S%z"`                  | Datetime format; defaults to ISO 86101.        |
| `DATE_FORMAT`       | `"%Y-%m-%d"`                             | Date format; defaults to ISO 86101.            |
| `CSV_DIALECT`*      | `excel`                                  | CSV dialect as defined in Python module `csv`. |
| `CSV_DELIMITER`*    | `csv.get_dialect(CSV_DIALECT).delimiter` | CSV fields delimiter.                          |
| `PRESERVE_N_TRACES` | `10`                                     | Number of trace files per spec to preserve.    |
| `SOURCE`*           |                                          | Name of a data source defined in `sources.py`. |
\* config file parameter marked with asterisk may be overridden at spec level with a corresponding spec parameter.

## Spec Parameters

 Specs are found in a config file in the `specs` dictionary and contain **spec parameters**. See also [Config Files Structure](conf.md).

Spec parameters for `dget` utility are described below. If not explicitly described as mandatory, a spec parameter is optional and may be omitted.

| Spec Parameter         | Description                                                                                                                                                                                         |
| ---------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `"tags"`               | List of tags attached to the spec.                                                                                                                                                                  |
| `"source"`             | Name of a data source defined in `sources.py`. This parameter overrides config file parameter `SOURCE`.                                                                                             |
| `"doc"`                | Short description/comment on the spec.                                                                                                                                                              |
| `"setup"`              | List of SQL statements to be executed at a spec startup.                                                                                                                                            |
| `"upset"`              | List of SQL statements to be executed at a spec completion.                                                                                                                                         |
| **`"file"`**           | **MANDATORY** name of the output file(s). The file name extension determines the output format. Use [glob-pattern](https://docs.python.org/3/library/glob.html) to set names for a series of files. |
| `"rows_per_file"`      | Number of rows (`int`) written to a separate file – in order to put data into a series of files of small size,                                                                                      |
| **`"query"`**          | **MANDATORY** query that returns either a dataset to be written to output file(s) or a single row with single column named `query` that contains dynamically built query to be executed.            |
| **`"bind_args"`**      | Python dictionary with names and default values for bind variables found in the`"query"`.                                                                                                           |
| `"header"`             | Either a list of field names or a `select` query that retrun a single row with field names. If not set then column aliases from the `"query"` are used as field names.                              |
| `"csv.encoding"`       | CSV file encodong. At spec level this parameter overrides config file parameter `ENCODING`.                                                                                                         |
| `"csv.dialect"`        | CSV dialect as defined in Python module `csv`. At spec level this parameter overrides config file parameter `CSV_DIALECT`.                                                                          |
| `"csv.delimiter"`      | CSV fields delimiter. At spec level this parameter overrides config file parameter `CSV_DELIMITER`.                                                                                                 |
| `"csv.dec_separator"`  | Decimal separator for numbers in CSV file. The default is `.` (dot).                                                                                                                                |
| `"json.encoding"`      | JSON file encodong. At spec level this parameter overrides config file parameter `ENCODING`.                                                                                                        |
| `"json.template"`      | Name of jinja2 template file used to build JSON output file. The default is `dget.json.jinja`.                                                                                                      |
| `"html.encoding"`      | HTML file encodong. At spec level this parameter overrides config file parameter `ENCODING`.                                                                                                        |
| `"html.template"`      | Name of jinja2 template file used to build HTML output file. The default is `dget.html.jinja`.                                                                                                      |
| `"html.title"`         | Title for HTML file. The default is spec name.                                                                                                                                                      |
| `"html.dec_separator"` | Decimal separator for numbers in HTML file. The default is `.` (dot).                                                                                                                               |
