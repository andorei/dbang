#!/usr/bin/python3

import os
import sys
import csv
import json
import argparse
import logging
from datetime import date, datetime

from openpyxl import load_workbook


VERSION = '0.2'

parser = argparse.ArgumentParser(
    description="Load data from file into DB, as specified in cfg-file spec.",
    epilog="Thanks for using %(prog)s!"
)

parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + VERSION)
parser.add_argument("cfg_file", help="cfg-file name")
parser.add_argument("spec", help="spec name")
parser.add_argument("in_file", nargs="?", default=None, help="input file name")

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
#LOG_FILE = IN_FILE + '.log'
USER_ID = BASENAME
IN_DIR = getattr(cfg, 'IN_DIR', os.path.join(SCRIPT_DIR, 'in'))
DEBUGGING = getattr(cfg, 'DEBUGGING', False)
LOGSTDOUT = getattr(cfg, 'LOGSTDOUT', False)

logging.basicConfig(
    filename=None if LOGSTDOUT else LOG_FILE,
    format='%(asctime)s:%(levelname)s:%(name)s:%(message)s',
    level=logging.INFO
)
logger = logging.getLogger(BASENAME)


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


def process(spec_name, spec, input_file):
    in_file = input_file or spec['file']
    if not os.path.isfile(in_file):
        in_file = os.path.join(IN_DIR, in_file)
        assert os.path.isfile(in_file), f"Input file not found: {input_file}"

    source = sources[spec['source']]

    filename = os.path.basename(in_file)
    in_base, in_format = filename.split('.')

    con = None
    cur = None
    file = None
    wb = None
    try:
        assert (
            in_format in ('csv', 'xlsx', 'json')
            and (in_format != 'json' or spec.get('insert_values'))
            and (spec.get('insert_statement') is None or spec.get('insert_values'))
            ), f"Bad file ext: {in_format}"

        con = connection(spec['source'])
        cur = con.cursor()

        # 1) load data file into database
        logger.info(f'Loading {spec_name}, {in_file}')

        iload = None
        if in_format == 'csv':
            file = open(in_file, 'r', encoding=spec.get('encoding', cfg.ENCODING))
            reader = \
                csv.reader(
                    file,
                    dialect=spec.get('csv_dialect', cfg.CSV_DIALECT),
                    delimiter=spec.get('csv_delimiter', cfg.CSV_DELIMITER),
                    quotechar=spec.get('csv_quotechar', cfg.CSV_QUOTECHAR)
                )
        elif in_format == 'xlsx':
            wb = load_workbook(filename=in_file, read_only=True)
            reader = wb.worksheets[0]
        elif in_format == 'json':
            file = open(in_file, 'r', encoding=spec.get('encoding', cfg.ENCODING))
            reader = json.load(file)
            assert (
                isinstance(reader, list)
                ), f"Bad json file {in_file}"

        count = 0
        data = []
        insert_line = None
        batch_size = 1000
        for row in reader:
            if count == 0:
                # create header and pepare line insert stmt
                if source['database'] == 'postgres':
                    cur.execute(
                        """
                        insert into ida (
                            iuser,
                            ifile,
                            entity
                        ) values (
                            %s,
                            %s,
                            %s
                        ) returning iload
                        """,
                        (USER_ID, filename, spec_name)
                    )
                    iload = cur.fetchone()[0]
                    con.commit()
                    insert_line = spec.get("insert_statement") or \
                        """
                        insert into ida_lines (
                            iload,
                            iline,
                        """ + ','.join(f'c{i+1}' for i in range(len(row))) + """
                        ) values (
                            %s,
                            %s,
                        """ + ','.join('%s' for i in range(len(row))) + """
                        )
                        """
                elif source['database'] == 'mysql':
                    cur.execute(
                        """
                        insert into ida (
                            iuser,
                            ifile,
                            entity
                        ) values (
                            %s,
                            %s,
                            %s
                        )
                        """,
                        (USER_ID, filename, spec_name)
                    )
                    cur.execute("select last_insert_id()")
                    iload = cur.fetchone()[0]
                    con.commit()
                    insert_line = spec.get("insert_statement") or \
                        """
                        insert into ida_lines (
                            iload,
                            iline,
                        """ + ','.join(f'c{i+1}' for i in range(len(row))) + """
                        ) values (
                            %s,
                            %s,
                        """ + ','.join('%s' for i in range(len(row))) + """
                        )
                        """
                elif source['database'] == 'oracle':
                    iload = cur.var(source['lib'].NUMBER)
                    cur.execute(
                        """
                        insert into ida (
                            iload,
                            iuser,
                            ifile,
                            entity
                        ) values (
                            ida_seq.nextval,
                            :iuser,
                            :ifile,
                            :entity
                        ) returning iload into :iload
                        """,
                        (USER_ID, filename, spec_name, iload)
                    )
                    iload = iload.getvalue()[0]
                    con.commit()
                    insert_line = spec.get("insert_statement") or \
                        """
                        insert into ida_lines (
                            iload,
                            iline,
                        """ + ','.join(f'c{i+1}' for i in range(len(row))) + """
                        ) values (
                            :iload,
                            :iline,
                        """ + ','.join(f':c{i+1}' for i in range(len(row))) + """
                        )
                        """
                elif source['database'] == 'sqlite':
                    cur.execute(
                        """
                        insert into ida (
                            iuser,
                            ifile,
                            entity
                        ) values (
                            :iuser,
                            :ifile,
                            :entity
                        ) returning rowid
                        """,
                        (USER_ID, filename, spec_name)
                    )
                    iload = cur.fetchone()[0]
                    con.commit()
                    insert_line = spec.get("insert_statement") or \
                        """
                        insert into ida_lines (
                            iload,
                            iline,
                        """ + ','.join(f'c{i+1}' for i in range(len(row))) + """
                        ) values (
                            ?,
                            ?,
                        """ + ','.join(f':c{i+1}' for i in range(len(row))) + """
                        )
                        """
                if DEBUGGING:
                    logger.info('-- insert')
                    logger.info('\n\n' + insert_line.strip() + '\n')

            count += 1
            if in_format == 'csv':
                if spec.get("insert_statement"):
                    data.append(spec["insert_values"](row))
                elif spec.get("insert_values"):
                    data.append((iload, count, *(spec["insert_values"](row))))
                else:
                    data.append((iload, count, *row))
            elif in_format == 'xlsx':
                if spec.get("insert_statement"):
                    data.append(tuple(cell.value for cell in spec["insert_values"](row)))
                elif spec.get("insert_values"):
                    data.append((iload, count, *[cell.value for cell in spec["insert_values"](row)]))
                else:
                    data.append((iload, count, *[cell.value for cell in row]))
            elif in_format == 'json':
                if spec.get("insert_statement"):
                    data.append(spec["insert_values"](row))
                else:
                    data.append((iload, count, *(spec["insert_values"](row))))

            if len(data) % batch_size == 0:
                if source['database'] == 'postgres':
                    source['extras'].execute_batch(cur, insert_line, data, page_size=100)
                elif source['database'] == 'mysql':
                    cur.executemany(insert_line, data)
                elif source['database'] == 'oracle':
                    cur.executemany(insert_line, data)
                elif source['database'] == 'sqlite':
                    cur.executemany(insert_line, data)
                data = []

        if data:
            if source['database'] == 'postgres':
                source['extras'].execute_batch(cur, insert_line, data, page_size=100)
            elif source['database'] == 'mysql':
                cur.executemany(insert_line, data)
            elif source['database'] == 'oracle':
                cur.executemany(insert_line, data)
            elif source['database'] == 'sqlite':
                cur.executemany(insert_line, data)

        if in_format in ('csv', 'json'):
            file.close()
        elif in_format == 'xlsx':
            wb.close()

        con.commit()
        #os.remove(in_file)
        logger.info(f'Loaded {count} rows with iload={iload}')

        # 2) validate loaded data

        err_count = 0
        if spec.get('validate_statements'):

            if DEBUGGING:
                logger.info('-- validate')
            for stmt in spec['validate_statements']:
                if DEBUGGING:
                    logger.info('\n\n' + stmt.strip() + '\n')
                cur.execute(stmt, (iload,))

            if spec.get('insert_statement') is None:
                #
                # follow buil-in ida protocol
                # if ida_lines rows have errors then update load status (ida.isat)
                #
                if source['database'] == 'postgres':
                    query = "select count(*) from ida_lines where iload = %s and istat = 2"
                elif source['database'] == 'mysql':
                    query = "select count(*) from ida_lines where iload = %s and istat = 2"
                elif source['database'] == 'oracle':
                    query = "select count(*) from ida_lines where iload = :1 and istat = 2"
                elif  source['database'] == 'sqlite':
                    query = "select count(*) from ida_lines where iload = ? and istat = 2"
                cur.execute(query, (iload,))
                err_count = cur.fetchone()
                err_count = err_count[0] if err_count else 0

                if err_count > 0:
                    # mark as failed
                    if source['database'] == 'postgres':
                        query = "update ida set istat = 2 where iload = %s"
                    elif source['database'] == 'mysql':
                        query = "update ida set istat = 2 where iload = %s"
                    elif source['database'] == 'oracle':
                        query = "update ida set istat = 2 where iload = :1"
                    elif  source['database'] == 'sqlite':
                        query = "update ida set istat = 2 where iload = ?"
                    cur.execute(query, (iload,))
                if err_count > 0:
                    logger.info(f'Validation found {err_count} bad lines.')
                else:
                    logger.info('Validation succeded')
            else:
                if source['database'] == 'postgres':
                    query = "select istat, ierrm from ida where iload = %s"
                elif source['database'] == 'mysql':
                    query = "select istat, ierrm from ida where iload = %s"
                elif source['database'] == 'oracle':
                    query = "select istat, ierrm from ida where iload = :iload"
                elif  source['database'] == 'sqlite':
                    query = "select istat, ierrm from ida where iload = ?"
                cur.execute(query, (iload,))
                row = cur.fetchone()
                err_count = 1 if row and row[0] == 2 else 0
                if err_count > 0:
                    logger.info(f'Validation failed with error: {row[1]}')
                else:
                    logger.info('Validation succeded')

            con.commit()

        # 3) process loaded data

        if err_count == 0 and spec.get('process_statements'):

            if DEBUGGING:
                logger.info('-- process')
            for stmt in spec['process_statements']:
                if DEBUGGING:
                    logger.info('\n\n' + stmt.strip() + '\n')
                cur.execute(stmt, (iload,))

            if spec.get('insert_statement') is None:
                #
                # follow buil-in ida protocol
                # if ida_lines rows have errors then update load status (ida.isat)
                #
                if source['database'] == 'postgres':
                    query = "select count(*) from ida_lines where iload = %s and istat = 2"
                elif source['database'] == 'mysql':
                    query = "select count(*) from ida_lines where iload = %s and istat = 2"
                elif source['database'] == 'oracle':
                    query = "select count(*) from ida_lines where iload = :iload and istat = 2"
                elif  source['database'] == 'sqlite':
                    query = "select count(*) from ida_lines where iload = ? and istat = 2"
                cur.execute(query, (iload,))
                err_count = cur.fetchone()
                err_count = err_count[0] if err_count else 0

                # mark as failed or succeeded
                if source['database'] == 'postgres':
                    query = f"update ida set istat = {2 if err_count > 0 else 1} where iload = %s"
                elif source['database'] == 'mysql':
                    query = f"update ida set istat = {2 if err_count > 0 else 1} where iload = %s"
                elif source['database'] == 'oracle':
                    query = f"update ida set istat = {2 if err_count > 0 else 1} where iload = :iload"
                elif  source['database'] == 'sqlite':
                    query = f"update ida set istat = {2 if err_count > 0 else 1} where iload = ?"
                cur.execute(query, (iload,))
                if err_count > 0:
                    logger.info(f'Processing found {err_count} bad lines.')
                else:
                    logger.info('Processing succeeded')
            else:
                if source['database'] == 'postgres':
                    query = "select istat, imess from ida where iload = %s"
                elif source['database'] == 'mysql':
                    query = "select istat, imess from ida where iload = %s"
                elif source['database'] == 'oracle':
                    query = "select istat, imess from ida where iload = :iload"
                elif  source['database'] == 'sqlite':
                    query = "select istat, imess from ida where iload = ?"
                cur.execute(query, (iload,))
                row = cur.fetchone()
                err_count = 1 if row and row[0] == 2 else 0
                if err_count > 0:
                    logger.info(f'Processing failed with error: {row[1]}')
                else:
                    # mark as succeeded
                    if source['database'] == 'postgres':
                        query = f"update ida set istat = 1 where iload = %s"
                    elif source['database'] == 'mysql':
                        query = f"update ida set istat = 1 where iload = %s"
                    elif source['database'] == 'oracle':
                        query = f"update ida set istat = 1 where iload = :iload"
                    elif  source['database'] == 'sqlite':
                        query = f"update ida set istat = 1 where iload = ?"
                    cur.execute(query, (iload,))
                    logger.info('Processing succeeded')
            con.commit()

        #
        # remove old data from ida preserving only last N loads
        #
        if source['database'] == 'postgres':
            query = """
                delete from ida o
                where entity = %s
                    and iload not in (
                        select iload from ida where entity = o.entity order by idate desc limit %s
                    )
                """
        elif source['database'] == 'mysql':
            query = """
                delete from ida
                where entity = %s
                    and iload in (
                      select iload
                      from (
                          select iload, row_number() over (partition by entity order by idate desc) rn from ida
                          ) q
                      where rn > %s
                    )
                """
        elif source['database'] == 'oracle':
            query = """
                delete from ida
                where entity = :1
                    and iload in (
                      select iload
                      from (
                          select iload, row_number() over (partition by entity order by idate desc) rn from ida
                          ) q
                      where rn > :2
                    )
                """
        elif  source['database'] == 'sqlite':
            query = """
                delete from ida as o
                where entity = ?
                    and iload not in (
                        select iload from ida where entity = o.entity order by idate desc limit ?
                    )
                """
        if DEBUGGING:
            logger.info('-- keep ida fit')
            logger.info('\n\n' + query.strip() + '\n')
        cur.execute(
            query,
            (spec_name, spec.get('preserve_n_loads', cfg.PRESERVE_N_LOADS))
        )
        con.commit()

    except:
        logger.exception('EXCEPT')
        if sources[spec['source']].get('con'):
            sources[spec['source']]['con'].rollback()
    finally:
        if file:
            file.close()
        if wb:
            wb.close()


def main():
    logger.info('-- start %s' % ' '.join(sys.argv))

    #process(SPEC, specs[SPEC], IN_FILE)
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
                    src["extras"] = extras
                elif src["database"] == "mysql":
                    import mysql.connector
                    src["lib"] = mysql.connector
                elif src["database"] == "sqlite":
                    import sqlite3
                    src["lib"] = sqlite3
                else:
                    src["lib"] = None
            process(spec_name, spec, args.in_file)

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
