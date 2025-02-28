# ddiff. Detecting and Reporting Data Discrepancies in Two Databases

	version 0.3

The `ddiff` utility executes queries from config file specs against two databases, compares the results and reports found discrepancies in HTML format.

* [How It Works](#how-it-works)
* [Detecting Discrepancies in Two Passes](#detecting-discrepancies-in-two-passes)
* [Command Line Arguments](#command-line-arguments)
* [Config File Parameters](#config-file-parameters)
* [Spec Parameters](#spec-parameters)

## How It Works

To check if data in two databases are the same you should extract datasets from the both, join them by primary key and compare line by line. But what if database tables contain millions of rows?

There is a trick to drastically reduce the number of rows to extract and compare. That trick is aggregation.

Instead of retrieving millions of rows from both databases, you could select much fewer rows of aggregate values grouped by appropriate columns. Compare the two datasets of aggregate rows, and if you find discrepancies, then just go deeper and find the rows in both databases that cause the discrepancies at aggregate level.

Here is an example to illustrate this approach:

```
-- Instead of retrieveing over 20 millions of sale facts...

-- from database #1 (Oracle)
select sale_date, pos_code, item_code, qty, amount
from sales
;

-- and from database #2 (PostgreSQL)
select tdate, pos_id, item_id, quantity, total
from t_sales
;

-- let's select rows of aggregate values groupped by month and point of sales...

-- from database #1 (Oracle)
select trunc(sale_date, 'mm') month,
    pos_code,
    count(*) count_,
    sum(item_code) sum_item,
    sum(qty) sum_qty,
    sum(amount) sum_amount
from sales
group by trunc(sale_date, 'mm'), pos_code
;

-- and from database #2 (PostgreSQL)
select date_trunc('month', t_date) month,
    pos_id pos_code,
    count(*) count_,
    sum(item_id) sum_item,
    sum(quantity) sum_qty,
    sum(total) sum_amount
from t_sales
group by date_trunc('month', t_date), pos_id
;
```

Here, rows of database tables are grouped by the first date of month and POS code. The combination `(month, pos_code)` is a unique identifier (or primary key) of aggregate rows in each result set.

Having both datasets, we can find rows from dataset #1 missing in dataset #2, and rows from dataset #2 missing in dataset #1. Suppose they are:

```
-- rows from dataset #1 missing in dataset #2
month      pos_code count_ sum_item sum_qty sum_amount
---------- -------- ------ -------- ------- ----------
2023-03-01       52  13140 10230677    4089    5235670

-- rows from dataset #2 missing in dataset #1 
month      pos_code count_ sum_item sum_qty sum_amount
---------- -------- ------ -------- ------- ----------
2023-03-01       52  13140 10230677    4088    5235635
```

As you can see, the aggregate rows with sales for March 2023 at POS 52 differ by columns `sum_qty` and `sum_amount`. There are no discrepancies in sales data for other months and POS.

To find the rows in both databases that cause this difference, we should select rows where the first date of month and POS code equals the `(month, pos_code)` from the aggregate rows that differ. We will select 13140 rows from each database (see column `count_`) and compare them.

```
-- from database #1 (Oracle)
select sale_date,
    pos_code,
    item_code,
    qty,
    amount
from sales
where (trunc(sale_date, 'mm'), pos_code) in (
        (date '2023-03-01', 52)
    )
;

-- then from database #2 (PostgreSQL)
select t_date sale_date,
    pos_id pos_code,
    item_id item_code,
    quantity qty,
    total amount
from t_sales
where (date_trunc('month', t_date), pos_id) in (
        (date '2023-03-01', 52)
    )
;
```

The primary keys of these new result sets are the combination `(sale_date, pos_code, item_code)`. 

And again, having two datasets we can find rows from dataset #1 missing in dataset #2, and rows from dataset #2 missing in dataset #1. They are:

```
-- row from database #1 missing in dataset #2
sale_date  pos_code item_code qty amount
---------- -------- --------- --- ------
2023-03-25       52     66156   2     70

-- row from database #2 missing in dataset #1
sale_date  pos_code item_code qty amount
---------- -------- --------- --- ------
2023-03-25       52     66156   1     35
```

Here we are. According to database #1 there are 2 sold items 66156 on March 25, 2023, at POS 52, while database #2 says there is only 1 item sold.

We join the result sets by their primary key `(sale_date, pos_code, item_code)` to represent the differences column by column for the report:

```
sale_date  pos_code item_code qty#1 qty#2 amount#1 amount#2
---------- -------- --------- ----- ----- -------- --------
2023-03-25       52     66156     2     1       70       35
```

Here is an example of `ddiff` config file with spec `"sales"` that uses the above queries (a bit modified):

```
import os
import sys

from sources import sources


# MANDATORY constants used by ddiff.py
OUT_DIR = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), 'out')

# Optional constants used in specs below
# ...

specs = {
    "sales": {
        "sources": ["prod", "whs"],
        "queries": [
            """
            select trunc(sale_date, 'mm') month,
                pos_code,
                count(*) count_,
                sum(item_code) sum_item,
                sum(qty) sum_qty,
                sum(amount) sum_amount
            from sales
            group by trunc(sale_date, 'mm'), pos_code
            """,
            """
            select date_trunc('month', t_date) month,
                pos_id pos_code,
                count(*) count_,
                sum(item_id) sum_item,
                sum(quantity) sum_qty,
                sum(total) sum_amount
            from t_sales
            group by date_trunc('month', t_date), pos_id
            """
        ],
        "pk": ["month", "pos_code"],
        #
        # level 2
        #
        "sales": {
            "queries": [
                """
                select sale_date,
                    pos_code,
                    item_code,
                    qty,
                    amount
                from sales
                where (trunc(sale_date, 'mm'), pos_code) in (
                    {% for row in argrows %}(date '{{row[0]}}', {{row[1]}}){{"," if not loop.last}}{% endfor %}
                    )
                """,
                """
                select t_date sale_date,
                    pos_id pos_code,
                    item_id item_code,
                    quantity qty,
                    total amount
                from t_sales
                where (date_trunc('month', t_date), pos_id) in (
                    {% for row in argrows %}(date '{{row[0]}}', {{row[1]}}){{"," if not loop.last}}{% endfor %}
                    )
                """
            ],
            "pk": ["sale_date", "pos_code", "item_code"]
        }
    }
}
```

Queries in a `ddiff` spec are actually jinja2-templates. Before executing level 2 queries, the templates are rendered to build the list of (date, POS code) for `in` operator in `where` clause. Variable `argrows` contains the rows with discrepancies detected at the upper level.

You can specify as many levels of aggregation in a spec as you find appropriate. The more levels you define, the less rows are retrieved from databases at each level.

Global variable `OUT_DIR` in a `ddiff` config file sets the directory for report files.

Test config files `ddiff-test-<source>.py` contains comments on all the spec parameters. Read it carefully and familiarize yourself with all the parameters.

## Detecting Discrepancies in Two Passes

It is often hard or impossible to find a time when data in DB is not changing. It takes some time – minutes to hours – for changes to propagate to all target systems. In this case, when comparing data from the two DBs, you always find discrepancies because recent data changes are on their way from a source DB to a target DB.

In order to exclude discrepancies due to on-way changes from the discrepancies report, `ddiff` implements the following experimental approach:

1. Run config file spec that is sensible to on-way changes two times with an interval greater than time needed to propagate data between the two DBs, and
2. include in the report only discrepancies that were found by both the first run and the second run and remained unchanged between the two runs.

Discrepancies found by the first run and not found by the second were caused by data changes on the way at the time of the first run. Discrepancies found by the second run and not by the first are those caused by data changes on the way at the time of the second run. And only discrepancies found by both runs are considered as persistent and go to the discrepancies report.

This approach is supported by the `ddiff` command line options:

```
-1, --one      find discrepancies and store them
-2, --two      find discrepancies and intersect them with the stored
```

To see how it works, let's look at the spec `"current"` from the config file `ddiff-test-sqlite.py`:

```
spec = {
    "current": {
        "sources": ["ONE", "TWO"],
        "pk": ["c1"],
        "queries": [
            """
            select 1 c1, current_timestamp c2, 3 c3 from dual
            union all
            select 2 c1, current_timestamp c2, 5 c3 from dual
            union all
            select 3 c1, current_timestamp c2, 7 c3 from dual
            union all
            select 5 c1, current_timestamp c2, 1 c3 from dual
            """,
            """
            select 1 c1, datetime(current_timestamp, '+5 second') c2, 3 c3 from dual
            union all
            select 2 c1, current_timestamp c2, 6 c3 from dual
            union all
            select 4 c1, current_timestamp c2, 9 c3 from dual
            union all
            select 5 c1, current_timestamp c2, 1 c3 from dual
            """
       ]
    },
    ...
}
```

If you execute the spec as usual, you'll get the following discrepancies in the report:

```
c1 DB1 c2              DB2 c2              DB1 c3 DB2 c3
-- ------------------- ------------------- ------ ------
 1 2023-08-29 04:20:18 2023-08-29 04:20:23      3      3
 2 2023-08-29 04:20:18 2023-08-29 04:20:18      5      6
 3 2023-08-29 04:20:18 [NULL]                   7 [NULL]
 4 [NULL]              2023-08-29 04:20:18 [NULL]      9
```

Notice that the discrepancy in row `c1 = 1` is due to the fact that column `c2` from the query against DB `ONE` contains current time, while column `c2` from DB `TWO` query contains current time plus 5 seconds. Each time we execute these queries, we get new values in column `c2` – as the time goes. And `c2` values in rows `c1 = 1` returned by the two queries differ by 5 seconds. Thus, the data changes currently on way between DBs are simulated.

Let's execute the spec so that to exclude current data changes from the discrepancies report. First run:

```
ddiff.py -1 ddiff-test-sqlite current
```

And second run:

```
ddiff.py -2 ddiff-test-sqlite current
```

The second run reported the following discrepancies:

```
c1 DB1 c2              DB2 c2              DB1 c3 DB2 c3
-- ------------------- ------------------- ------ ------
 2 2023-08-29 04:22:36 2023-08-29 04:22:36      5      6
 3 2023-08-29 04:22:36 [NULL]                   7 [NULL]
 4 [NULL]              2023-08-29 04:22:36 [NULL]      9
```

The row `с1 = 1` was excluded from the report because discrepancies found in this row by the first run and by the second are not the same. Hence, they are considered as the ones caused by the on-way changes currently being propagated between the DBs. Whereas rows where `c1` equals 2, 3 and 4 showed the same discrepancies in both runs, and row `c1 = 5` showed no discrepancies.

## Command Line Arguments

```
$ ./ddiff.py -h
usage: ddiff.py [-h] [-v] [-1] [-2] cfg_file [spec]

Detect discrepancies in two databases as specified in cfg-file specs.

positional arguments:
  cfg_file       cfg-file name
  spec           spec name, defaults to "all"

options:
  -h, --help     show this help message and exit
  -v, --version  show program's version number and exit
  -1, --one      find discrepancies and store them
  -2, --two      find discrepancies and intersect them with the stored

Thanks for using ddiff.py!
```

The only mandatory argument is config file name `cfg_file`.

If `spec` is provided, then the utility executes only the named spec or specs with the given tag. If `spec` is omitted, then all specs from the config file are executed,

Options `--one` and `--two` are covered in [Detecting Discrepancies in Two Passes](#detecting-discrepancies-in-two-passes).

## Config File Parameters

Config file parameters are variables with names in uppercase that define context for executing specs from that config file. See also [Config Files Structure](conf.md).

The `ddiff` config file parameters are described below.

| Parameter         | Default Value           | Description                                                          |
| ----------------- | ----------------------- | -------------------------------------------------------------------- |
| `DEBUGGING`       | `False`                 | Debugging mode?                                                      |
| `LOGGING`         | = DEBUGGING             | Write to log file?                                                   |
| `LOG_DIR`         | `./`                    | Path to the directory with log files.                                |
| `OUT_DIR`         | `./`                    | Path to the directory with discrepancy reports files.                |
| `DATETIME_FORMAT` | `"%Y-%m-%d %H:%M:%S%z"` | Datetime format; defaults to ISO 86101.                              |
| `DATE_FORMAT`     | `"%Y-%m-%d"`            | Date format; defaults to ISO 86101.                                  |
| `SOURCES`*        |                         | Optional list of two data source names defined in file `sources.py`. |
\* config file parameter marked with asterisk may be overridden at spec level with a corresponding spec parameter.

## Spec Parameters

 Specs are found in a config file in the `specs` dictionary and contain **spec parameters**. See also [Config Files Structure](conf.md).

Spec parameters for `ddiff` utility are described below. If not explicitly described as mandatory, a spec parameter is optional and may be omitted.

| Spec Parameter  | Description                                                                                                                                                                                                                                                                   |
| --------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `"tags"`        | List of tags attached to the spec.                                                                                                                                                                                                                                            |
| `"sources"`     | List of two data source names (DB1 and DB2) defined in file `sources.py`. This parameter overrides config file parameter `SOURCES`.                                                                                                                                           |
| `"doc"`         | Short description/comment on a spec that is shown in a discrepancies report.                                                                                                                                                                                                  |
| `"setups"`      | List of SQL statements for DB1 and DB2 to be executed at a spec startup.                                                                                                                                                                                                      |
| `"upsets"`      | List of SQL statements for DB1 and DB2 to be executed at a spec completion.                                                                                                                                                                                                   |
| **`"queries"`** | **MANDATORY** list of two queries for DB1 and DB2, respectively. The two queries should return columns with the same names and data types so that the utility could find the difference of the two datasets.                                                                  |
| **`"pk"`**      | **MANDATORY** list of column names that comprise the primary key of a queries' datasets.                                                                                                                                                                                      |
| `"op"`          | The difference modifier with one of the values: `>` (DB1 dataset minus DB2 dataset), `<` (DB2 dataset minus DB1 dataset) or `=` (symmetric difference, the default).                                                                                                          |
| `"<spec>"`      | A nested dictionary with mandatory keys `queries` and `pk` that define the level 2 queries and primary key. It may also contain a next level nested dictionary `<spec>`. Spec parameters other than `queries` and `pk` are propagated from the top level to the lower levels. |
