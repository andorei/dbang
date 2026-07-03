#!/usr/bin/env python3

import os
import sys
import argparse
import logging
import re
from datetime import date, datetime
#import concurrent.futures
import threading

from jinja2 import (
    Template,
    Environment,
    FileSystemLoader,
    select_autoescape
)


VERSION = '0.4.0'

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
BASEBASE = BASENAME.rsplit('.', 1)[0]

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

PARALLEL_WORKERS = min(getattr(cfg, 'PARALLEL_WORKERS', 1), 8)

DEBUGGING = getattr(cfg, 'DEBUGGING', False)
LOGGING = getattr(cfg, 'LOGGING', DEBUGGING)
LOG_DIR = getattr(cfg, 'LOG_DIR', CUR_DIR)
if LOGGING and not os.path.isdir(LOG_DIR):
    sys.stderr.write(
        parser.format_usage() + \
        f"{BASENAME}: error: log dir not found: {LOG_DIR}\n"
    )
    sys.exit(1)
LOG_FILE = os.path.join(LOG_DIR, f"{date.today().isoformat()}_{BASEBASE}.log")
if sys.version_info >= (3, 9):
    logging.basicConfig(
        filename=LOG_FILE,
        encoding='utf-8',
        format="%(asctime)s:%(levelname)s:%(process)s:" + ("%(thread)d:%(message)s" if PARALLEL_WORKERS > 1 else "%(message)s"),
        level=logging.DEBUG if DEBUGGING else logging.INFO if LOGGING else logging.CRITICAL + 1
    )
else:
    logging.basicConfig(
        filename=LOG_FILE,
        format="%(asctime)s:%(levelname)s:%(process)s:" + ("%(thread)d:%(message)s" if PARALLEL_WORKERS > 1 else "%(message)s"),
        level=logging.DEBUG if DEBUGGING else logging.INFO if LOGGING else logging.CRITICAL + 1
    )
logger = logging.getLogger(BASEBASE)

# datetime format for strftime is ISO 86101 by default
DATETIME_FORMAT = getattr(cfg, 'DATETIME_FORMAT', '%Y-%m-%d %H:%M:%S%z')
DATE_FORMAT = getattr(cfg, 'DATE_FORMAT', '%Y-%m-%d')

# number of rows to fetch with one fetch
ONE_FETCH_ROWS = 5000

SPEC_REPORT_TEMPLATE="""
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="content-type" content="text/html; charset=UTF-8">
    <style type="text/css">
        th {background:lightblue; padding: 5px;}
        td {background:#e2e2e2; padding: 5px; text-align: left;}
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
RUN_REPORT_TEMPLATE="""
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="content-type" content="text/html; charset=UTF-8">
    <style type="text/css">
        th {background:lightblue; padding: 5px;}
        td {background:#e2e2e2; padding: 5px; text-align: left;}
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

env = Environment(
    loader=FileSystemLoader([CFG_DIR]),
    autoescape=select_autoescape(['html', 'xml'])
)

spec_report_tpl = getattr(cfg, 'SPEC_REPORT_TEMPLATE', None)
if spec_report_tpl and os.path.isfile(os.path.join(CFG_DIR, spec_report_tpl)):
    spec_report_tpl = env.get_template(spec_report_tpl)
else:
    spec_report_tpl = Template(SPEC_REPORT_TEMPLATE)

run_report_tpl = getattr(cfg, 'RUN_REPORT_TEMPLATE', None)
if run_report_tpl and os.path.isfile(os.path.join(CFG_DIR, run_report_tpl)):
    run_report_tpl = env.get_template(run_report_tpl)
else:
    run_report_tpl = Template(RUN_REPORT_TEMPLATE)


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


def process_spec(con, run, spec_name, spec):
    """
    Process spec from config-file.
    """
    return_code = 0
    try:
        assert (
            isinstance(spec, dict)
            and {*spec.keys()} >= {'source', 'query'}
            #and isinstance(spec['source'], str)
            and isinstance(spec['query'], str)
            and sources.get(spec['source'])
            ), f"Bad spec {spec_name}"

        logger.info(f"spec \"{spec_name}\"; source = \"{spec['source']}\"")
        spec['warnings'] = []
        spec['safe_name'] = re.sub(r'[^\w. \-()\[\]]', '_', spec_name).rstrip('. ').lstrip()

        # Initialize/Setup stuff related to this spec.
        if spec.get('setup'):
            logger.debug('-- spec setup')
            exec_sql(con, spec['setup'])

        logger.debug('\n\n%s\n', spec['query'].strip())
        cur = con.cursor()
        cur.execute(spec['query'])
        spec['cols'] = [d[0] for d in cur.description]
        rows = cur.fetchmany(ONE_FETCH_ROWS)
        cur.close()

        if ONE_FETCH_ROWS == len(rows):
            spec['warnings'].append("Got max number of rows.")

        if rows:
            spec_report = \
                spec_report_tpl.render(
                    cfg=CFG_MODULE,
                    run=run,
                    test=spec_name,
                    doc=spec.get('doc'),
                    rows=rows,
                    titles=spec.get('header', spec['cols']),
                    warnings=spec.get('warnings'),
                    source=spec['source']
                )
            spec_report_file = OUT_FILE.format(f"{CFG_MODULE}_{spec['safe_name']}")
            with open(spec_report_file, 'w', encoding="UTF-8") as f:
                f.write(spec_report)

        logger.info("Got %s fault rows.", len(rows))
        spec['result'] = len(rows)

        # Finalize/Release stuff related to this spec.
        if spec.get('upset'):
            logger.debug('-- spec upset')
            exec_sql(con, spec['upset'])

        con.rollback()
    except:
        logger.exception('EXCEPT')
        con.rollback()
        return_code = 1
    return return_code


class ReturnValueThread(threading.Thread):
    """
    Class where join() returns value returned by target function
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.result = 0

    def run(self):
        if self._target is not None:
            self.result = self._target(*self._args, **self._kwargs)

    def join(self, *args, **kwargs):
        super().join(*args, **kwargs)
        return self.result


def worker(list_of_arg_tuples):
    error_count = 0
    connections = dict()

    for arg_tuple in list_of_arg_tuples:
        run, spec_name, spec = arg_tuple

        # get worker connection for the spec
        source_name = spec['source']
        if not connections.get(source_name):
            source = sources[source_name]
            connections[source_name] = \
                source['lib'].connect(source['con_string'], **source.get('con_kwargs', dict())) \
                if source.get('con_string') else \
                source['lib'].connect(**source['con_kwargs'])
            if source.get('setup'):
                logger.debug('-- setup')
                exec_sql(connections[source_name], source['setup'])
        con = connections[source_name]

        # execute the spec
        error_count += process_spec(con, run, spec_name, spec)

    # shutdown all worker connections
    for source_name, con in connections.items():
        source = sources[source_name]
        if source.get('upset'):
            logger.debug('-- upset')
            exec_sql(con, source['upset'])
        con.close()

    return error_count


def main():
    logger.info("-- start %s", ' '.join(sys.argv))

    _temp = datetime.now()
    run = [
        int(_temp.strftime('%Y%m%d%H%M%S')),
        _temp.strftime(DATETIME_FORMAT),
        _temp.strftime('%Y-%m-%d_%H-%M-%S')
    ]
    logger.info(f"run {run[0]} with {PARALLEL_WORKERS} thread(s)")

    error_count = 0
    todo = []
    for spec_name, spec in specs.items():
        if SPEC in (spec_name, 'all', *spec.get('tags', [])):
            spec['source'] = spec.get('source', getattr(cfg, 'SOURCE', None))
            if spec['source'] not in sources:
                logger.error('Skipping spec "%s" with unknown source', spec_name)
                error_count += 1
                continue
            src = sources[spec['source']]
            if src.get('lib') is None:
                if src['database'] == 'mssql':
                    import mssql_python
                    src['lib'] = mssql_python
                elif src['database'] == 'mysql':
                    import mysql.connector
                    src['lib'] = mysql.connector
                elif src['database'] == 'oracle':
                    #import cx_Oracle
                    #src['lib'] = cx_Oracle
                    import oracledb
                    src['lib'] = oracledb
                    if src.get('oracledb_thick_mode'):
                        src['lib'].init_oracle_client()
                elif src['database'] == 'postgresql':
                    import psycopg
                    src['lib'] = psycopg
                elif src['database'] == 'sqlite':
                    import sqlite3
                    src['lib'] = sqlite3
                else:
                    src['lib'] = None
            todo.append((run, spec_name, spec))
            #error_count += process_spec(run, spec_name, spec)

    # create and start worker threads
    threads = []
    for i in range(PARALLEL_WORKERS):
        threads.append(ReturnValueThread(target=worker, args=(todo[i::PARALLEL_WORKERS],)))
        threads[-1].start()
    # wait for all worker threads to terminate
    for thread in threads:
        error_count += thread.join()

    # create run report
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

    logger.debug(f"{datetime.now() - _temp}")
    logger.info("-- done %s", f" WITH {error_count} ERRORS" if error_count else '')
    sys.exit(error_count)


if __name__ == '__main__':
    main()
