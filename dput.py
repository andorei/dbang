#!/usr/bin/python3

import os
import sys
import csv
import logging
from datetime import date, datetime


DEBUGGING = True
LOGSTDOUT = False

BASENAME = os.path.basename(sys.argv[0])
if len(sys.argv) != 4:
    sys.stderr.write(
        f"""
        Error: Wrong number of arguments.
        Usage: {BASENAME} <cfg-file> <spec> <csv file>
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
        Usage: {BASENAME} <cfg-file> <spec> <csv file>
        """
    )
    sys.exit(1)

sys.path.append(CFG_DIR)
cfg = __import__(CFG_NAME)
sources = cfg.sources
specs = cfg.specs

SPEC = sys.argv[2]
if SPEC not in [*specs.keys(), 'all']:
    sys.stderr.write(
        f"""
        Error: Spec {SPEC} not found in config-file.
        Usage: {BASENAME} <cfg-file> <spec> <csv file>
        """
    )
    sys.exit(1)

#IN_DIR = os.path.join(SCRIPT_DIR, 'in') # set in config-file
CSV_FILE = sys.argv[3]
if not os.path.isfile(CSV_FILE):
    CSV_FILE = os.path.join(cfg.IN_DIR, CSV_FILE)
    if not os.path.isfile(CSV_FILE):
        sys.stderr.write(
        f"""
        Error: CSV file {sys.argv[3]} not found.
        Usage: {BASENAME} <cfg-file> <spec> <csv file>
        """
        )
        sys.exit(1)

SOURCE = sources[specs[SPEC]['source']]
if SOURCE["database"] == "oracle":
    import cx_Oracle
    SOURCE["lib"] = cx_Oracle
elif SOURCE["database"] == "postgres":
    import psycopg2
    from psycopg2 import extras
    SOURCE["lib"] = psycopg2
elif SOURCE["database"] == "mysql":
    import mysql.connector
    SOURCE["lib"] = mysql.connector
elif SOURCE["database"] == "sqlite":
    import sqlite3
    SOURCE["lib"] = sqlite3
else:
    SOURCE["lib"] = None

BASENAME = os.path.basename(sys.argv[0]).split('.')[0]
#LOG_FILE = os.path.join(SCRIPT_DIR, 'log', f'{date.today().isoformat()}_{BASENAME}.log')
LOG_FILE = CSV_FILE + '.log'
USER_ID = BASENAME

logging.basicConfig(
    filename=None if LOGSTDOUT else LOG_FILE,
    format='%(asctime)s:%(levelname)s:%(name)s:%(message)s',
    level=logging.INFO
)
logger = logging.getLogger(BASENAME)


def connection(src):
    if not sources[src].get('con'):
        if sources[src].get('con_string'):
            sources[src]['con'] = \
                sources[src]['lib'].connect(sources[src]['con_string'], **sources[src].get('con_kwargs', dict()))
        else:
            sources[src]['con'] = \
                sources[src]['lib'].connect(**sources[src]['con_kwargs'])
        if sources[src].get('init'):
            if isinstance(sources[src]['init'], str):
                sources[src]['init'] = [sources[src]['init']]
            cur = sources[src]['con'].cursor()
            for init in sources[src]['init']:
                cur.execute(init)
            cur.close()
    return sources[src]['con']


def process(spec_name, spec, csv_file):
    filename = os.path.basename(csv_file)
    
    con = None
    cur = None
    try:
        con = connection(spec['source'])
        cur = con.cursor()

        # 1) load csv file into database
        logger.info(f'Loading {spec_name}, {csv_file}')

        iload = None
        with open(csv_file, 'r', encoding=spec.get('encoding', cfg.CSV_ENCODING)) as f:
            count = 0
            data = []
            insert_line = None
            batch_size = 1000
            csvreader = \
                csv.reader(
                    f,
                    dialect=spec.get('dialect', cfg.CSV_DIALECT),
                    delimiter=spec.get('delimiter', cfg.CSV_DELIMITER),
                    quotechar=spec.get('quotechar', cfg.CSV_QUOTECHAR)
                )
            for row in csvreader:
                if count == 0:
                    # create header
                    if SOURCE['database'] == 'postgres':
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
                        insert_line =  \
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
                    elif SOURCE['database'] == 'mysql':
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
                        insert_line =  \
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
                    elif SOURCE['database'] == 'oracle':
                        iload = cur.var(SOURCE['lib'].NUMBER)
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
                        insert_line =  \
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
                    elif SOURCE['database'] == 'sqlite':
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
                        insert_line =  \
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
                count += 1
                data.append((iload, count, *row))
                if len(data) % batch_size == 0:
                    if SOURCE['database'] == 'postgres':
                        extras.execute_batch(cur, insert_line, data, page_size=100)
                    elif SOURCE['database'] == 'mysql':
                        cur.executemany(insert_line, data)
                    elif SOURCE['database'] == 'oracle':
                        cur.executemany(insert_line, data)
                    elif SOURCE['database'] == 'sqlite':
                        cur.executemany(insert_line, data)
                    data = []
            if data:
                if SOURCE['database'] == 'postgres':
                    extras.execute_batch(cur, insert_line, data, page_size=100)
                elif SOURCE['database'] == 'mysql':
                    cur.executemany(insert_line, data)
                elif SOURCE['database'] == 'oracle':
                    cur.executemany(insert_line, data)
                elif SOURCE['database'] == 'sqlite':
                    cur.executemany(insert_line, data)

        con.commit()
        #os.remove(csv_file)
        logger.info(f'Loaded {count} rows with iload={iload}')

        # 2) validate loaded data

        err_count = 0
        if spec.get('validate_statements'):

            for stmt in spec['validate_statements']:
                cur.execute(stmt, (iload,))

            if SOURCE['database'] == 'postgres':
                query = "select count(*) from ida_lines where iload = %s and istat = 2"
            elif SOURCE['database'] == 'mysql':
                query = "select count(*) from ida_lines where iload = %s and istat = 2"
            elif SOURCE['database'] == 'oracle':
                query = "select count(*) from ida_lines where iload = :1 and istat = 2"
            elif  SOURCE['database'] == 'sqlite':
                query = "select count(*) from ida_lines where iload = ? and istat = 2"
            cur.execute(query, (iload,))
            err_count = cur.fetchone()
            err_count = err_count[0] if err_count else 0

            if err_count > 0:
                # mark as failed
                if SOURCE['database'] == 'postgres':
                    query = "update ida set istat = 2 where iload = %s"
                elif SOURCE['database'] == 'mysql':
                    query = "update ida set istat = 2 where iload = %s"
                elif SOURCE['database'] == 'oracle':
                    query = "update ida set istat = 2 where iload = :1"
                elif  SOURCE['database'] == 'sqlite':
                    query = "update ida set istat = 2 where iload = ?"
                cur.execute(query, (iload,))

            con.commit()
            logger.info(f'Validation found {err_count} bad lines.')

        # 3) process loaded data

        if err_count == 0 and spec.get('process_statements'):

            for stmt in spec['process_statements']:
                cur.execute(stmt, (iload,))

            if SOURCE['database'] == 'postgres':
                query = "select count(*) from ida_lines where iload = %s and istat = 2"
            elif SOURCE['database'] == 'mysql':
                query = "select count(*) from ida_lines where iload = %s and istat = 2"
            elif SOURCE['database'] == 'oracle':
                query = "select count(*) from ida_lines where iload = :iload and istat = 2"
            elif  SOURCE['database'] == 'sqlite':
                query = "select count(*) from ida_lines where iload = ? and istat = 2"
            cur.execute(query, (iload,))
            err_count = cur.fetchone()
            err_count = err_count[0] if err_count else 0

            if err_count > 0:
                # mark as failed
                if SOURCE['database'] == 'postgres':
                    query = "update ida set istat = 2 where iload = %s"
                elif SOURCE['database'] == 'mysql':
                    query = "update ida set istat = 2 where iload = %s"
                elif SOURCE['database'] == 'oracle':
                    query = "update ida set istat = 2 where iload = :iload"
                elif  SOURCE['database'] == 'sqlite':
                    query = "update ida set istat = 2 where iload = ?"
                cur.execute(query, (iload,))

            con.commit()
            logger.info(f'Processing found {err_count} bad lines.')

    except:
        logger.exception('EXCEPT')
    finally:
        if cur:
            cur.close()
        if con:
            con.close()
            con = None


def main():
    logger.info('-- start %s' % ' '.join(sys.argv))

    process(SPEC, specs[SPEC], CSV_FILE)

    logger.info('-- done')


if __name__ == '__main__':
    main()
