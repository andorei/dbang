# dbang

	version 0.3

Read this in other languages: [русский](README.ru.md).

**dbang** command line utilities

* assess logical consistency and integrity of DB systems:
    * [`ddiff.py`](doc/ddiff.md) - compares queries' results against two databases and reports discrepancies
    * [`dtest.py`](doc/dtest.md) - executes test queries against databases and reports data faults found
* get the data out and put the data in databases, as specified in config files
    * [`dget.py`](doc/dget.md) - extracts data from databases into CSV, XLSX, JSON or HTML files
    * [`dput.py`](doc/dput.md) - loads data from CSV, XLSX or JSON files into database tables
* compose and send emails as specified in config files
    * [`hedwig.py`](doc/hedwig.md) - sends emails built from files (e.g. files produced by `ddiff` or `dget`).

The utilities work with Oracle, PostgreSQL, SQLite and MySQL databases using Python DB-API modules.

## Installation

The **dbang** utilities are written in Python 3 and depend on a number of Python packages specified in file [`requirements.txt`](requirements.txt).

To install **dbang** utilities
1. Download [compressed archive file of the latest release](https://github.com/andorei/dbang/releases/latest).
2. Unpack it in the directory of your choice.
3. Install with `pip` required dependencies from file [`requirements.txt`](requirements.txt)
```
cd dbang-<version>
pip install -r requirements.txt
```

## Usage

You run a **dbang** utility with command line

```
python <utility>.py [options] <config-file> [<spec> | all]
```

where
* `<utility>` is one of `ddiff`, `dtest`, `dget`, `dput` or `hedwig`,
* `options` are command line options specific to a utility,
* `<config-file>` is a path to config file, and
* `<spec>` is a specification name from the config file. If `<spec>` is omitted then all specs from the config file are executed.

To see all available options run the utility with option `--help`.

Of course on Linux you can make the utilities executable and run them directly by name.

**dbang** utilities
* process specs from config files written in Python,
* write error, info and debug messages in log file, if logging or debugging mode is on,
* save their resulting files and logs in directories set with `OUT_DIR` and `LOG_DIR` variables in config file, or in the current directory if the variables are not set.

## Examples

Directory `conf` contains test config files written both to test and to demonstrate what the utilities can do. All test config files use data sources specified in config file `sources.py` which is missing right after installation.

You create the file `sources.py` yourself by coping the example file `sample-sources.py`. After which you can run the utilities with config files that use local sqlite3 database:

```
cd dbang-<version>
./ddiff.py conf/ddiff-test-sqlite
./dtest.py conf/dtest-test-sqlite
./dget.py conf/dget-test-sqlite
./dput.py conf/dput-test-sqlite all
```

In `out` directory you'll find
* data discrepancies report generated by `ddiff`,
* data quality report generated by `dtest`,
* files with data extracted from database by `dget`.

In `log` directory you'll find each utility's log file.

To run the utilities with config files for Oracle, PostgreSQL or MySQL databases, edit connection parameters for data sources `"oracle-source"`, `"postgres-source"` or `"mysql-source"` in file `sources.py`. That done, the utilities run with the appropriate test config files will connect to the DB you specified.

Before running `hedwig.py` with its test config file, make sure to set right values for variables `MAIL_SERVER` and `MAIL_TO` in `conf/hedwig-test.py`. After that execute

```
./hedwig.py conf/hedwig-test
```

and check your incoming email.

## Further Details

To efficiently use **dbang** utilities you should learn how to create config files with specifications of your own.

You might use one of the test config files as a template to start with. Save it with a new name and modify and adjust it to your needs.

You might run the utilities with specified config files on schedule (using `crontab` on Linux or Task Scheduler on Windows) and email the generated reports and/or other files by means of `hedwig`.

* [`sources.py`](doc/sources.md)
* [`<config-file>.py`](doc/conf.md)
* [`ddiff.py`](doc/ddiff.md)
* [`dtest.py`](doc/dtest.md)
* [`dget.py`](doc/dget.md)
* [`dput.py`](doc/dput.md)
* [`hedwig.py`](doc/hedwig.md)

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests (test config files) as appropriate.

## License

[MIT](LICENSE)
