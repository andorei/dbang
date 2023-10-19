# dget. Getting data from database into file

`dget` retrieves data from DB and writes it to `csv`, `xlsx`, `json` or `html` file, accoring to the config-file spec.

Here are example specs where a row with two fields is retrieved from DB and is written to a file. The spec name gives the name for the file and its format:

```
sources['.'] = sources['sqlite-source']

specs = {
    "hello world.csv": {
        "source": ".",
        "query": "select 'Hello world!', 42 from dual",
        "titles": "select 'Привет', 'Ответ' from dual"
    },
    "hello world.xlsx": {
        "source": ".",
        "query": "select 'Hello world!'  as hello, 42 as answer from dual"
    },
    "hello world.json": {
        "source": ".",
        "query": "select 'Hello world!', 42 from dual",
        "titles": ["Hello", "Answer"]
    },
    "hello world.html": {
        "source": ".",
        "query": "select 'Hello world!', 42 from dual",
        "titles": ["Hello", "Answer"]
    },
    ...
}

sources['sqlite-source']['setup'] = sources['sqlite-source'].get('setup', []) + [
    "create table if not exists dual as select 'X' as dummy"
]

sources['postgres-source']['setup'] = sources['postgres-source'].get('setup', []) + [
    "create table if not exists dual as select 'X' as dummy"
]
```

Optional parameter `"titles"` allows to set column titles

* as a list of strings, like in spec `"hello world.html"`,
* or as a query against DB, which returns strings, like in spec `"hello world.csv"`.

If parameter `"titles"` is omitted then `dget` uses column aliases from the `"query"`, like in spec `"hello world.xlsx"`.

`dget` allows to dynamically generate queries, execute them and write their results to a file. If `"query"` from the spec returns the only string value with alias `query`, then `dget` uses this string value as a query to execute.

For example, the query against PosqreSQL DB in the next spec produces a query to get number of rows in all the tables in current schema which names end with `_h`:

```
specs = {
    "rowcount.html": {
         "source": "postgres-source",
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

`json` and `html` files are built by default using jinja2 templates `dget.json.jinja` and `dget.html.jinja`, respectively, located in `cfg` directory. You can create your own jinja2 templates, using the same variables as in the default templates. To use your own template in a config-file specification set its name in the spec parameter `"template"`.

Test config-file `dget-test.py` contains comments on all the spec parameters. Read it carefully and familiarize yourself with all the parameters.


## `dget` Case No 1

You must have heard about self-service business intelligence (SSBI). What might it look like in a simple case?

Day after day company's IT department gets requests to download from DB into `xlsx` file

* all articles of category Shoes and of season Spring-Summer 23,
* all articles with special trasnporation conditions,
* new articles introduced during the last month,
* new articles managed by manager Smith,
* etc.

These and other similar requests can be satisfied with a single download of articles with all the required attributes: category, season, transportation conditions, date of sales start, manager name. You only need to periodically download the data into a file available to all the interested parties.

Now a person who needs the list of all articles belonging to Shoes category and Spring-Summer 23 season has to just open the file in Excel and filter the spreadsheet by columns Category and Season. Other employees should do the same way.

To download the article data periodically you should write a `dget` spec with appropriate SQL query and schedule execution of `dget.py` with that spec on a periodic basis (using `crontab` on Linux or Task Scheduler on Windows).


## `dget` Case No 2

Put the result of SQL query into `html` file and send it to the addressees as a table in the body of email message.

The data in html-table might represent

* errors registered in a log table during last hour,
* periodic report (on users activity, on status of business-processes, etc.),
* notification on a special event that requires user's attention.

If `html` file to be sent is too big to insert its content into the message body you might instead attach it to the email message.

Composing email messages and sending them to interested parties is what `hedwig` utility does for you (according to specs in a config-file).
