# dtest. Testing and Reporting Data Quality

	version 0.3

The `dtest` utility executes queries from config file specs against a relational database, and generates a report on data quality in HTML format.

* [How It Works](#как-это-работает)
* [Command Line Arguments](#command-line-arguments)
* [Config File Parameters](#config-file-parameters)
* [Spec Parameters](#spec-parameters)

## How It Works

When I need to make sure there are no data in a database that violate a given rule, I write a query to select data violating that rule. For example,

```
-- Make sure there are no semicolons in item names.

select * 
from items 
where name like '%;%'
;
no rows

-- Make sure the position count in a header equals to a count of positions.

select *
from header h
where pos_count != (
    select count(*) from positions p where p.header_id = h.header_id
    )
;
no rows
```

If the query returns no rows, it is a good result.

If the query returns one or more rows of data, then the rule is violated, and I need to correct the data.

Here is an example of `dtest` specs with the above queries (a bit modified):

```
import os
import sys

from sources import sources


OUT_DIR = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), 'out')

specs = {
    "Names without semicolons": {
        "source": "prod",
        "query": """"
            select item_id, name
            from items 
            where name like '%;%'
            """"
    },
    "Position count in a header": {
        "source": "prod",
        "query": """"
            with q as (
                select header_id, count(*) cnt
                from positions p
                group by header_id
            )
            select h.header_id, h.pos_count, q.cnt
            from header h 
                left join q on q.header_id = h.header_id
            where h.pos_count != coalesce(q.cnt, -1)
            """"
    }
}
```

Global variable `OUT_DIR` sets the directory for report files.

Test config file `dtest-test.py` contains comments on all the spec parameters. Read it carefully and familiarize yourself with all the parameters.

## Command Line Arguments

```
$ ./dtest.py -h
usage: dtest.py [-h] [-v] cfg_file [spec]

Run queries from cfg-file spec(s) against a DB, and generate data quality report.

positional arguments:
  cfg_file       cfg-file name
  spec           spec name, defaults to "all"

options:
  -h, --help     show this help message and exit
  -v, --version  show program's version number and exit

Thanks for using dtest.py!
```

The only mandatory argument is config file name `cfg_file`.

If `spec` is provided, then the utility executes only the named spec or specs with the given tag. If `spec` is omitted, then all specs from the config file are executed.

## Config File Parameters

Config file parameters are variables with names in uppercase that define context for executing specs from that config file. See also [Config Files Structure](conf.md).

The `dtest` config file parameters are described below.

| Parameter         | Default Value           | Description                                      |
| ----------------- | ----------------------- | ------------------------------------------------ |
| `DEBUGGING`       | `False`                 | Debugging mode?                                  |
| `LOGGING`         | = DEBUGGING             | Write to log file?                               |
| `LOG_DIR`         | `./`                    | Path to the directory with log files.            |
| `OUT_DIR`         | `./`                    | Path to the directory with data quality reports. |
| `DATETIME_FORMAT` | `"%Y-%m-%d %H:%M:%S%z"` | Datetime format; defaults to ISO 86101.          |
| `DATE_FORMAT`     | `"%Y-%m-%d"`            | Date format; defaults to ISO 86101.              |
| `SOURCE`*         |                         | Name of a data source defined in `sources.py`.   |
\* config file parameter marked with asterisk may be overridden at spec level with a corresponding spec parameter.

## Spec Parameters

Specs are found in a config file in the `specs` dictionary and contain **spec parameters**. See also [Config Files Structure](conf.md).

Spec parameters for `dtest` utility are described below. If not explicitly described as mandatory, a spec parameter is optional and may be omitted.

| Spec Parameter | Description                                                                                                                              |
| -------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| `"tags"`       | List of tags attached to the spec.                                                                                                       |
| `"source"`     | Name of a data source defined in `sources.py`. This parameter overrides config file parameter `SOURCE`.                                  |
| `"doc"`        | Short description/comment on a spec that is shown in a data quality report.                                                              |
| `"setup"`      | List of SQL statements to be executed at a spec startup.                                                                                 |
| `"upset"`      | List of SQL statements to be executed at a spec completion.                                                                              |
| **`"query"`**  | **MANDATORY** query to select rows that violate the rule being checked.                                                                  |
| `"header"`     | List of column names for the data returned by the `"query"`. If not set then column aliases from the `"query"` are used as column names. |
