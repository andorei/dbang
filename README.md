# dbang Command Line Utilities, v0.3

Read this in other languages: [русский](README.ru.md).

dbang command line utilities written in Python help to implement typical solutions related to databases:

* `ddiff.py` - [compares queries' results against two databases and reports discrepancies](doc/ddiff.md);
* `dtest.py` - [executes test queries against databases and reports data faults found](doc/dtest.md);
* `dget.py` - [extracts data from databases into csv, xlsx, json or html files](doc/dget.md);
* `dput.py` - [loads data from csv, xlsx or json files into database tables](doc/dput.md);
* `hedwig.py` - [sends emails built from files (e.g. files produced by ddiff or dget)](doc/hedwig.md).

The utilities work with Oracle, PostgreSQL, SQLite and MySQL databases using Python DB-API modules.

`ddiff.py` and `dtest.py` assess logical consistency and integrity of DB systems.

`dget.py` and `dput.py` get the data out and put the data in databases, as specified in config-files.

dbang utiliies
* process specs from config-files written in Python,
* write error, info and debug messages in log files, if logging or debugging mode is on,
* save their resulting files and logs in directories set with `OUT_DIR` and `LOG_DIR` variables in config-file, or in the current directory if the variables are not set.

You run a dbang utility with command line

```
<name>.py [options] <cfg-file> [<spec> | all]
```

where `<cfg-file>` is a config-file name, and `<spec>` is a specification name from the config-file. If `<spec>` is omitted then all specs from the config-file are executed.

To see available options run the utility with option `--help`.

Run the utilities with test config-files and see the results in the `out` directory and log files in the `log`:

```
ddiff.py ddiff-test-sqlite
dtest.py dtest-test-sqlite
dget.py dget-test-sqlite
dput.py dput-test-sqlite all
```

The above shown config-files use sqlite database defined in file `cfg/sources.py` as data source `"sqlite-source"`.

To run config-files for other databases edit connection parameters for data sources `"oracle-source"`, `"postgres-source"` or `"mysql-source"` in file `cfg/sources.py`. That done, utilities run with config-files will connect to the DB you specified.

When running `dput.py`, in addition to the config-file name, you need to specify the spec name and, optionally, the name of input file with extension `.csv`, `.xlsx` or `.json`. By default the filename is given in the spec and the file is looked for in the `in` directory, if not specified otherwise in a config-file.

Before running `hedwig.py` with its test config-file, make sure you have right values for `MAIL_SERVER` global variable and `to` dict items in `hedwig-test.py`. Atfer that execute

```
hedwig.py hedwig-test
```

and check your incoming mail.

To efficiently use dbang utilities you should learn how to create config-files with specifications of your own. You might use one of the test config-files as a template to start with. Save it with a new name and modify and adjust it to your needs.

You might run the utilities with specified config-files on schedule (using `crontab` on Linux or Task Scheduler on Windows) and email the generated reports and/or other files by means of `hedwig`.


## Data Sources

Data sources, or databases, used by the utilities are defined in dict `sources` in file `cfg/sources.py`.

Here is an example:

```
import os
import sys

sources = {
    "sqlite-source": {
        "database": "sqlite",
        "con_string": os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), f'.dbang.db')
    },
    "postgres-source": {
        "database": "postgres",
        "con_string": "postgresql://username:password@host/database"
        "setup": ["set timezone=\'Asia/Vladivostok\'"]
    },
    "oracle-source": {
        "database": "oracle",
        "con_string": "username/password@host:1521/ORA",
        "con_kwargs": {"encoding": "UTF-8"},
        "setup": ["ALTER SESSION SET TIME_ZONE = '+10:00'"]
    },
    "mysql-source": {
        "database": "mysql",
        "con_string": "",
        "con_kwargs": {'host': 'host', 'database': 'database', 'user': 'username', 'password': 'password'},
        "setup": ["create table if not exists test_table (id int, name varchar(50))"],
        "upset": ["drop table if exists test_table"]
    },
}
```

A data source is described with the following parameters:

* `"database"` - DBMS type, one of `"sqlite"`, `"postgres"`, `"oracle"`, `"mysql"`, used to choose the Python database API module;
* `"con_string"` - DB connection string, used as the first argument when calling `<module>.connect()`;
* `"con_kwargs"` - optional dict of named arguments, used when when calling `<module>.connect()`;
* `"setup"` - optional list of strings with SQL statements to execute once upon connecting to the DB;
* `"upset"` - optional list of strings with SQL statements to execute once before closing connectiio to the DB.


## Config-Files Structure

Config-files for dbang utilities, except `hedwig`, have the same structure:

```
import os
import sys

from sources import sources

#
# SETTINGS USED BY utility
#
OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'out')
DEBUGGING = True
LOGGING = True
LOG_DIR = os.path.join(os.path.dirname(__file__), '..', 'log')

#
# SETTINGS USED IN specs
#
# ...

specs = {
    "<spec_1>": {
        "source": "<source_1>",
        ...
    },
    "<spec_2>": {
        "source": "<source_2>",
        ...
    },
}

sources['source_1']['setup'] = sources['source_1'].get('setup', []) + [
    "<SQL statement>"
]

sources['source_2']['setup'] = sources['source_2'].get('setup', []) + [
    "<SQL statement>"
]
```

Config-files for `hedwig` do not import nor use data sources from `sources`. The rest is similar.

After `import` statements there goes a block of parameters used by utilities. All such parameters are defined in test config-files and while they might be useful they are not mandatory. If omited the utilities behave by default.

The block of utility parameters is followed by an optional block of user defined variables. If you have to repeatedly use the same expressions in specs then consider defining variables and using them instead.

The `specs` dict contains named specifications (which are dicts) and is the core of a config-file. Specs tell utilities what exactly to do. See test config-files for the commented specifications.

After `specs` dict there might be definitions of DB queries to be executed once upon establishing DB connection. If, for example, the utility or the config-file specs require a certain table in DB or specific session parameters then add necessary SQL statements to the `"setup"` list of the data source. To have SQL statements executed just before closing DB connection, add the statements to the `"upset"` list. See examples of `"setup"` and `"upset"` SQL statements in test config-files.


## How the utilities work

* `ddiff.py` - [compares queries' results against two databases and reports discrepancies](doc/ddiff.md);
* `dtest.py` - [executes test queries against databases and reports data faults found](doc/dtest.md);
* `dget.py` - [extracts data from databases into csv, xlsx, json or html files](doc/dget.md);
* `dput.py` - [loads data from csv, xlsx or json files into database tables](doc/dput.md);
* `hedwig.py` - [sends emails built from files (e.g. files produced by ddiff or dget)](doc/hedwig.md).
