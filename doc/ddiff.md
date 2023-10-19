# ddiff. Detecting and reporting data discrepancies in two databases

`ddiff` executes queries from config-file specs against two databases, compares the results and reports found discrepancies in html format.


* [How it works](#how-it-works)
* [Excluding current data changes from the discrepancies report](#excluding-current-data-changes-from-the-discrepancies-report)


## How it works

To check if the data in two databases are the same you should extract the data from the both and compare datasets line by line. But what if database tables contain millions of rows?

There is a trick to drastically reduce the number of rows to extract and compare. That trick is aggregation.

Instead of selecting millions of rows from both databases you could select much less rows of aggregate values groupped by appropriate columns. Compare the two datasets of aggregate rows, and if you find discrepancies then just drill down to find the rows in both databases that cause the discrepancies at aggregate level.

Here is an example to illustrate this approach:

```
-- Instead of selecting over twenty millions of sale facts...

-- from database #1 (Oracle)
select sale_date, pos_code, item_code, qty, amount from sales
;

-- and from database #2 (PostgreSQL)
select tdate, pos_id, item_id, quantity, total from t_sales
;

-- select rows of aggregate values groupped by month and point of sales...

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

Here rows of database tables are groupped by the first date of month and POS code. The combination `(month, pos_code)` is a unique identifier (or primary key) of aggregate rows in each result set.

Having both datasets we can find rows from dataset #1 missing in dataset #2, and rows from dataset #2 missing in dataset #1:

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

We see that the aggregate rows with sales for March 2023 at POS 52 differ by columns `sum_qty` and `sum_amount`. There are no discrepancies in sales data for other months and POS.

To find the rows in both databases that cause this difference we should select rows where the first date of month and POS code equals the `(month, pos_code)` from the aggregate rows that differ. We will select 13140 rows from each database (see column `count_`) and compare them.

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

And again, having two datasets we can find rows from dataset #1 missing in dataset #2, and rows from dataset #2 missing in dataset #1:

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

Here is an example of `ddiff` config-file with spec `"sales"` that uses the above queries (a bit modified):

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

Queries in a `ddiff` spec are actually jinja2-templates. Before executing level 2 queries the templates are rendrered to build the list of (date, POS code) for `in` operator in `where` clause. Variable `argrows` contains the rows with discrepancies detected at the upper level.

You can specify as many levels of aggregation in a spec as you find appropriate. The more levels you define the less rows are retrieved from databases at each level.

Global variable `OUT_DIR` in a `ddiff` config-file sets the directory for report files.

Test config-files `ddiff-test-<source>.py` contains comments on all the spec parameters. Read it carefully and familiarize yourself with all the parameters.


## Excluding current data changes from the discrepancies report

It is often hard or impossible to find a time when data in DB is not changing. It takes some time – minutes to hours – for changes to propagate to all target systems. In this case, when comparing data from the two DBs, you always find discrepancies because recent data changes are on their way from a source DB to a target DB.

In order to exclude discrepancies due to on-way changes from the discrepancies report `ddiff` implements the following experimental approach:

1. Run config-file spec that is sensible to on-way changes two times with an interval greater than time needed to propagate data between the two DBs, and
2. include in the report only discrepancies that were found by both the first run and the second run and remained unchanged between the two runs.

Discrepancies found by the first run and not found by the second were caused by data changes on way at the time of the first run. Discrepancies found by the second run and not by the first are those caused by data changes on way at the time of the second run. And only discrepancies found by both runs are considered as persistent and go to the discrepancies report.

This approach is supported by the `ddiff` command line options:

```
-1, --one      find discrepancies and store them
-2, --two      find discrepancies and intersect them with the stored
```

To see how it works let's look at the spec `"current"` from the config-file `ddiff-test-sqlite.py`:

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

If you execute the spec as usual you'll get the following discrepancies in the report:

```
c1 DB1 c2              DB2 c2              DB1 c3 DB2 c3
-- ------------------- ------------------- ------ ------
 1 2023-08-29 04:20:18 2023-08-29 04:20:23      3      3
 2 2023-08-29 04:20:18 2023-08-29 04:20:18      5      6
 3 2023-08-29 04:20:18 [NULL]                   7 [NULL]
 4 [NULL]              2023-08-29 04:20:18 [NULL]      9
```

Notice that the discrepancy in row `c1 = 1` is due to the fact that column `c2` from the query against DB `ONE` contains current time while column `c2` from DB `TWO` query contains current time plus 5 seconds. Each time we execute thses queries we get new values in column `c2` – the time goes. And `c2` values in rows `c1 = 1` returned by the two queries differ by 5 seconds. Thus the data changes curently on way between DBs are simulated.

Let's execute the spec so that to exclude current data changes form the discrepancies report. First run:

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

The row `с1 = 1` was excluded from the report because discrepancies found in this row by the first run and by the second are not the same. Hence they are considered as the ones caused by the on-way changes currently being propagated between the DBs. Whereas rows where `c1` equals 2, 3 and 4 showed the same discrepancies in both runs, and row `c1 = 5` showed no discrepancies.
