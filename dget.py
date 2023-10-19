#!/usr/bin/python3

import os
import sys
import csv
import argparse
import logging
import decimal as dec
from datetime import date, datetime

from openpyxl import Workbook, styles
from openpyxl.cell import WriteOnlyCell
from jinja2 import Template, Environment, FileSystemLoader, select_autoescape


VERSION = '0.2'

parser = argparse.ArgumentParser(
    description="Retrieve data from DB into file, as specified in cfg-file specs.",
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
DEBUGGING = getattr(cfg, 'DEBUGGING', False)
LOGSTDOUT = getattr(cfg, 'LOGSTDOUT', False)

# number of rows to fetch with one fetch
ONE_FETCH_ROWS = 5000

logging.basicConfig(
    filename=None if LOGSTDOUT else LOG_FILE,
    format='%(asctime)s:%(levelname)s:%(name)s:%(message)s',
    level=logging.INFO
)
logger = logging.getLogger(BASENAME)

env = Environment(
    loader=FileSystemLoader(CFG_DIR),
    autoescape=select_autoescape(['html', 'xml'])
)


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
    return sources[src]['con']


def rows_from_cursor(cur, first_row=None):
    rowcount = 0
    if first_row:
        yield first_row
        rowcount += 1
    while True:
        rows = cur.fetchmany(ONE_FETCH_ROWS)
        if not rows:
            break
        for row in rows:
            yield row
            rowcount += 1
    logger.info(f"Got {rowcount} rows.")


def process(run, spec_name, spec):
    try:
        out_base, out_format = spec_name.rsplit('.', 1)
        assert (
            isinstance(spec, dict)
            and (
                out_format in ('html', 'csv', 'xlsx', 'json')
                or (
                    isinstance(spec['template'], str)
                    and spec['template'].endswith(".jinja")
                    and os.path.isfile(os.path.join(CFG_DIR, spec['template']))
                )
            )
            and {*spec.keys()} >= {'source', 'query'}
            and isinstance(spec['source'], str)
            and isinstance(spec['query'], str)
            and sources.get(spec['source'])
            ), f"Bad spec {spec_name}"

        logger.info(f"{spec_name}; DB = {spec['source']}")

        con = connection(spec['source'])
        cur = con.cursor()

        if isinstance(spec.get('titles'), str):
            query = spec['titles']
            if DEBUGGING:
                logger.info('\n\n' + query.strip() + '\n')
            cur.execute(query)
            # if query returns query execute it
            if len(cur.description) == 1 and cur.description[0][0] == 'query':
                query = cur.fetchone()[0]
                if DEBUGGING:
                    logger.info('\n\n' + query.strip() + '\n')
                cur.execute(query)
            spec['titles'] = cur.fetchone()

        query = spec['query']
        if DEBUGGING:
            logger.info('\n\n' + query.strip() + '\n')
        cur.execute(query)
        # if query returns query execute it
        if len(cur.description) == 1 and cur.description[0][0] == 'query':
            query = cur.fetchone()[0]
            if DEBUGGING:
                logger.info('\n\n' + query.strip() + '\n')
            cur.execute(query)

        if not spec.get('titles'):
            spec['titles'] = [d[0] for d in cur.description]

        dec_sep = spec.get('dec_separator', '.')
        out_path = spec.get('out_dir', OUT_DIR)

        file = None
        rowcount = 0
        if out_format in ('json', 'html'):
            #
            # create .json or .html file using one-piece jinja2 template file
            #
            first_row = cur.fetchone()
            if first_row:
                template = env.get_template(spec.get('template') or f'dget.{out_format}.jinja')
                out_file = os.path.join(out_path, f"{out_base}.out")
                file = open(out_file, "w", encoding=spec.get("encoding", cfg.ENCODING), errors='replace')
                file.write(
                    template.render(
                        run=run,
                        title=spec.get('title', out_base),
                        titles=spec['titles'],
                        rows=rows_from_cursor(cur, first_row),
                        zip=zip
                    )
                )
                file.close()
                _out_file = out_file.rstrip('out') + out_format
                # os.rename: On Windows, if dst exists a FileExistsError is always raised.
                if os.path.isfile(_out_file):
                    os.remove(_out_file)
                os.rename(out_file, _out_file)

        #elif out_format == 'json':
        #    #
        #    # create .json file using BEGIN, NEXT, END jinja2 templates from config-file
        #    #
        #    while True:
        #        rows = cur.fetchmany(ONE_FETCH_ROWS)
        #        if not rows:
        #            break
        #        rowcount += len(rows)
        #        # begin
        #        if file is None:
        #            out_file = os.path.join(out_path, f"{out_base}.out")
        #            file = open(out_file, "w", encoding=spec.get("encoding", cfg.ENCODING), errors='replace')
        #            template = Template(spec.get("json_begin", cfg.JSON_BEGIN))
        #            file.write(template.render(run=run, title=spec.get('title', out_base), titles=spec['titles']))
        #            template = Template(spec.get("json_next", cfg.JSON_NEXT))
        #        # next
        #        file.write(template.render(titles=spec['titles'], rows=rows, zip=zip))
        #    logger.info(f"Got {rowcount} rows.")
        #    # end
        #    file.write(spec.get("json_end", cfg.JSON_END))
        #
        #    file.close()
        #    _out_file = out_file.rstrip('out') + out_format
        #    # os.rename: On Windows, if dst exists a FileExistsError is always raised.
        #    if os.path.isfile(_out_file):
        #        os.remove(_out_file)
        #    os.rename(out_file, _out_file)
        #
        #elif out_format == 'html':
        #    #
        #    # create .html file using BEGIN, NEXT, END jinja2 templates from config-file
        #    #
        #    while True:
        #        rows = cur.fetchmany(ONE_FETCH_ROWS)
        #        if not rows:
        #            break
        #        rowcount += len(rows)
        #        # begin
        #        if file is None:
        #            out_file = os.path.join(out_path, f"{out_base}.out")
        #            file = open(out_file, "w", encoding=spec.get("encoding", cfg.ENCODING), errors='replace')
        #            template = Template(spec.get('html_begin', cfg.HTML_BEGIN))
        #            file.write(template.render(run=run, title=spec.get('title', out_base), titles=spec['titles']))
        #            template = Template(spec.get('html_next', cfg.HTML_NEXT))
        #        # next
        #        prepared_rows = (
        #            (
        #                ('', '0') if f == None else \
        #                (f.strftime(cfg.PY_DATE_FORMAT), 'd') if isinstance(f, date) else \
        #                (f.strftime(cfg.PY_DATETIME_FORMAT), 'd') if isinstance(f, datetime) else \
        #                (str(f), 's') if not isinstance(f, (int, float, dec.Decimal)) else \
        #                (str(f).replace('.', dec_sep), 'n') \
        #                for f in row
        #            ) for row in rows
        #        )
        #        file.write(template.render(rows=prepared_rows))
        #    logger.info(f"Got {rowcount} rows.")
        #    # end
        #    file.write(spec.get("html_end", cfg.HTML_END))
        #
        #    file.close()
        #    _out_file = out_file.rstrip('out') + out_format
        #    # os.rename: On Windows, if dst exists a FileExistsError is always raised.
        #    if os.path.isfile(_out_file):
        #        os.remove(_out_file)
        #    os.rename(out_file, _out_file)

        elif out_format == 'csv':
            #
            # create .csv file line by line
            #
            while True:
                rows = cur.fetchmany(ONE_FETCH_ROWS)
                if not rows:
                    break
                rowcount += len(rows)
                # begin
                if file is None:
                    out_file = os.path.join(out_path, f"{out_base}.out")
                    file = open(out_file, "w", encoding=spec.get("encoding", cfg.ENCODING), errors='replace')
                    csv_writer = \
                        csv.writer(
                            file,
                            dialect=spec.get('dialect', cfg.CSV_DIALECT),
                            delimiter=spec.get('delimiter', cfg.CSV_DELIMITER),
                            lineterminator='\n'
                        )
                    csv_writer.writerow(spec['titles'])
                # next
                for row in rows:
                    csv_writer.writerow(
                        '' if f == None else \
                        f.strftime(cfg.PY_DATE_FORMAT) if isinstance(f, date) else \
                        f.strftime(cfg.PY_DATETIME_FORMAT) if isinstance(f, datetime) else \
                        f if not isinstance(f, (float, dec.Decimal)) or dec_sep == '.' else \
                        str(f).replace('.', dec_sep) \
                        for f in row
                    )
            logger.info(f"Got {rowcount} rows.")
            # end
            pass

            file.close()
            _out_file = out_file.rstrip('out') + out_format
            # os.rename: On Windows, if dst exists a FileExistsError is always raised.
            if os.path.isfile(_out_file):
                os.remove(_out_file)
            os.rename(out_file, _out_file)

        elif out_format == 'xlsx':
            #
            # create .xlsx file row by row
            #
            wb = None
            while True:
                rows = cur.fetchmany(ONE_FETCH_ROWS)
                if not rows:
                    break
                rowcount += len(rows)
                # begin
                if wb is None:
                    out_file = os.path.join(out_path, f"{out_base}.out")
                    wb = Workbook(write_only=True)
                    ws = wb.create_sheet()
                    font = styles.Font(bold=True)
                    titles = [WriteOnlyCell(ws, value=title) for title in spec['titles']]
                    for title in titles:
                        title.font = font
                    ws.append(titles)
                # next
                for row in rows:
                    ws.append(
                        '' if f == None else \
                        f.strftime(cfg.PY_DATE_FORMAT) if isinstance(f, date) else \
                        f.strftime(cfg.PY_DATETIME_FORMAT) if isinstance(f, datetime) else \
                        f if not isinstance(f, (float, dec.Decimal)) or dec_sep == '.' else \
                        str(f).replace('.', dec_sep) \
                        for f in row
                    )
            logger.info(f"Got {rowcount} rows.")
            # end
            wb.save(out_file)

            wb.close()
            _out_file = out_file.rstrip('out') + out_format
            # os.rename: On Windows, if dst exists a FileExistsError is always raised.
            if os.path.isfile(_out_file):
                os.remove(_out_file)
            os.rename(out_file, _out_file)

        cur.close()
        con.rollback()

    except:
        logger.exception('EXCEPT')
        if con:
            con.rollback()


def main():
    logger.info(f'-- start {" ".join(sys.argv)}')

    _temp = datetime.now()
    run = [
        int(_temp.strftime('%Y%m%d%H%M%S')),
        _temp.strftime('%Y-%m-%d %H:%M:%S'),
        _temp.strftime('%Y-%m-%d_%H-%M-%S')
    ]

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

    for src in sources.values():
        if src.get('con') is not None:
            if src.get('upset'):
                if DEBUGGING:
                    logger.info('-- upset')
                exec_sql(src['con'], src.get('upset'))
            src['con'].close()

    logger.info('-- done')


if __name__ == '__main__':
    main()
