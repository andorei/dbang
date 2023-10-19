# dtest. Testing and reporting data quality

`dtest` executes queries from config-file specs against a relational database, and generates report on data quality in html format.

When I need to make sure there are no data in a database that violate a given rule I write a query to select data violating that rule. For example,

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

If the query returns no rows it is a good result.

If the query returns one or more rows of data then the rule is violated and I need to correct the data.

Here is an example of `dtest` specs with the above queries (a bit modified):

```
import os
import sys

from sources import sources


# MANDATORY constants used by dtest.py
OUT_DIR = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), 'out')

# Optional constants used in specs below
# ...

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

Test config-file `dtest-test.py` contains comments on all the spec parameters. Read it carefully and familiarize yourself with all the parameters.
