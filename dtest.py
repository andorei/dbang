#!/usr/bin/env python3

import os
import sys
import argparse
import logging
from datetime import date, datetime
import re

from jinja2 import Template


VERSION = '0.3'

parser = argparse.ArgumentParser(
    description="Run queries from cfg-file spec(s) against a DB, and generate data quality report.",
    epilog="Thanks for using %(prog)s!"
)

parser.add_argument("-v", "--version", action="version", version="%(prog)s " + VERSION)
parser.add_argument("cfg_file", help="cfg-file name")
parser.add_argument("spec", nargs="?", default="all", help="spec name, defaults to \"all\"")

args = parser.parse_args()

BASENAME = os.path.basename(sys.argv[0])
if not os.path.isfile(args.cfg_file) and not os.path.isfile(args.cfg_file + '.py'):
    sys.stderr.write(
        parser.format_usage() + \
        f"{BASENAME}: error: cfg-file not found: {args.cfg_file}\n"
    )
    sys.exit(1)

#USER_DIR = os.environ.get('HOMEPATH', os.environ.get('HOME', ''))
USER_DIR = os.path.expanduser('~')
if not os.path.isdir(USER_DIR):
    sys.stderr.write(
        parser.format_usage() + \
        f"{BASENAME}: error: user's home dir not found: {USER_DIR}\n"
    )
    sys.exit(1)
TEMP_DIR = os.path.join(USER_DIR, '.dbang')
if not os.path.isdir(TEMP_DIR):
    os.mkdir(TEMP_DIR)

CUR_DIR = os.getcwd()
CFG_DIR = os.path.abspath(os.path.dirname(args.cfg_file) or CUR_DIR)
CFG_MODULE = os.path.basename(args.cfg_file).rsplit('.', 1)[0]
sys.path.append(CFG_DIR)
cfg = __import__(CFG_MODULE)
sources = cfg.sources
specs = cfg.specs

SPEC = args.spec
# filter out specs commented out with leading --
specs = {k:v for k,v in specs.items() if not k.startswith('--')}
if SPEC not in [*specs.keys(), 'all', *(tag for val in specs.values() if val.get('tags') for tag in val['tags'])]:
    sys.stderr.write(
        parser.format_usage() + \
        f"{BASENAME}: error: spec not found in cfg-file: {SPEC}\n"
    )
    sys.exit(1)

OUT_DIR = getattr(cfg, 'OUT_DIR', CUR_DIR)
if not os.path.isdir(OUT_DIR):
    sys.stderr.write(
        parser.format_usage() + \
        f"{BASENAME}: error: out dir not found: {OUT_DIR}\n"
    )
    sys.exit(1)
OUT_FILE = os.path.join(OUT_DIR, '{}.html')

DEBUGGING = getattr(cfg, 'DEBUGGING', False)
LOGGING = getattr(cfg, 'LOGGING', DEBUGGING)
LOG_DIR = getattr(cfg, 'LOG_DIR', CUR_DIR)
if LOGGING and not os.path.isdir(LOG_DIR):
    sys.stderr.write(
        parser.format_usage() + \
        f"{BASENAME}: error: log dir not found: {LOG_DIR}\n"
    )
    sys.exit(1)
LOG_FILE = os.path.join(LOG_DIR, f"{date.today().isoformat()}_{BASENAME.rsplit('.', 1)[0]}.log")
logging.basicConfig(
    filename=LOG_FILE,
    #encoding='utf-8', # encoding needs Python >=3.9
    format="%(asctime)s:%(levelname)s:%(name)s:%(message)s",
    level=logging.DEBUG if DEBUGGING else logging.INFO if LOGGING else logging.CRITICAL + 1
)
logger = logging.getLogger(BASENAME.rsplit('.', 1)[0])

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
{%- if doc %}
<p>{{doc}}</p>
{%- endif %}
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
<tr><th>Test</th><th>DB</th><th>Result</th><th>Warning</th><th>Doc</th></tr>
{%- endif %}
<tr>
    <td>{{row[0]}}</td>
    <td>{{row[3]}}</td>
    <td>{% if row[1] == 0 %}<span style="color:green;">Success.</span>{% elif row[1] == -1 %}Failed to run.{% else %}<a href="{{cfg}}_{{row[0]}}.html" style="color:red;">Got {{row[1]}} fault rows.</a>{% endif %}</td>
    <td>{% if row[2] %}{% for warn in row[2] %}{{warn}}{{"<br/>" if not loop.last}}{% endfor %}{% endif %}</td>
    <td>{% if row[4] %}{{row[4]|escape}}{% endif %}</td>
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

test_report_tpl = Template(TEST_REPORT)
run_report_tpl = Template(RUN_REPORT)


def exec_sql(con, sql):
    """
    Execute sql statement(s) using connection con.
    """
    if sql:
        cur = con.cursor()
        if isinstance(sql, str):
            logger.debug('\n\n%s\n', sql.strip())
            cur.execute(sql)
        elif isinstance(sql, (list, tuple)):
            for stmt in sql:
                assert isinstance(stmt, str), f"Expected SQL statement: {stmt}"
                logger.debug('\n\n%s\n', stmt.strip())
                cur.execute(stmt)
        else:
            assert False, f"Expected SQL statement: {sql}"
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
            logger.debug('-- setup')
            exec_sql(sources[src]['con'], sources[src].get('setup'))
    return sources[src]['con']


def process(run, spec_name, spec):
    """
    Process spec from config-file.
    """
    return_code = 0
    try:
        assert (
            isinstance(spec, dict)
            and {*spec.keys()} >= {'source', 'query'}
            and isinstance(spec['source'], str)
            and isinstance(spec['query'], str)
            and sources.get(spec['source'])
            ), f"Bad spec {spec_name}"

        logger.info("test %s; DB = %s", spec_name, spec['source'])
        logger.debug('\n\n%s\n', spec['query'].strip())
        spec['warnings'] = []
        spec['safe_name'] = re.sub(r'[^\w. \-()\[\]]', '_', spec_name).rstrip('. ').lstrip()

        con = connection(spec['source'])
        cur = con.cursor()
        cur.execute(spec['query'])
        spec['cols'] = [d[0] for d in cur.description]
        rows = cur.fetchmany(ONE_FETCH_ROWS)
        cur.close()

        if ONE_FETCH_ROWS == len(rows):
            spec['warnings'].append("Got max number of rows.")

        if rows:
            test_report = \
                test_report_tpl.render(
                    cfg=CFG_MODULE,
                    run=run,
                    test=spec_name,
                    doc=spec.get('doc'),
                    rows=rows,
                    titles=spec.get('titles', spec['cols']),
                    warnings=spec.get('warnings'),
                    source=spec['source']
                )
            test_report_file = OUT_FILE.format(f"{CFG_MODULE}_{spec['safe_name']}")
            with open(test_report_file, 'w', encoding="UTF-8") as f:
                f.write(test_report)

        logger.info("Got %s fault rows.", len(rows))
        spec['result'] = len(rows)

        con.rollback()
    except:
        logger.exception('EXCEPT')
        for src in sources.values():
            if src.get('con'):
                src['con'].rollback()
        return_code = 1
    return return_code


def main():
    logger.info("-- start %s", ' '.join(sys.argv))

    error_count = 0
    _temp = datetime.now()
    run = [
        int(_temp.strftime('%Y%m%d%H%M%S')),
        _temp.strftime('%Y-%m-%d %H:%M:%S'),
        _temp.strftime('%Y-%m-%d_%H-%M-%S')
    ]
    logger.info("run %s", run[0])

    for spec_name, spec in specs.items():
        if SPEC in (spec_name, 'all', *spec.get('tags', [])):
            spec['source'] = spec.get('source', getattr(cfg, 'SOURCE', None))
            if spec['source'] is None:
                logger.error('Skipping spec "%s" with no source', spec_name)
                error_count += 1
                continue
            src = sources[spec['source']]
            if src.get('lib') is None:
                if src['database'] == 'oracle':
                    #import cx_Oracle
                    #src['lib'] = cx_Oracle
                    import oracledb
                    src['lib'] = oracledb
                    if src.get('oracledb_thick_mode'):
                        src['lib'].init_oracle_client()
                elif src['database'] == 'postgres':
                    import psycopg
                    src['lib'] = psycopg
                elif src['database'] == 'mysql':
                    import mysql.connector
                    src['lib'] = mysql.connector
                elif src['database'] == 'sqlite':
                    import sqlite3
                    src['lib'] = sqlite3
                else:
                    src['lib'] = None
            error_count += process(run, spec_name, spec)

    run_results = [
        (spec['safe_name'], spec.get('result', -1), spec.get('warnings'), spec['source'], spec.get('doc'))
        for spec_name, spec in specs.items() if SPEC in (spec_name, 'all', *spec.get('tags', []))
    ]
    succeeded = len([1 for x in run_results if x[1] == 0])
    failed = len([1 for x in run_results if x[1] > 0])
    not_run = len([1 for x in run_results if x[1] == -1])
    run_report = \
        run_report_tpl.render(
            cfg=CFG_MODULE,
            run=run,
            rows=run_results,
            succeeded=succeeded,
            failed=failed,
            not_run=not_run
        )
    run_report_file = OUT_FILE.format(f"{CFG_MODULE}")
    with open(run_report_file, 'w', encoding='UTF-8') as f:
        f.write(run_report)

    for src in sources.values():
        if src.get('con') is not None:
            if src.get('upset'):
                logger.debug("-- upset")
                exec_sql(src['con'], src.get('upset'))
            src['con'].close()
            src['con'] = None

    logger.info("-- done %s", f" WITH {error_count} ERRORS" if error_count else '')
    sys.exit(error_count)


if __name__ == '__main__':
    main()
