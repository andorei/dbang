#!/usr/bin/python3

import os
import sys
import argparse
import logging
import decimal as dec
from datetime import date, datetime
from math import ceil

from jinja2 import Template


VERSION = '0.2'

parser = argparse.ArgumentParser(
    description="Detect discrepancies in two databases as specified in cfg-file specs.",
    epilog="Thanks for using %(prog)s!"
)

parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + VERSION)
parser.add_argument("cfg_file", help="cfg-file name")
parser.add_argument("spec", nargs="?", default="all", help="spec name, defaults to \"all\"")
parser.add_argument("-1", "--one", action='store_true', help="find discrepancies and store them")
parser.add_argument("-2", "--two", action='store_true', help="find discrepancies and intersect them with the stored")

args = parser.parse_args()

BASENAME = os.path.basename(sys.argv[0])
SCRIPT_DIR = os.path.dirname(os.path.realpath(sys.argv[0]))
CFG_DIR = os.path.join(SCRIPT_DIR, 'cfg')
CFG_NAME = args.cfg_file.split('.')[0]
CFG_FILE = f"{CFG_NAME}.py"
if not os.path.isfile(os.path.join(CFG_DIR, CFG_FILE)):
    sys.stderr.write(
        parser.format_usage() + \
        f"{BASENAME}: error: cfg-file not found: {CFG_FILE}\n"
    )
    sys.exit(1)

sys.path.append(CFG_DIR)
cfg = __import__(CFG_NAME)
sources = cfg.sources
specs = cfg.specs

SPEC = args.spec
if SPEC not in [*specs.keys(), 'all']:
    sys.stderr.write(
        parser.format_usage() + \
        f"{BASENAME}: error: spec not found in cfg-file: {SPEC}\n"
    )
    sys.exit(1)

BASENAME = os.path.basename(sys.argv[0]).split('.')[0]
LOG_FILE = os.path.join(SCRIPT_DIR, 'log', f'{date.today().isoformat()}_{BASENAME}.log')
OUT_DIR = getattr(cfg, 'OUT_DIR', os.path.join(SCRIPT_DIR, 'out'))
OUT_FILE = os.path.join(OUT_DIR, '{}.html')
DEBUGGING = getattr(cfg, 'DEBUGGING', False)
LOGSTDOUT = getattr(cfg, 'LOGSTDOUT', False)

# keep data in ddiff_ table after test completion
DDIFF_KEEP = False
# number of rows to fetch with one fetch
ONE_FETCH_ROWS = 5000
# number of fetched rows at which we go no futher
MAX_FETCH_ROWS = 1000000
# number of mismatchs at which we go no deeper
MAX_DISCREPANCIES = 1000

INSERT_RESULTS = """
insert into ddiff_ (
    cfg,spec,run,source,{% for i, col in (c['pk'] + c['cols']) %}c{{loop.index}}{{"," if not loop.last}}{% endfor %})
values (
{%- if database == 'sqlite' %}
    ?,?,?,?,{% for i, col in (c['pk'] + c['cols']) %}?{{"," if not loop.last}}{% endfor %}
{%- elif database == 'postgres' %}
    %s,%s,%s,%s,{% for i, col in (c['pk'] + c['cols']) %}%s{{"," if not loop.last}}{% endfor %}
{%- elif database == 'mysql' %}
    %s,%s,%s,%s,{% for i, col in (c['pk'] + c['cols']) %}%s{{"," if not loop.last}}{% endfor %}
{%- elif database == 'oracle' %}
    :cfg,:spec,:run,:source,{% for i, col in (c['pk'] + c['cols']) %}:{{i}}{{"," if not loop.last}}{% endfor %}
{%- endif %}
)
"""
SELECT_RESULTS = """
with d1 as (
    select {% for col in (c['pk'] + c['cols']) %}c{{loop.index}}{{"," if not loop.last}}{% endfor %}
    from ddiff_
    where cfg='{{cfg}}' and spec = '{{spec}}' and run = {{run[0]}} and source = '{{c['sources'][0]}}'
    {% if database == 'oracle' %}minus{% else %}except{% endif%}
    select {% for col in (c['pk'] + c['cols']) %}c{{loop.index}}{{"," if not loop.last}}{% endfor %}
    from ddiff_
    where cfg='{{cfg}}' and spec = '{{spec}}' and run = {{run[0]}} and source = '{{c['sources'][1]}}'
), d2 as (
    select {% for col in (c['pk'] + c['cols']) %}c{{loop.index}}{{"," if not loop.last}}{% endfor %}
    from ddiff_
    where cfg='{{cfg}}' and spec = '{{spec}}' and run = {{run[0]}} and source = '{{c['sources'][1]}}'
    {% if database == 'oracle' %}minus{% else %}except{% endif%}
    select {% for col in (c['pk'] + c['cols']) %}c{{loop.index}}{{"," if not loop.last}}{% endfor %}
    from ddiff_
    where cfg='{{cfg}}' and spec = '{{spec}}' and run = {{run[0]}} and source = '{{c['sources'][0]}}'
)
{%- if op == '<' or op == '=' %}
select
    {%- for i, col in c['pk'] %}
    coalesce(d1.c{{i}}, d2.c{{i}}) "{{col}}"{{"," if not loop.last or c['cols']}}
    {%- endfor %}
    {%- for i, col in c['cols'] %}
    d1.c{{i}} "DB1 {{col}}", d2.c{{i}} "DB2 {{col}}"{{"," if not loop.last}}
    {%- endfor %}
from d1 left join d2 on {% for i, col in c['pk'] %} d1.c{{i}} = d2.c{{i}}{{" and " if not loop.last}}{% endfor %}
{%- endif %}
{%- if op == '=' %}
union
{%- endif %}
{%- if op == '>' or op == '=' %}
select
    {%- for i, col in c['pk'] %}
    coalesce(d1.c{{i}}, d2.c{{i}}) "{{col}}"{{"," if not loop.last or c['cols']}}
    {%- endfor %}
    {%- for i, col in c['cols'] %}
    d1.c{{i}} "DB1 {{col}}", d2.c{{i}} "DB2 {{col}}"{{"," if not loop.last}}
    {%- endfor %}
from d2 left join d1 on {% for i, col in c['pk'] %} d1.c{{i}} = d2.c{{i}}{{" and " if not loop.last}}{% endfor %}
{%- endif %}
order by {% for i, col in c['pk'] %}{{loop.index}}{{"," if not loop.last}}{% endfor %}
"""
INSERT_DIFFS = """
insert into ddiff_diffs_ (
    cfg,spec,run,{% for i, col in (c['pk'] + c['cols'] + c['cols']) %}c{{loop.index}}{{"," if not loop.last}}{% endfor %})
values (
{%- if database == 'sqlite' %}
    ?,?,?,{% for i, col in (c['pk'] + c['cols'] + c['cols']) %}?{{"," if not loop.last}}{% endfor %}
{%- elif database == 'postgres' %}
    %s,%s,%s,{% for i, col in (c['pk'] + c['cols'] + c['cols']) %}%s{{"," if not loop.last}}{% endfor %}
{%- elif database == 'mysql' %}
    %s,%s,%s,{% for i, col in (c['pk'] + c['cols'] + c['cols']) %}%s{{"," if not loop.last}}{% endfor %}
{%- elif database == 'oracle' %}
    :cfg,:spec,:run,{% for i, col in (c['pk'] + c['cols'] + c['cols']) %}:{{i}}{{"," if not loop.last}}{% endfor %}
{%- endif %}
)
"""
SELECT_DIFFS = """
with t1 as (
    select {% for i in pk_nums %}c{{i}},{% endfor %}
        {% for i in col_nums %}case when c{{i}} != c{{i+1}} then c{{i}}||c{{i+1}} when c{{i}} = c{{i+1}} then null else 'x' end c{{i}}{{"," if not loop.last}}{% endfor %}
    from ddiff_diffs_
    where cfg = '{{cfg}}' and spec = '{{spec}}' and run = (
            select max(run) from ddiff_diffs_ where cfg='{{cfg}}' and spec='{{spec}}' and run != {{run[0]}}
        )
), t2 as (
    select {% for i in pk_nums %}c{{i}},{% endfor %}
        {% for i in col_nums %}case when c{{i}} != c{{i+1}} then c{{i}}||c{{i+1}} when c{{i}} = c{{i+1}} then null else 'x' end c{{i}}{{"," if not loop.last}}{% endfor %}
    from ddiff_diffs_
    where cfg = '{{cfg}}' and spec = '{{spec}}' and run = {{run[0]}}
), tt as (
    select {% for i in pk_nums %}t1.c{{i}}{{"," if not loop.last}}{% endfor %}
    from t1
        join t2 on ({% for i in pk_nums %}t1.c{{i}}{{"," if not loop.last}}{% endfor %}) = ({% for i in pk_nums %}t2.c{{i}}{{"," if not loop.last}}{% endfor %})
    where {% for i in col_nums %}t1.c{{i}} = t2.c{{i}}{{" or " if not loop.last}}{% endfor %}
)
select {% for i in pk_nums %}dd.c{{i}},{% endfor %}{% for i in col_nums %}dd.c{{i}},dd.c{{i+1}}{{"," if not loop.last}}{% endfor %}
from ddiff_diffs_ dd 
    join tt on ({% for i in pk_nums %}dd.c{{i}}{{"," if not loop.last}}{% endfor %}) = ({% for i in pk_nums %}tt.c{{i}}{{"," if not loop.last}}{% endfor %})
where cfg = '{{cfg}}' and spec = '{{spec}}' and run = {{run[0]}}
order by {% for i in pk_nums %}{{loop.index}}{{"," if not loop.last}}{% endfor %}
"""
TEST_REPORT="""
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="content-type" content="text/html; charset=UTF-8">
    <style type="text/css">
        th {background:lightblue; padding: 1px 5px 1px 5px;}
        td {background:lightgrey; padding: 1px 5px 1px 5px; text-align: left;}
    </style>
<title>Data Discrepancies Report ({{cfg}}): {{test}}</title>
</head>
<body>
<h2><a href="{{cfg}}.html">Data Discrepancies Report ({{cfg}})</a>: {{test}}</h2>
{%- if rows %}
{%- for row in rows %}
{%- if loop.first %}
<p>
{{run[1]}}. DB1 = {{sources[0]}}, DB2 = {{sources[1]}}. <span style="color:red;">Found {{rows|length}} discrepancies. </span>
{% for warn in warnings %}{{warn}} {% endfor %}
</p>
<table>
<tr>{% for title in titles %}<th>{{title}}</th>{% endfor %}</tr>
{%- endif %}
<tr>
{%- for col in row %}
    {%- if col is iterable and col is not string %}
        {%- if col[0] == col[1] %}
        <td>{{col[0] if col[0] is not none else '[NULL]'}}</td><td>{{col[1] if col[1] is not none else '[NULL]'}}</td>
        {%- else%}
        <td style="color:red;">{{col[0] if col[0] is not none else '[NULL]'}}</td><td style="color:red;">{{col[1] if col[1] is not none else '[NULL]'}}</td>
        {%- endif %}
    {%- else %}
        <td>{{col if col is not none else '[NULL]'}}</td>
    {%- endif %}
{%- endfor %}
</tr>
{%- if loop.last %}
</table>
{%- endif %}
{%- endfor %}
{%- else %}
<p style="color:green;">Found 0 discrepancies.</p>
{%- endif %}
</body>
</html>
"""
RUN_REPORT="""
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="content-type" content="text/html; charset=UTF-8">
    <style type="text/css">
        th {background:lightblue; padding: 1px 5px 1px 5px;}
        td {background:lightgrey; padding: 1px 5px 1px 5px; text-align: left;}
    </style>
<title>Data Discrepancies Report ({{cfg}})</title>
</head>
<body>
<h2>Data Discrepancies Report ({{cfg}})</h2>
{%- if rows %}
{%- for row in rows %}
{%- if loop.first %}
<p>
{{run[1]}}. 
{% if succeeded > 0 %}<span style="color:green;">{{succeeded}} test{% if succeeded > 1 %}s{% endif%} succeeded. </span>{% endif %}
{% if failed > 0 %}<span style="color:red;">{{failed}} test{% if failed > 1 %}s{% endif%} failed. </span>{% endif %}
{% if not_run > 0 %}{{not_run}} test{% if not_run > 1 %}s{% endif%} failed to run.{% endif %}
</p>
<table style="min-width:35%;">
<tr><th>Test</th><th>DB1</th><th>DB2</th><th>Result</th><th>Warning</th></tr>
{%- endif %}
<tr>
    <td>{{row[0]}}</td>
    <td>{{row[3]}}</td>
    <td>{{row[4]}}</td>
    <td>{% if row[1] == 0 %}<span style="color:green;">Success.</span>{% elif row[1] == -1 %}Failed to run.{% else %}<a href="{{cfg}}_{{row[0]}}.html" style="color:red;">Found {{row[1]}} discrepancies.</a>{% endif %}</td>
    <td>{% if row[2] %}{% for warn in row[2] %}{{warn}}{{"<br/>" if not loop.last}}{% endfor %}{% endif %}</td>
</tr>
{%- if loop.last %}
</table>
{%- endif %}
{%- endfor %}
{%- else %}
<p>No tests.</p>
{%- endif %}
</body>
</html>
"""


logging.basicConfig(
    filename=None if LOGSTDOUT else LOG_FILE,
    format='%(asctime)s:%(levelname)s:%(name)s:%(message)s',
    level=logging.INFO
)
logger = logging.getLogger(BASENAME)

select_tpl = Template(SELECT_RESULTS)
insert_tpl = Template(INSERT_RESULTS)
select_diffs_tpl = Template(SELECT_DIFFS)
insert_diffs_tpl = Template(INSERT_DIFFS)
test_report_tpl = Template(TEST_REPORT)
run_report_tpl = Template(RUN_REPORT)


def exec_sql(con, sql):
    if sql:
        cur = con.cursor()
        if isinstance(sql, str):
            if DEBUGGING:
                logger.info('\n\n' + sql.strip() + '\n')
            cur.execute(sql)
        elif isinstance(sql, (list, tuple)):
            for stmt in sql:
                if DEBUGGING:
                    logger.info('\n\n' + stmt.strip() + '\n')
                cur.execute(stmt)
        cur.close()


def connection(src):
    if isinstance(src, str):
        source = sources[src]
    elif isinstance(src, dict):
        source = src
    if not source.get('con'):
        if source.get('con_string'):
            source['con'] = \
                source['lib'].connect(source['con_string'], **source.get('con_kwargs', dict()))
        else:
            source['con'] = source['lib'].connect(**source['con_kwargs'])
        if source['database'] == 'oracle':
            # see https://cx-oracle.readthedocs.io/en/latest/user_guide/sql_execution.html#fetched-number-precision.
            def number_to_decimal(cursor, name, default_type, size, precision, scale):
                if default_type == source['lib'].DB_TYPE_NUMBER:
                    return cursor.var(dec.Decimal, arraysize=cursor.arraysize)
            source['con'].outputtypehandler = number_to_decimal
        if source.get('setup'):
            if DEBUGGING:
                logger.info('-- setup')
            exec_sql(source['con'], source['setup'])
    return source['con']


def pump(run, spec_name, spec, con0, argrows, source_idx):
    con = connection(spec['sources'][source_idx])
    cur = con.cursor()
    query = spec['queries'][source_idx]

    cur0 = con0.cursor()
    rowcount = 0
    query_tpl = None

    # to keep the query reasonably short we should split long argrows lists
    # into sereval shorter lists and execute several short selects/inserts
    if argrows:
        parts = ceil(len(argrows) / 200)
    else:
        parts = 1

    if DEBUGGING:
        logger.info(f"-- select {spec['sources'][source_idx]} dataset into ddiff_: {parts} time(s)")

    for part in range(parts):
        if argrows:
            if query_tpl is None:
                query_tpl = Template(query)
            query = query_tpl.render(argrows=argrows[part*200:part*200+200])
            if DEBUGGING:
                logger.info('\n\n' + query.strip() + '\n')
        else:
            if DEBUGGING and part == 0:
                logger.info('\n\n' + query.strip() + '\n')
        cur.execute(query)

        if spec.get('cols') is None:
            spec['cols'] = [(i + 1, d[0].lower()) for i, d in enumerate(cur.description) if d[0].lower() not in spec['pk']]
            spec['pk'] = [(i + 1, d[0].lower()) for i, d in enumerate(cur.description) if d[0].lower() in spec['pk']]
            spec['insert'] = insert_tpl.render(c=spec, database=cfg.DDIFF_SOURCE['database'])
            if DEBUGGING:
                logger.info('\n\n' + spec['insert'].strip() + '\n')

        while rowcount < MAX_FETCH_ROWS:
            # get next bunch of rows
            res = cur.fetchmany(ONE_FETCH_ROWS)
            if not res:
                break
            rowcount += len(res)
            # insert next bunch of rows
            #logger.info(res)
            cur0.executemany(
                spec['insert'],
                # cx_Oracle requires list here - not a tuple, not a generator expr.
                [(CFG_NAME, spec_name, run[0], spec['sources'][source_idx]) + row for row in res]
            )
    cur.close()
    cur0.close()
    return rowcount


def process(run, spec_name, spec, con0, argrows):
    try:
        assert (
            isinstance(spec, dict)
            and {*spec.keys()} >= {'pk', 'sources', 'queries'}
            and spec['pk'].__class__ in (list, tuple)
            and spec['sources'].__class__ in (list, tuple)
            and spec['queries'].__class__ in (list, tuple)
            and len(spec['sources']) == 2
            and len(spec['queries']) == 2
            and sources.get(spec['sources'][0])
            and sources.get(spec['sources'][1])
            and spec.get('op', '=').__class__ == str
            and spec.get('op', '=') in ('<', '>', '=')
            ), f"Bad spec {spec_name}"

        if spec.get('cols') is None:
            logger.info(f"test {spec_name}; DB1 = {spec['sources'][0]}, DB2 = {spec['sources'][1]}")
            specs[spec_name]['warnings'] = []

        we_have_1st_pass_diffs = False
        if args.two:
            # Check if we have discrepancies from the first pass.
            cur0 = con0.cursor()
            cur0.execute(f"select count(*) from ddiff_diffs_ where cfg='{CFG_NAME}' and spec='{spec_name}'")
            we_have_1st_pass_diffs = (cur0.fetchone()[0] > 0)

        rows = []
        if not args.two or we_have_1st_pass_diffs:
            # Get 1st and 2nd query results and insert them into ddiff_ table.
            rowcount1 = pump(run, spec_name, spec, con0, argrows, 0)
            rowcount2 = pump(run, spec_name, spec, con0, argrows, 1)

            if MAX_FETCH_ROWS <= max(rowcount1, rowcount2):
                specs[spec_name]['warnings'].append(f"DB1: {rowcount1} rows, DB2: {rowcount2} rows.")

            # Get differences between 1st and 2nd query results.
            select = \
                select_tpl.render(
                    cfg=CFG_NAME,
                    spec=spec_name,
                    run=run,
                    c=spec,
                    database=cfg.DDIFF_SOURCE['database'],
                    op=spec.get('op', '=')
                )
            if DEBUGGING:
                logger.info('-- select discrepancies from ddiff_')
                logger.info('\n\n' + select.strip() + '\n')
            cur0 = con0.cursor()
            cur0.execute(select)
            rows = cur0.fetchall()

            if rows:
                if spec.get(spec_name) and len(rows) <= MAX_DISCREPANCIES * (100 if args.one or args.two else 1):
                    # Delete intermediate query results from ddiff_ table.
                    con0.rollback()
                    if not spec[spec_name].get('sources'):
                        spec[spec_name]['sources'] = spec['sources']
                    if spec.get('op') and not spec[spec_name].get('op'):
                        spec[spec_name]['op'] = spec['op']
                    process(run, spec_name, spec[spec_name], con0, rows)
                else:
                    titles=(x[0] for x in cur0.description)

                    if args.one or args.two:
                        # Store the found discrepancies in ddiff_diffs_ table.
                        insert_diffs = insert_diffs_tpl.render(c=spec, database=cfg.DDIFF_SOURCE['database'])
                        if DEBUGGING:
                            logger.info('-- insert discrepancies into ddiff_diffs_')
                            logger.info('\n\n' + insert_diffs.strip() + '\n')
                        cur0.executemany(
                            insert_diffs,
                            # cx_Oracle requires list here - not a tuple, not a generator expr.
                            [(CFG_NAME, spec_name, run[0]) + row for row in rows]
                        )

                    if args.two:
                        # Intersect the newly found discrepancies with the stored.
                        select_diffs = \
                            select_diffs_tpl.render(
                                cfg=CFG_NAME,
                                spec=spec_name,
                                run=run,
                                #c=spec,
                                pk_nums=[i+1 for i in range(len(spec['pk']))],
                                col_nums=[i+1+len(spec['pk']) for i in range(0, len(spec['cols']) * 2, 2)],
                                database=cfg.DDIFF_SOURCE['database'],
                            )
                        if DEBUGGING:
                            logger.info('-- select persistent discrepancies from ddiff_diffs_')
                            logger.info('\n\n' + select_diffs.strip() + '\n')
                        cur0.execute(select_diffs)
                        rows = cur0.fetchall()

                    if not args.one and rows:
                        # TODO Generate multi-page test reports OR limit number of rows in the report
                        if spec.get(spec_name) and len(rows) > MAX_DISCREPANCIES * (100 if args.one or args.two else 1):
                            specs[spec_name]['warnings'].append(f"Found {len(rows)} discrepancies, go no deeper.")
                        cols_index = len(spec['pk'])
                        test_report = \
                            test_report_tpl.render(
                                cfg=CFG_NAME,
                                run=run,
                                test=spec_name,
                                #rows=rows,
                                rows=tuple(tuple(row[:cols_index]) + tuple(x for x in zip(row[cols_index::2], row[cols_index+1::2])) for row in rows),
                                #titles=(x[0] for x in cur0.description),
                                titles=titles,
                                warnings=specs[spec_name].get('warnings'),
                                sources=specs[spec_name]['sources']
                            )
                        test_report_file = OUT_FILE.format(f"{CFG_NAME}_{spec_name}")
                        with open(test_report_file, 'w', encoding="UTF-8") as f:
                            f.write(test_report)

                    logger.info(f"Found {len(rows)} discrepancies.")
                    specs[spec_name]['result'] = len(rows)
            else:
                logger.info(f"Found {len(rows)} discrepancies.")
                specs[spec_name]['result'] = len(rows)
        else:
            logger.info(f"Found {len(rows)} discrepancies.")
            specs[spec_name]['result'] = len(rows)

        if not DDIFF_KEEP:
            cur0.execute("delete from ddiff_")
        con0.commit()
    except:
        logger.exception('EXCEPT')
        for src in sources.values():
            if src.get('con'):
                src['con'].rollback()


def main():
    logger.info(f'-- start {" ".join(sys.argv)}')

    _temp = datetime.now()
    run = [
        int(_temp.strftime('%Y%m%d%H%M%S')),
        _temp.strftime('%Y-%m-%d %H:%M:%S'),
        _temp.strftime('%Y-%m-%d_%H-%M-%S')
    ]
    logger.info(f"run {run[0]}")
    if DEBUGGING:
        logger.info(f"args: {args}")

    con0 = None
    for spec_name, spec in specs.items():
        if SPEC in (spec_name, 'all'):
            for src in (sources[spec['sources'][0]], sources[spec['sources'][1]], cfg.DDIFF_SOURCE):
                if src.get('lib') is None:
                    if src["database"] == "oracle":
                        import cx_Oracle
                        src["lib"] = cx_Oracle
                    elif src["database"] == "postgres":
                        import psycopg2
                        #from psycopg2 import extras
                        src["lib"] = psycopg2
                    elif src["database"] == "mysql":
                        import mysql.connector
                        src["lib"] = mysql.connector
                    elif src["database"] == "sqlite":
                        import sqlite3
                        src["lib"] = sqlite3
                        # Setup the adaptor in order to save decimals as text
                        # uniformely without trailing zeros and a trailing dot.
                        def decimal_to_text(d):
                            s = str(d)
                            # postgres decimal 0 might turn into smth like 0E-20
                            return s.rstrip('0').rstrip('.') if '.' in s else '0' if d == 0 else s
                        sqlite3.register_adapter(dec.Decimal, decimal_to_text)
                    else:
                        src["lib"] = None
            con0 = connection(cfg.DDIFF_SOURCE)
            process(run, spec_name, spec, con0, spec.get('argrows', []))

    if not args.one:
        run_results = [
            (spec_name, spec.get('result', -1), spec.get('warnings'), spec['sources'][0], spec['sources'][1])
            for spec_name, spec in specs.items() if SPEC in (spec_name, 'all')
        ]
        succeeded = len([1 for x in run_results if x[1] == 0])
        failed = len([1 for x in run_results if x[1] > 0])
        not_run = len([1 for x in run_results if x[1] == -1])
        run_report = \
            run_report_tpl.render(
                cfg=CFG_NAME,
                run=run,
                rows=run_results,
                succeeded=succeeded,
                failed=failed,
                not_run=not_run
            )
        run_report_file = OUT_FILE.format(f"{CFG_NAME}")
        with open(run_report_file, 'w', encoding="UTF-8") as f:
            f.write(run_report)

        if not DDIFF_KEEP:
            cur0 = con0.cursor()
            cur0.execute(f"delete from ddiff_diffs_ where cfg = '{CFG_NAME}'")
            con0.commit()

    for src in sources.values():
        if src.get('con'):
            if src.get('upset'):
                if DEBUGGING:
                    logger.info('-- upset')
                exec_sql(src['con'], src.get('upset'))
            src['con'].close()
            src['con'] = None

    logger.info('-- done')


if __name__ == '__main__':
    main()
