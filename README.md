# dbang Command Line Utilities

Read this in other languages: [русский](README.ru.md).

dbang command line utilities include:

* `ddiff.py` - compares queries' results against two databases and reports discrepancies;
* `dtest.py` - executes test queries against databases and reports data faults found;
* `dget.py` - extracts data from databases into csv or html files;
* `dput.py` - loads data from CSV files into database tables;
* `hedwig.py` - sends emails built from files (e.g. files produced by ddiff or dget).

`ddiff.py` and `dtest.py` are the utilities to assess logical consistency and integrity of DB systems.

`dget.py` and `dput.py` are the scripts to get the data out and put the data in databases, as specified in config-files.

dbang utiliies typically
* use configuration files from `cfg` directory to get job to do,
* save their results in `out` directory (if not specified otherwise in a config-file).

You run a dbang utility with command line

```
<name>.py <cfg-file> [<spec> | all]
```

where `<cfg-file>` is a config-file name, and `<spec>` is a specification name from the config-file. If `<spec>` is omitted then all specs from the config-file are executed.

You might want to run the utilities with test config-files and see the results in the `out` directory:

```
ddiff.py ddiff-test
dtest.py dtest-test
dget.py dget-test
dput.py dput-test test_csv_sqlite test.csv
```

When running `dput.py`, in addition to the config-file name, you need to specify the specification name and the CSV file name. By default CSV files to load are looked for in the `in` directory (if not specified otherwise in a config-file).

Before running `hedwig.py` with its test config-file, make sure you have right values for `MAIL_SERVER` global variable and `to` dict items in `hedwig-test.py`. Atfer that execute

```
hedwig.py hedwig-test
```

and check your incomimg mail.
