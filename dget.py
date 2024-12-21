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

from openpyxl import Workbook, styles
from openpyxl.cell import WriteOnlyCell
from jinja2 import (
    #Template,
    Environment,
    FileSystemLoader,
    select_autoescape
)


VERSION = '0.3'

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

BASEDIR, BASENAME = os.path.split(sys.argv[0])

if not os.path.isfile(args.cfg_file) and not os.path.isfile(args.cfg_file + '.py'):
    sys.stderr.write(
        parser.format_usage() + \
        f"{BASENAME}: error: cfg-file not found: {args.cfg_file}\n"
    )
    sys.exit(1)

TEMPLATES_DIR = os.path.join(BASEDIR, 'conf')
if not os.path.isdir(TEMPLATES_DIR):
    TEMPLATES_DIR = os.path.join(BASEDIR, '..', 'conf')
    if not os.path.isdir(TEMPLATES_DIR):
        sys.stderr.write(
            parser.format_usage() + \
            f"{BASENAME}: error: templates dir not found: {TEMPLATES_DIR}\n"
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
    format="%(asctime)s:%(levelname)s:%(process)s:%(message)s",
    level=logging.DEBUG if DEBUGGING else logging.INFO if LOGGING else logging.CRITICAL + 1
)
logger = logging.getLogger(BASENAME.rsplit('.', 1)[0])

locale.setlocale(locale.LC_TIME, '')
# datetime format for strftime depends on locale by default
DATETIME_FORMAT = getattr(cfg, 'DATETIME_FORMAT', '%c')
DATE_FORMAT = getattr(cfg, 'DATE_FORMAT', '%x')
# output file encoding by default
ENCODING = getattr(cfg, 'ENCODING', locale.getpreferredencoding())
CSV_DIALECT = getattr(cfg, 'CSV_DIALECT', 'excel')
CSV_DELIMITER = getattr(cfg, 'CSV_DELIMITER', csv.get_dialect(CSV_DIALECT).delimiter)

# number of rows to fetch with one fetch
ONE_FETCH_ROWS = 5000
# number of gets preserved per entity
PRESERVE_N_TRACES = getattr(cfg, 'PRESERVE_N_TRACES', 10)

env = Environment(
    loader=FileSystemLoader([TEMPLATES_DIR, CFG_DIR]),
    autoescape=select_autoescape(['html', 'xml'])
)


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
    """"
    Get database connection by name src.
    """
    if isinstance(src, str):
        source = sources[src]
    elif isinstance(src, dict):
        source = src
    if not source.get('con'):
        if source.get('con_string'):
            source['con'] = \
                source['lib'].connect(source['con_string'], **source.get('con_kwargs', dict()))
        else:
            source['con'] = \
                source['lib'].connect(**source['con_kwargs'])
        if source.get('setup'):
            logger.debug('-- setup')
            exec_sql(source['con'], source.get('setup'))
    return source['con']


def csv_row(row, dec_sep='.'):
    return tuple(
        '' if f == None else \
        f.strftime(DATETIME_FORMAT) if isinstance(f, datetime) else \
        f.strftime(DATE_FORMAT) if isinstance(f, date) else \
        f if not isinstance(f, (float, dec.Decimal)) else \
        str(f).replace('.', dec_sep) \
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


def finalize_file(filename, file_format, compress=False):
    _filename = filename.rstrip('out') + file_format
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


def process(run, spec_name, spec, out_file):
    """
    Process spec from config-file.
    """
    return_code = 0
    con = None
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
            isinstance(spec['template'], str) and
            spec['template'].endswith(".jinja") and
            os.path.isfile(os.path.join(CFG_DIR, spec['template']))
            ), f"Bad format \"{in_format}\" or missing \"template\" in spec \"{spec_name}\""
        assert sources.get(spec['source']), \
            f"Source \"{spec['source']}\" not defined, spec \"{spec_name}\""
        assert 'query' in spec.keys() and isinstance(spec['query'], str), \
            f"Missing or bad \"query\" in spec \"{spec_name}\""
        assert args.arg is None or (
            isinstance(args.arg, list) 
            and isinstance(spec.get('bind_args'), dict) 
            and len(args.arg) == len(spec['bind_args'])
            ), f"Command line args and \"bind_args\" do not match, spec {spec_name}"

        logger.info("%s; DB = %s", spec_name, spec['source'])

        con = connection(spec['source'])

        # Optionally prepare for data retieval/set the context.
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
            template = env.get_template(spec.get(f"{out_format}.template", f"dget.{out_format}.jinja"))
            while True:
                first_row = cur.fetchone()
                if not first_row:
                    break
                else:
                    out_file = file_stem(out_base, filename_parts, seqn, args.user) + '.out'
                    seqn += 1
                    out_file = os.path.join(out_path, out_file)
                    file = open(out_file, 'w', encoding=encoding, errors='replace')
                    file.write(
                        template.render(
                            run=run,
                            title=spec.get(f"{out_format}.title", spec_name),
                            titles=spec['header'],
                            source=spec['source'],
                            dec_sep=spec.get(f"{out_format}.dec_separator", '.'),
                            rows=rows_from_cursor(cur, first_row, rows_per_file),
                            zip=zip
                        )
                    )
                    file.close()
                    finalize_file(out_file, out_format, out_compress)

        elif out_format == 'csv':
            #
            # create .csv file(s) line by line
            #
            dec_separator = spec.get('csv.dec_separator', '.')
            while True:
                rows = cur.fetchmany(ONE_FETCH_ROWS)
                if not rows:
                    break
                for row in rows:
                    # begin file
                    if file is None:
                        out_file = file_stem(out_base, filename_parts, seqn, args.user) + '.out'
                        seqn += 1
                        out_file = os.path.join(out_path, out_file)
                        file = open(out_file, 'w', encoding=encoding, errors='replace')
                        csv_writer = \
                            csv.writer(
                                file,
                                dialect=spec.get('csv.dialect', CSV_DIALECT),
                                delimiter=spec.get('csv.delimiter', CSV_DELIMITER),
                                lineterminator='\n'
                            )
                        csv_writer.writerow(spec['header'])
                    # next line
                    csv_writer.writerow(csv_row(row, dec_separator))
                    rowcount += 1
                    if rows_per_file and rowcount % rows_per_file == 0:
                        # end file
                        file.close()
                        file = None
                        finalize_file(out_file, out_format, out_compress)
            if file:
                # end file
                file.close()
                file = None
                finalize_file(out_file, out_format, out_compress)
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
                        out_file = file_stem(out_base, filename_parts, seqn, args.user) + '.out'
                        seqn += 1
                        out_file = os.path.join(out_path, out_file)
                        wb = Workbook(write_only=True)
                        ws = wb.create_sheet()
                        font = styles.Font(bold=True)
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
                        finalize_file(out_file, out_format, out_compress)
            if wb:
                # end file
                wb.save(out_file)
                wb.close()
                wb = None
                finalize_file(out_file, out_format, out_compress)
            logger.info("Got %s rows.", rowcount)

        cur.close()

        # Optionally confirm data retrieval.
        if spec.get('upset'):
            logger.debug('-- spec upset')
            exec_sql(con, spec['upset'])

        con.commit()
    except:
        logger.exception('EXCEPT')
        if con:
            con.rollback()
        return_code = 1
    return return_code


def main():
    logger.info("-- start %s", ' '.join(sys.argv))

    error_count = 0
    _temp = datetime.now()
    _ts = _temp.strftime('%Y%m%d%H%M%S')
    run = [
        int(_temp.strftime('%Y%m%d%H%M%S')),
        _temp.strftime('%Y-%m-%d %H:%M:%S'),
        _temp.strftime('%Y-%m-%d_%H-%M-%S')
    ]
    trace(_ts, 0)

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
            error_count += process(run, spec_name, spec, args.out_file)

    for src in sources.values():
        if src.get('con') is not None:
            if src.get('upset'):
                logger.debug("-- upset")
                exec_sql(src['con'], src.get('upset'))
            src['con'].close()
            src['con'] = None

    trace(_ts, 1 if error_count == 0 else 2)
    logger.info("-- done %s", f" WITH {error_count} ERRORS" if error_count else '')
    sys.exit(error_count)


if __name__ == '__main__':
    main()
