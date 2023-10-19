#!/usr/bin/python3

import os
import sys
import argparse
import logging
from datetime import date, datetime

from jinja2 import Template


VERSION = '0.2'

parser = argparse.ArgumentParser(
    description="Run queries from cfg-file spec(s) against a DB, and generate data quality report.",
    epilog="Thanks for using %(prog)s!"
)

parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + VERSION)
parser.add_argument("cfg_file", help="cfg-file name")
parser.add_argument("spec", nargs="?", default="all", help="spec name, defaults to \"all\"")

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

# number of rows to fetch with one fetch
ONE_FETCH_ROWS = 5000

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
<title>Data Quality Report ({{cfg}}): {{test}}</title>
</head>
<body>
<h2><a href="{{cfg}}.html">Data Quality Report ({{cfg}})</a>: {{test}}</h2>
{%- if rows %}
{%- for row in rows %}
{%- if loop.first %}
<p>
{{run[1]}}. DB = "{{source}}". <span style="color:red;">Got {{rows|length}} fault rows. </span>
{% for warn in warnings %}{{warn}} {% endfor %}
</p>
<table>
<tr>{% for title in titles %}<th>{{title}}</th>{% endfor %}</tr>
{%- endif %}
<tr>{% for col in row %}<td>{{col if col is not none else '<NULL>'}}</td>{% endfor %}</tr>
{%- if loop.last %}
</table>
{%- endif %}
{%- endfor %}
{%- else %}
<p style="color:green;">Found 0 rows.</p>
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
<title>Data Quality Report ({{cfg}})</title>
</head>
<body>
<h2>Data Quality Report ({{cfg}})</h2>
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
<tr><th>Test</th><th>DB</th><th>Result</th><th>Warning</th></tr>
{%- endif %}
<tr>
    <td>{{row[0]}}</td>
    <td>{{row[3]}}</td>
    <td>{% if row[1] == 0 %}<span style="color:green;">Success.</span>{% elif row[1] == -1 %}Failed to run.{% else %}<a href="{{cfg}}_{{row[0]}}.html" style="color:red;">Got {{row[1]}} fault rows.</a>{% endif %}</td>
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
    if not sources[src].get('con'):
        if sources[src].get('con_string'):
            sources[src]['con'] = \
                sources[src]['lib'].connect(sources[src]['con_string'], **sources[src].get('con_kwargs', dict()))
        else:
            sources[src]['con'] = \
                sources[src]['lib'].connect(**sources[src]['con_kwargs'])
        if sources[src].get('setup'):
            if DEBUGGING:
                logger.info('-- setup')
            exec_sql(sources[src]['con'], sources[src].get('setup'))
        #if sources[src].get('init'):
        #    if isinstance(sources[src]['init'], str):
        #        sources[src]['init'] = [sources[src]['init']]
        #    cur = sources[src]['con'].cursor()
        #    for init in sources[src]['init']:
        #        cur.execute(init)
        #    cur.close()
    return sources[src]['con']


def process(run, spec_name, spec):
    try:
        assert (
            isinstance(spec, dict)
            and {*spec.keys()} >= {'source', 'query'}
            and isinstance(spec['source'], str)
            and isinstance(spec['query'], str)
            and sources.get(spec['source'])
            ), f"Bad spec {spec_name}"

        logger.info(f"test {spec_name}; DB = {spec['source']}")
        if DEBUGGING:
            logger.info('\n\n' + spec['query'].strip() + '\n')
        spec['warnings'] = []

        con = connection(spec['source'])
        cur = con.cursor()
        cur.execute(spec['query'])
        spec['cols'] = [d[0] for d in cur.description]
        rows = cur.fetchmany(ONE_FETCH_ROWS)
        cur.close()

        if ONE_FETCH_ROWS == len(rows):
            spec['warnings'].append(f"Got max number of rows.")

        if rows:
            test_report = \
                test_report_tpl.render(
                    cfg=CFG_NAME,
                    run=run,
                    test=spec_name,
                    rows=rows,
                    titles=spec.get('titles', spec['cols']),
                    warnings=spec.get('warnings'),
                    source=spec['source']
                )
            test_report_file = OUT_FILE.format(f"{CFG_NAME}_{spec_name}")
            with open(test_report_file, 'w', encoding="UTF-8") as f:
                f.write(test_report)

        logger.info(f"Got {len(rows)} fault rows.")
        spec['result'] = len(rows)

        con.rollback()
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

    for spec_name, spec in specs.items():
        if SPEC in (spec_name, 'all'):
            src = sources[spec['source']]
            if src.get('lib') is None:
                if src["database"] == "oracle":
                    import cx_Oracle
                    src["lib"] = cx_Oracle
                elif src["database"] == "postgres":
                    import psycopg2
                    from psycopg2 import extras
                    src["lib"] = psycopg2
                elif src["database"] == "mysql":
                    import mysql.connector
                    src["lib"] = mysql.connector
                elif src["database"] == "sqlite":
                    import sqlite3
                    src["lib"] = sqlite3
                else:
                    src["lib"] = None
            process(run, spec_name, spec)

    run_results = [
        (spec_name, spec.get('result', -1), spec.get('warnings'), spec['source'])
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
            if src.get('upset'):
                if DEBUGGING:
                    logger.info('-- upset')
                exec_sql(src['con'], src.get('upset'))
            src['con'].close()

    logger.info('-- done')


if __name__ == '__main__':
    main()
