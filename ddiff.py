#!/usr/bin/python3

import os
import sys
import logging
import decimal as dec
from datetime import date, datetime

from jinja2 import Template


DEBUGGING = True
LOGSTDOUT = True

BASENAME = os.path.basename(sys.argv[0])
if len(sys.argv) not in (2, 3):
    sys.stderr.write(f"{BASENAME}: Need config-file to proceed.\n")
    sys.stderr.write(
        f"""
        Error: Wrong number of arguments.
        Usage: {BASENAME} <cfg-file> [<spec> | all]
        """
    )
    sys.exit(1)

SCRIPT_DIR = os.path.dirname(os.path.realpath(sys.argv[0]))
CFG_DIR = os.path.join(SCRIPT_DIR, 'cfg')
CFG_NAME = sys.argv[1].split('.')[0]
CFG_FILE = f"{CFG_NAME}.py"
if not os.path.isfile(os.path.join(CFG_DIR, CFG_FILE)):
    sys.stderr.write(
        f"""
        Error: Config-file {CFG_FILE} not found.
        Usage: {BASENAME} <cfg-file> [<spec> | all]
        """
    )
    sys.exit(1)

sys.path.append(CFG_DIR)
cfg = __import__(CFG_NAME)
sources = cfg.sources
specs = cfg.specs

SPEC = sys.argv[2] if len(sys.argv) == 3 else 'all'
if SPEC not in [*specs.keys(), 'all']:
    sys.stderr.write(
        f"""
        Error: Spec {SPEC} not found in config-file.
        Usage: {BASENAME} <cfg-file> [<spec> | all]
        """
    )
    sys.exit(1)

for source in sources.values():
    if source["database"] == "oracle":
        import cx_Oracle
        source["lib"] = cx_Oracle
    elif source["database"] == "postgres":
        import psycopg2
        source["lib"] = psycopg2
    elif source["database"] == "sqlite":
        import sqlite3
        # Setup the adaptor in order to save decimals as text
        # uniformely without trailing zeros and a trailing dot.
        def decimal_to_text(d):
            s = str(d)
            # postgres decimal 0 might turn into smth like 0E-20
            return s.rstrip('0').rstrip('.') if '.' in s else '0' if d == 0 else s
        sqlite3.register_adapter(dec.Decimal, decimal_to_text)
        source["lib"] = sqlite3
    else:
        source["lib"] = None

BASENAME = os.path.basename(sys.argv[0]).split('.')[0]
LOG_FILE = os.path.join(SCRIPT_DIR, 'log', f'{date.today().isoformat()}_{BASENAME}.log')
OUT_FILE = os.path.join(SCRIPT_DIR, 'out', '{}.html')

# data source with ddiff_ table
DDIFF_SOURCE = "."
# keep data in ddiff_ table after test completion
DDIFF_KEEP = False
# number of rows to fetch with one fetch
ONE_FETCH_ROWS = 5000
# number of fetched rows at which we go no futher
MAX_FETCH_ROWS = 100000
# number of mismatchs at which we go no deeper
MAX_DISCREPANCIES = 200

INSERT_RESULTS = """
insert into ddiff_ (
    run,test,source,{% for i, col in (c['pk'] + c['cols']) %}c{{loop.index}}{{"," if not loop.last}}{% endfor %})
values (
{%- if database == 'sqlite' %}
    ?,?,?,{% for i, col in (c['pk'] + c['cols']) %}?{{"," if not loop.last}}{% endfor %}
{%- elif database == 'postgres' %}
    %s,%s,%s,{% for i, col in (c['pk'] + c['cols']) %}%s{{"," if not loop.last}}{% endfor %}
{%- elif database == 'oracle' %}
    :run,:test,:source,{% for i, col in (c['pk'] + c['cols']) %}:{{i}}{{"," if not loop.last}}{% endfor %}
{%- endif %}
)
"""
SELECT_RESULTS = """
with d1 as (
    select {% for col in (c['pk'] + c['cols']) %}c{{loop.index}}{{"," if not loop.last}}{% endfor %}
    from ddiff_
    where run = {{run[0]}} and test = '{{test}}' and source = '{{c['sources'][0]}}'
    {% if database == 'oracle' %}minus{% else %}except{% endif%}
    select {% for col in (c['pk'] + c['cols']) %}c{{loop.index}}{{"," if not loop.last}}{% endfor %}
    from ddiff_
    where run = {{run[0]}} and test = '{{test}}' and source = '{{c['sources'][1]}}'
), d2 as (
    select {% for col in (c['pk'] + c['cols']) %}c{{loop.index}}{{"," if not loop.last}}{% endfor %}
    from ddiff_
    where run = {{run[0]}} and test = '{{test}}' and source = '{{c['sources'][1]}}'
    {% if database == 'oracle' %}minus{% else %}except{% endif%}
    select {% for col in (c['pk'] + c['cols']) %}c{{loop.index}}{{"," if not loop.last}}{% endfor %}
    from ddiff_
    where run = {{run[0]}} and test = '{{test}}' and source = '{{c['sources'][0]}}'
)
select
    {%- for i, col in c['pk'] %}
    coalesce(d1.c{{i}}, d2.c{{i}}) "{{col}}"{{"," if not loop.last or c['cols']}}
    {%- endfor %}
    {%- for i, col in c['cols'] %}
    d1.c{{i}} "DB1 {{col}}", d2.c{{i}} "DB2 {{col}}"{{"," if not loop.last}}
    {%- endfor %}
from d1 left join d2 on {% for i, col in c['pk'] %} d1.c{{i}} = d2.c{{i}}{{" and " if not loop.last}}{% endfor %}
union
select
    {%- for i, col in c['pk'] %}
    coalesce(d1.c{{i}}, d2.c{{i}}) "{{col}}"{{"," if not loop.last or c['cols']}}
    {%- endfor %}
    {%- for i, col in c['cols'] %}
    d1.c{{i}} "DB1 {{col}}", d2.c{{i}} "DB2 {{col}}"{{"," if not loop.last}}
    {%- endfor %}
from d2 left join d1 on {% for i, col in c['pk'] %} d1.c{{i}} = d2.c{{i}}{{" and " if not loop.last}}{% endfor %}
order by {% for i, col in c['pk'] %}{{loop.index}}{{"," if not loop.last}}{% endfor %}
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
        <td>{{col[0] if col[0] is not none else '<NULL>'}}</td><td>{{col[1] if col[1] is not none else '<NULL>'}}</td>
        {%- else%}
        <td style="color:red;">{{col[0] if col[0] is not none else '<NULL>'}}</td><td style="color:red;">{{col[1] if col[1] is not none else '<NULL>'}}</td>
        {%- endif %}
    {%- else %}
        <td>{{col if col is not none else '<NULL>'}}</td>
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
test_report_tpl = Template(TEST_REPORT)
run_report_tpl = Template(RUN_REPORT)


def connection(src):
    if not sources[src].get('con'):
        sources[src]['con'] = \
            sources[src]['lib'].connect(sources[src]['con_string'], **sources[src].get('con_qwargs', dict()))
        if sources[src]['database'] == 'oracle':
            # see https://cx-oracle.readthedocs.io/en/latest/user_guide/sql_execution.html#fetched-number-precision.
            def number_to_decimal(cursor, name, default_type, size, precision, scale):
                if default_type == cx_Oracle.DB_TYPE_NUMBER:
                    return cursor.var(dec.Decimal, arraysize=cursor.arraysize)
            sources[src]['con'].outputtypehandler = number_to_decimal
        if sources[src].get('init'):
            if isinstance(sources[src]['init'], str):
                sources[src]['init'] = [sources[src]['init']]
            cur = sources[src]['con'].cursor()
            for init in sources[src]['init']:
                if DEBUGGING:
                    logger.info('\n\n' + init.strip() + '\n')
                cur.execute(init)
            cur.close()
            sources[src]['con'].commit()
    return sources[src]['con']


def pump(run, spec_name, spec, con0, argrows, i):
    cur0 = con0.cursor()
    rowcount = 0

    con = connection(spec['sources'][i])
    cur = con.cursor()
    query = spec['queries'][i]
    if argrows:
        query_tpl = Template(query)
        query = query_tpl.render(argrows=argrows)
        if DEBUGGING:
            logger.info('\n\n' + query.strip() + '\n')
    cur.execute(query)

    if spec.get('cols') is None:
        spec['cols'] = [(i + 1, d[0].lower()) for i, d in enumerate(cur.description) if d[0].lower() not in spec['pk']]
        spec['pk'] = [(i + 1, d[0].lower()) for i, d in enumerate(cur.description) if d[0].lower() in spec['pk']]
        spec['insert'] = insert_tpl.render(c=spec, database=sources[DDIFF_SOURCE]['database'])
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
            [(run[0], spec_name, spec['sources'][i]) + row for row in res]
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
            ), f"Bad spec {spec_name}"

        if spec.get('cols') is None:
            logger.info(f"test {spec_name}; DB1 = {spec['sources'][0]}, DB2 = {spec['sources'][1]}")
            specs[spec_name]['warnings'] = []

        # Get 1st and 2nd query results and insert them into ddiff_ table.
        rowcount1 = pump(run, spec_name, spec, con0, argrows, 0)
        rowcount2 = pump(run, spec_name, spec, con0, argrows, 1)

        if MAX_FETCH_ROWS <= max(rowcount1, rowcount2):
            specs[spec_name]['warnings'].append(f"DB1: {rowcount1} rows, DB2: {rowcount2} rows.")

        # Get differences between 1st and 2nd query results.
        select = select_tpl.render(run=run, test=spec_name, c=spec, database=sources[DDIFF_SOURCE]['database'])
        if DEBUGGING:
            logger.info('\n\n' + select.strip() + '\n')
        cur0 = con0.cursor()
        cur0.execute(select)
        rows = cur0.fetchall()
        if rows:
            if spec.get(spec_name) and len(rows) <= MAX_DISCREPANCIES:
                # Delete intermediate query results from ddiff_ table.
                con0.rollback()
                if not spec[spec_name].get('sources'):
                    spec[spec_name]['sources'] = spec['sources']
                process(run, spec_name, spec[spec_name], con0, rows)
            else:
                if spec.get(spec_name) and len(rows) > MAX_DISCREPANCIES:
                    specs[spec_name]['warnings'].append(f"Found {len(rows)} discrepancies, go no deeper.")
                cols_index = len(spec['pk'])
                test_report = \
                    test_report_tpl.render(
                        cfg=CFG_NAME,
                        run=run,
                        test=spec_name,
                        #rows=rows,
                        rows=tuple(tuple(row[:cols_index]) + tuple(x for x in zip(row[cols_index::2], row[cols_index+1::2])) for row in rows),
                        titles=(x[0] for x in cur0.description),
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

        if DDIFF_KEEP:
            con0.commit()
        else:
            con0.rollback()
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

    con0 = connection(DDIFF_SOURCE)
    for spec_name, spec in specs.items():
        if SPEC in (spec_name, 'all'):
            process(run, spec_name, spec, con0, spec.get('argrows', ()))

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

    for src in sources.values():
        if src.get('con'):
            src['con'].close()
            src['con'] = None

    logger.info('-- done')


if __name__ == '__main__':
    main()
