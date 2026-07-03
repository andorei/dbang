#!/usr/bin/env python3

import os
import sys
import locale
import re
import csv
import glob
import argparse
import logging
import decimal as dec
from datetime import date, datetime, time
import threading

from openpyxl import Workbook, styles
from openpyxl.cell import WriteOnlyCell
from jinja2 import (
    Template,
    Environment,
    FileSystemLoader,
    select_autoescape
)


VERSION = '0.4.0'

parser = argparse.ArgumentParser(
    description="Retrieve data from DB into file, as specified in cfg-file specs.",
    epilog="Thanks for using %(prog)s!"
)

parser.add_argument("-v", "--version", action="version", version="%(prog)s " + VERSION)
parser.add_argument("-a", "--arg", action="append", help="pass one or more arguments to SQL query")
parser.add_argument("-u", "--user", action="store", 
                    default=os.environ.get('USER', os.environ.get('USERNAME', 'DBANG')), 
                    help="set username")
parser.add_argument("-t", "--trace", action="store_true", help="enable tracing")
parser.add_argument("cfg_file", help="cfg-file name")
parser.add_argument("spec", nargs="?", default="all", help="spec name, defaults to \"all\"")
parser.add_argument("out_file", nargs="?", default=None, help="output file name")

args = parser.parse_args()

locale.setlocale(locale.LC_TIME, '')
BASEDIR, BASENAME = os.path.split(sys.argv[0])

if not os.path.isfile(args.cfg_file) and not os.path.isfile(args.cfg_file + '.py'):
    sys.stderr.write(
        parser.format_usage() + \
        f"{BASENAME}: error: cfg-file not found: {args.cfg_file}\n"
    )
    sys.exit(1)

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

TEMPLATES_DIR = CFG_DIR

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
LOG_FILE = os.path.join(LOG_DIR, f"{date.today().isoformat()}_{BASENAME.rsplit('.', 1)[0]}.log")
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
logger = logging.getLogger(__name__)

# output file encoding by default
ENCODING = getattr(cfg, 'ENCODING', locale.getpreferredencoding())
# datetime format for strftime is ISO 86101 by default
DATETIME_FORMAT = getattr(cfg, 'DATETIME_FORMAT', '%Y-%m-%d %H:%M:%S%z')
DATE_FORMAT = getattr(cfg, 'DATE_FORMAT', '%Y-%m-%d')

CSV_DIALECT = getattr(cfg, 'CSV_DIALECT', 'excel')
CSV_DELIMITER = getattr(cfg, 'CSV_DELIMITER', None) or csv.get_dialect(CSV_DIALECT).delimiter

# number of rows to fetch with one fetch
ONE_FETCH_ROWS = 5000
# number of gets preserved per entity
PRESERVE_N_TRACES = getattr(cfg, 'PRESERVE_N_TRACES', 10)

env = Environment(
    loader=FileSystemLoader([TEMPLATES_DIR, CFG_DIR]),
    autoescape=select_autoescape(['html', 'xml'])
)

JSON_TEMPLATE="""[
{%- for row in rows %}
{{"{"}}{% for k, v in zip(titles, row) %}"{{k}}": {% if v is not none %}{{v|tojson}}{% else %}null{% endif %}{% if not loop.last %}, {% endif %}{% endfor %}{{"}"}}{% if not loop.last %},{% endif %}
{%- endfor %}
]
"""
HTML_TEMPLATE="""<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="content-type" content="text/html; charset=UTF-8">
    <style type="text/css">
        th {{"{"}}background:lightblue; padding: 8px;{{"}"}}
        td {{"{"}}background:#e2e2e2; padding: 8px; text-align: left;{{"}"}}
    </style>
<title>{{title}}</title>
</head>
<body>
<h2>{{title}}</h2>
<p>{{run[1]}}</p>
<table>
{%- if titles %}
<tr>{% for t in titles %}<th>{{t}}</th>{% endfor %}</tr>
{%- endif %}
{%- for row in rows %}
<tr>{% for d in row %}<td{{' style="text-align:right;"' if d is number else ''}}>{% if d is none %}{% elif d is number %}{{d|replace('.', dec_sep)}}{% else %}{{d}}{% endif %}</td>{% endfor %}</tr>
{%- endfor %}
</table>
</body>
</html>
"""

json_tpl = Template(JSON_TEMPLATE)
html_tpl = Template(HTML_TEMPLATE)


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


def csv_row(row, dec_sep='.'):
    return tuple(
        '' if f == None else \
        f.strftime(DATETIME_FORMAT) if isinstance(f, datetime) else \
        f.strftime(DATE_FORMAT) if isinstance(f, date) else \
        str(f).replace('.', dec_sep) if isinstance(f, (float, complex, dec.Decimal)) else \
        str(f) \
        for f in row
        )


def jinja_row(row):
    return tuple(
        f.strftime(DATETIME_FORMAT) if isinstance(f, datetime) else \
        f.strftime(DATE_FORMAT) if isinstance(f, date) else \
        float(f) if isinstance(f, dec.Decimal) else \
        f
        for f in row
        )


def xlsx_row(row):
    # TypeError: Excel does not support timezones in datetimes. The tzinfo in the datetime/time object must be set to None.
    return tuple(
        f.replace(tzinfo=None) if isinstance(f, (time, datetime)) else \
        f
        for f in row
        )


def rows_from_cursor(cur, first_row=None, fetch_rows=0):
    rowcount = 0
    if first_row:
        yield jinja_row(first_row)
        rowcount += 1
        while True:
            how_many = \
                ONE_FETCH_ROWS if fetch_rows == 0 else \
                fetch_rows - 1 if fetch_rows <= ONE_FETCH_ROWS else \
                ONE_FETCH_ROWS if ONE_FETCH_ROWS <= (fetch_rows - 1 - rowcount) else \
                fetch_rows - 1 - ONE_FETCH_ROWS
            rows = cur.fetchmany(how_many)
            if not rows:
                break
            for row in rows:
                yield jinja_row(row)
                rowcount += 1
            if fetch_rows and rowcount == fetch_rows:
                break
    logger.info("Got %s rows.", rowcount)


def file_stem(stem, parts, seqn, user):
    filename_dict = dict()
    for part in parts:
        if part == 'date':
            filename_dict['date'] = date.today().isoformat()
        elif part == 'datetime':
            filename_dict['datetime'] = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        elif part == 'seqn':
            filename_dict['seqn'] = seqn
        elif part == 'user':
            filename_dict['user'] = user
    return stem % filename_dict


def finalize_file(filename, compress=False):
    _filename = filename[:-4]  # remove trailing '.out'
    if compress:
        import zipfile
        _zipfilename = _filename + '.zip'
        with zipfile.ZipFile(_zipfilename, 'w') as zf:
            zf.write(filename, arcname=os.path.basename(_filename))
        os.remove(filename)
    else:
        # os.rename: On Windows, if dst exists a FileExistsError is always raised.
        if os.path.isfile(_filename):
            os.remove(_filename)
        os.rename(filename, _filename)


def trace(ts, status):
    """
    Create or rename trace file to show current status.
    """
    if not args.trace:
        return

    safe_spec = re.sub(r'[^\w. \-()\[\]]', '_', args.spec).rstrip('. ').lstrip()
    safe_user = re.sub(r'[^\w. \-()\[\]]', '_', args.user).rstrip('. ').lstrip()
    this_trace = f"dget#{safe_spec}#{safe_user}#{ts}#"
    this_trace_glob = os.path.join(TEMP_DIR, this_trace + '?')
    this_trace_file = os.path.join(TEMP_DIR, this_trace + str(status))

    traces = glob.glob(this_trace_glob)
    assert len(traces) < 2, f"Too many traces {this_trace_glob}: {len(traces)}"

    if len(traces) == 0:
        with open(this_trace_file, 'w', encoding="UTF-8"):
            pass
        all_traces_glob = os.path.join(TEMP_DIR, f"dget#{safe_spec}#{safe_user}#??????????????#?")
        for i, trace_file in enumerate(sorted(glob.glob(all_traces_glob), reverse=True)):
            if i >= PRESERVE_N_TRACES:
                os.remove(trace_file)
    elif len(traces) == 1 and traces[0] != this_trace_file:
        os.rename(traces[0], this_trace_file)
    logger.debug("trace %s", this_trace + str(status))


def process_spec(con, run, spec_name, spec, out_file):
    """
    Process spec from config-file.
    """
    return_code = 0
    try:
        assert out_file or spec.get('file'), \
            f"Output file not specified, spec \"{spec_name}\""
        out_base, out_format = (out_file or spec.get('file')).rsplit('.', 1)
        if out_format == 'zip':
            out_compress = True
            out_base, out_format = out_base.rsplit('.', 1)
        else:
            out_compress = False
        assert out_format in ('html', 'csv', 'xlsx', 'json') or (
            #isinstance(spec['template'], str) and
            spec['template'].endswith(".jinja") and
            os.path.isfile(os.path.join(CFG_DIR, spec['template']))
            ), f"Bad format \"{out_format}\" or missing \"template\" in spec \"{spec_name}\""
        assert sources.get(spec['source']), \
            f"Source \"{spec['source']}\" not defined, spec \"{spec_name}\""
        assert 'query' in spec.keys() and isinstance(spec['query'], str), \
            f"Missing or bad \"query\" in spec \"{spec_name}\""
        assert args.arg is None or (
            isinstance(args.arg, list) 
            and isinstance(spec.get('bind_args'), dict) 
            and len(args.arg) == len(spec['bind_args'])
            ), f"Command line args and \"bind_args\" do not match, spec {spec_name}"

        logger.info(f"spec \"{spec_name}\"; source = \"{spec['source']}\"")

        # Initialize/Setup stuff related to this spec.
        if spec.get('setup'):
            logger.debug('-- spec setup')
            exec_sql(con, spec['setup'])

        # Retrieve data.
        cur = con.cursor()

        if isinstance(spec.get('header'), str):
            query = spec['header']
            logger.debug('\n\n%s\n', query.strip())
            cur.execute(query)
            # if query returns query execute it
            if len(cur.description) == 1 and cur.description[0][0] == 'query':
                query = cur.fetchone()[0]
                logger.debug('\n\n%s\n', query.strip())
                cur.execute(query)
            spec['header'] = cur.fetchone()

        query = spec['query']
        qargs = spec.get('bind_args', {})
        if args.arg:
            qargs = {k: v for k,v in zip(qargs.keys(), [type(v)(a) for v, a in zip(qargs.values(), args.arg)])}
        logger.debug('\n\n%s\n\n%s\n', query.strip(), str(qargs))
        cur.execute(query, qargs)
        # if query returns query execute it
        if len(cur.description) == 1 and cur.description[0][0] == 'query':
            query = cur.fetchone()[0]
            logger.debug('\n\n%s\n', query.strip())
            cur.execute(query)

        if not spec.get('header'):
            spec['header'] = [d[0] for d in cur.description]

        out_path = spec.get('out_dir', OUT_DIR)
        rows_per_file = spec.get('rows_per_file', 0)
        encoding = spec.get(f"{out_format}.encoding", ENCODING)

        filename_parts = re.findall(r'%\((.+?)\)', out_base)
        assert not filename_parts or \
            set(filename_parts) <= {'date', 'datetime', 'seqn', 'user'}, \
            f"Bad named fields in filename: {spec['file']}"

        file = None
        seqn = 0
        rowcount = 0
        if out_format in ('json', 'html'):
            #
            # create .json or .html file(s) using jinja2 template
            #
            template = spec.get(f"{out_format}.template", None)
            if template and os.path.isfile(os.path.join(TEMPLATES_DIR, template)):
                template = env.get_template(template)
            else:
                template = json_tpl if out_format == 'json' else html_tpl
            while True:
                first_row = cur.fetchone()
                if not first_row:
                    break
                else:
                    out_file = file_stem(out_base, filename_parts, seqn, args.user) + f".{out_format}.out"
                    seqn += 1
                    out_file = os.path.join(out_path, out_file)
                    file = open(out_file, 'w', encoding=encoding, errors='replace')
                    file.write(
                        template.render(
                            run=run,
                            title=spec.get(f"{out_format}.title", spec_name),
                            titles=spec['header'] if spec.get(f"csv.header", True) or out_format == 'json' else [],
                            source=spec['source'],
                            dec_sep=spec.get(f"{out_format}.dec_separator", '.'),
                            rows=rows_from_cursor(cur, first_row, rows_per_file),
                            zip=zip
                        )
                    )
                    file.close()
                    finalize_file(out_file, out_compress)

        elif out_format == 'csv':
            #
            # create .csv file(s) line by line
            #
            dec_separator = spec.get('csv.dec_separator', '.')
            csv_dialect = spec.get('csv.dialect', CSV_DIALECT)
            csv_delimiter = spec.get('csv.delimiter', CSV_DELIMITER)
            while True:
                rows = cur.fetchmany(ONE_FETCH_ROWS)
                if not rows:
                    break
                for row in rows:
                    # begin file
                    if file is None:
                        out_file = file_stem(out_base, filename_parts, seqn, args.user) + f".{out_format}.out"
                        seqn += 1
                        out_file = os.path.join(out_path, out_file)
                        file = open(out_file, 'w', encoding=encoding, errors='replace')
                        if csv_dialect == 'naive':
                            pass
                        else:
                            csv_writer = \
                                csv.writer(
                                    file,
                                    dialect=csv_dialect,
                                    delimiter=csv_delimiter,
                                    lineterminator='\n'
                                )
                        if spec.get('csv.header', True):
                            if csv_dialect == 'naive':
                                file.write(csv_delimiter.join(spec['header']) + '\n')
                            else:
                                csv_writer.writerow(spec['header'])
                    # next line
                    if csv_dialect == 'naive':
                        file.write(csv_delimiter.join(csv_row(row, dec_separator)) + '\n')
                    else:
                        csv_writer.writerow(csv_row(row, dec_separator))
                    rowcount += 1
                    if rows_per_file and rowcount % rows_per_file == 0:
                        # end file
                        file.close()
                        file = None
                        finalize_file(out_file, out_compress)
            if file:
                # end file
                file.close()
                file = None
                finalize_file(out_file, out_compress)
            logger.info("Got %s rows.", rowcount)

        elif out_format == 'xlsx':
            #
            # create .xlsx file(s) row by row
            #
            wb = None
            while True:
                rows = cur.fetchmany(ONE_FETCH_ROWS)
                if not rows:
                    break
                for row in rows:
                    # begin file
                    if wb is None:
                        out_file = file_stem(out_base, filename_parts, seqn, args.user) + f".{out_format}.out"
                        seqn += 1
                        out_file = os.path.join(out_path, out_file)
                        wb = Workbook(write_only=True)
                        ws = wb.create_sheet()
                        font = styles.Font(bold=True)
                        if spec.get('xlsx.header', True):
                            titles = [WriteOnlyCell(ws, value=title) for title in spec['header']]
                            for title in titles:
                                title.font = font
                            ws.append(titles)
                    # next row
                    ws.append(xlsx_row(row))
                    rowcount += 1
                    if rows_per_file and rowcount % rows_per_file == 0:
                        # end file
                        wb.save(out_file)
                        wb.close()
                        wb = None
                        finalize_file(out_file, out_compress)
            if wb:
                # end file
                wb.save(out_file)
                wb.close()
                wb = None
                finalize_file(out_file, out_compress)
            logger.info("Got %s rows.", rowcount)

        cur.close()

        # Finalize/Release stuff related to this spec.
        if spec.get('upset'):
            logger.debug('-- spec upset')
            exec_sql(con, spec['upset'])

        con.commit()
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
        run, spec_name, spec, out_file = arg_tuple

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
        error_count += process_spec(con, run, spec_name, spec, out_file)

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
    _ts = _temp.strftime('%Y%m%d%H%M%S')
    run = [
        int(_temp.strftime('%Y%m%d%H%M%S')),
        _temp.strftime('%Y-%m-%d %H:%M:%S'),
        _temp.strftime('%Y-%m-%d_%H-%M-%S')
    ]
    trace(_ts, 0)
    logger.info(f"run with {PARALLEL_WORKERS} thread(s)")

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
            todo.append((run, spec_name, spec, args.out_file))
            #error_count += process(run, spec_name, spec, args.out_file)

    # create and start worker threads
    threads = []
    for i in range(PARALLEL_WORKERS):
        threads.append(ReturnValueThread(target=worker, args=(todo[i::PARALLEL_WORKERS],)))
        threads[-1].start()
    # wait for all worker threads to terminate
    for thread in threads:
        error_count += thread.join()

    trace(_ts, 1 if error_count == 0 else 2)
    logger.debug(f"{datetime.now() - _temp}")
    logger.info("-- done %s", f" WITH {error_count} ERRORS" if error_count else '')

    sys.exit(error_count)


if __name__ == '__main__':
    main()
