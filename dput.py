#!/usr/bin/env python3

import os
import sys
import locale
import re
import glob
import csv
import json
import argparse
import logging
from datetime import date, datetime

from openpyxl import load_workbook


VERSION = '0.3'

parser = argparse.ArgumentParser(
    description="Load data from file into DB, as specified in cfg-file spec.",
    epilog="Thanks for using %(prog)s!"
)

parser.add_argument("-a", "--arg", action="append", help="pass one or more arguments to SQL query")
parser.add_argument("-d", "--delete", action="store_true", help="delete loaded data file(s)")
parser.add_argument("-f", "--force", action="store_true", help="load data file(s) unconditionally")
parser.add_argument("-t", "--trace", action="store_true", help="enable tracing")
parser.add_argument("-u", "--user", action="store",
                    default=os.environ.get('USER', os.environ.get('USERNAME', 'DBANG')),
                    help="set data loader username")
parser.add_argument("-v", "--version", action="version", version="%(prog)s " + VERSION)
parser.add_argument("cfg_file", help="cfg-file name")
parser.add_argument("spec", help="spec name")
parser.add_argument("in_file", nargs="?", default=None, help="input file name")

args = parser.parse_args()

locale.setlocale(locale.LC_TIME, '')
BASENAME = os.path.basename(sys.argv[0])
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

SPEC = args.spec
# filter out specs commented out with leading --
specs = {k:v for k,v in specs.items() if not k.startswith('--')}
if SPEC not in [*specs.keys(), 'all', *(tag for val in specs.values() if val.get('tags') for tag in val['tags'])]:
    sys.stderr.write(
        parser.format_usage() + \
        f"{BASENAME}: error: spec not found in cfg-file: {SPEC}\n"
    )
    sys.exit(1)

IN_DIR = getattr(cfg, 'IN_DIR', CUR_DIR)
if not os.path.isdir(IN_DIR):
    sys.stderr.write(
        parser.format_usage() + \
        f"{BASENAME}: error: in dir not found: {IN_DIR}\n"
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

# output file encoding by default
ENCODING = getattr(cfg, 'ENCODING', locale.getpreferredencoding())
# datetime format for strftime is ISO 86101 by default
#DATETIME_FORMAT = getattr(cfg, 'DATETIME_FORMAT', '%Y-%m-%d %H:%M:%S%z')
#DATE_FORMAT = getattr(cfg, 'DATE_FORMAT', '%Y-%m-%d')

CSV_DIALECT = getattr(cfg, 'CSV_DIALECT', 'excel')
CSV_DELIMITER = getattr(cfg, 'CSV_DELIMITER', csv.get_dialect(CSV_DIALECT).delimiter)

USER_ID = args.user
STAT_FILE = os.path.join(TEMP_DIR, f".{CFG_MODULE}.json")
# number of loads preserved per entity
PRESERVE_N_LOADS = getattr(cfg, 'PRESERVE_N_LOADS', 10)
PRESERVE_N_TRACES = getattr(cfg, 'PRESERVE_N_TRACES', 10)

BATCH_SIZE = 1000


# BEGIN DB SPECIFIC STUFF ######################################################
#
# To add support for a new database
# 1) add database specific stuff to the following IDA_ objects and 
# 2) import database driver in main() at the end of the script.

IDA_SETUP = {
    "mysql": [
    """
create table if not exists ida (
    iload int not null auto_increment,
    idate timestamp not null default current_timestamp,
    istat smallint not null default 0,
    imess varchar(4000),
    ifile varchar(256),
    iuser varchar(100),
    entity varchar(100),
    arg1 text,
    arg2 text,
    arg3 text,
    arg4 text,
    arg5 text,
    arg6 text,
    arg7 text,
    arg8 text,
    arg9 text,
    primary key (iload)
)
    """,
    """
create table if not exists ida_lines (
    iload int not null,
    iline int not null,
    ntable smallint not null default -1,
    nline int not null default -1,
    istat smallint not null default 0,
    ierrm varchar(4000) null,
    c1 text, c2 text, c3 text, c4 text, c5 text,
    c6 text, c7 text, c8 text, c9 text, c10 text,
    c11 text, c12 text, c13 text, c14 text, c15 text,
    c16 text, c17 text, c18 text, c19 text, c20 text,
    c21 text, c22 text, c23 text, c24 text, c25 text,
    c26 text, c27 text, c28 text, c29 text, c30 text,
    c31 text, c32 text, c33 text, c34 text, c35 text,
    c36 text, c37 text, c38 text, c39 text, c40 text,
    c41 text, c42 text, c43 text, c44 text, c45 text,
    c46 text, c47 text, c48 text, c49 text, c50 text,
    c51 text, c52 text, c53 text, c54 text, c55 text,
    c56 text, c57 text, c58 text, c59 text, c60 text,
    c61 text, c62 text, c63 text, c64 text, c65 text,
    c66 text, c67 text, c68 text, c69 text, c70 text,
    c71 text, c72 text, c73 text, c74 text, c75 text,
    c76 text, c77 text, c78 text, c79 text, c80 text,
    c81 text, c82 text, c83 text, c84 text, c85 text,
    c86 text, c87 text, c88 text, c89 text, c90 text,
    c91 text, c92 text, c93 text, c94 text, c95 text,
    c96 text, c97 text, c98 text, c99 text, c100 text,
    primary key (iload, iline, ntable, nline),
    foreign key (iload) references ida(iload) on delete cascade
)
    """
    ],
    "oracle": [
    """
declare
    table_exists pls_integer;
begin
    select count(*)
    into table_exists
    from all_objects
    where object_name in ('IDA', 'IDA_LINES')
        and owner = user
        and object_type in ('TABLE', 'SYNONYM')
    ;
    if 0 = table_exists then
        execute immediate '
            create table ida (
                iload number(9) not null,
                idate timestamp default current_timestamp not null,
                istat number(1) default 0 not null,
                imess varchar2(4000),
                ifile varchar2(256),
                iuser varchar2(100),
                entity varchar2(100),
                arg1 varchar2(4000),
                arg2 varchar2(4000),
                arg3 varchar2(4000),
                arg4 varchar2(4000),
                arg5 varchar2(4000),
                arg6 varchar2(4000),
                arg7 varchar2(4000),
                arg8 varchar2(4000),
                arg9 varchar2(4000),
                primary key (iload)
            )';
        execute immediate '
            create table ida_lines (
                iload number(9) not null,
                iline number(9) not null,
                ntable number(3) default -1 not null,
                nline number(9) default -1 not null,
                istat number(1) default 0 not null,
                ierrm varchar2(4000),
                c1 varchar2(4000), c2 varchar2(4000), c3 varchar2(4000), c4 varchar2(4000),
                c5 varchar2(4000), c6 varchar2(4000), c7 varchar2(4000), c8 varchar2(4000),
                c9 varchar2(4000), c10 varchar2(4000), c11 varchar2(4000), c12 varchar2(4000),
                c13 varchar2(4000), c14 varchar2(4000), c15 varchar2(4000), c16 varchar2(4000),
                c17 varchar2(4000), c18 varchar2(4000), c19 varchar2(4000), c20 varchar2(4000),
                c21 varchar2(4000), c22 varchar2(4000), c23 varchar2(4000), c24 varchar2(4000),
                c25 varchar2(4000), c26 varchar2(4000), c27 varchar2(4000), c28 varchar2(4000),
                c29 varchar2(4000), c30 varchar2(4000), c31 varchar2(4000), c32 varchar2(4000),
                c33 varchar2(4000), c34 varchar2(4000), c35 varchar2(4000), c36 varchar2(4000),
                c37 varchar2(4000), c38 varchar2(4000), c39 varchar2(4000), c40 varchar2(4000),
                c41 varchar2(4000), c42 varchar2(4000), c43 varchar2(4000), c44 varchar2(4000),
                c45 varchar2(4000), c46 varchar2(4000), c47 varchar2(4000), c48 varchar2(4000),
                c49 varchar2(4000), c50 varchar2(4000), c51 varchar2(4000), c52 varchar2(4000),
                c53 varchar2(4000), c54 varchar2(4000), c55 varchar2(4000), c56 varchar2(4000),
                c57 varchar2(4000), c58 varchar2(4000), c59 varchar2(4000), c60 varchar2(4000),
                c61 varchar2(4000), c62 varchar2(4000), c63 varchar2(4000), c64 varchar2(4000),
                c65 varchar2(4000), c66 varchar2(4000), c67 varchar2(4000), c68 varchar2(4000),
                c69 varchar2(4000), c70 varchar2(4000), c71 varchar2(4000), c72 varchar2(4000),
                c73 varchar2(4000), c74 varchar2(4000), c75 varchar2(4000), c76 varchar2(4000),
                c77 varchar2(4000), c78 varchar2(4000), c79 varchar2(4000), c80 varchar2(4000),
                c81 varchar2(4000), c82 varchar2(4000), c83 varchar2(4000), c84 varchar2(4000),
                c85 varchar2(4000), c86 varchar2(4000), c87 varchar2(4000), c88 varchar2(4000),
                c89 varchar2(4000), c90 varchar2(4000), c91 varchar2(4000), c92 varchar2(4000),
                c93 varchar2(4000), c94 varchar2(4000), c95 varchar2(4000), c96 varchar2(4000),
                c97 varchar2(4000), c98 varchar2(4000), c99 varchar2(4000), c100 varchar2(4000),
                primary key (iload, iline, ntable, nline),
                foreign key (iload) references ida(iload) on delete cascade
            )';
        execute immediate 'create sequence ida_seq';
    end if;
end;
    """
    ],
    "postgres": [
    """
create table if not exists ida (
    iload serial4 not null,
    idate timestamptz not null default now(),
    istat int2 not null default 0,
    imess varchar(4000),
    ifile varchar(256),
    iuser varchar(100),
    entity varchar(100),
    arg1 varchar(4000),
    arg2 varchar(4000),
    arg3 varchar(4000),
    arg4 varchar(4000),
    arg5 varchar(4000),
    arg6 varchar(4000),
    arg7 varchar(4000),
    arg8 varchar(4000),
    arg9 varchar(4000),
    primary key (iload)
)
    """,
    """
create table if not exists ida_lines (
    iload int not null,
    iline int not null,
    ntable smallint not null default -1,
    nline int not null default -1,
    istat smallint not null default 0,
    ierrm varchar(4000),
    c1 varchar(4000), c2 varchar(4000), c3 varchar(4000), c4 varchar(4000), c5 varchar(4000),
    c6 varchar(4000), c7 varchar(4000), c8 varchar(4000), c9 varchar(4000), c10 varchar(4000),
    c11 varchar(4000), c12 varchar(4000), c13 varchar(4000), c14 varchar(4000), c15 varchar(4000),
    c16 varchar(4000), c17 varchar(4000), c18 varchar(4000), c19 varchar(4000), c20 varchar(4000),
    c21 varchar(4000), c22 varchar(4000), c23 varchar(4000), c24 varchar(4000), c25 varchar(4000),
    c26 varchar(4000), c27 varchar(4000), c28 varchar(4000), c29 varchar(4000), c30 varchar(4000),
    c31 varchar(4000), c32 varchar(4000), c33 varchar(4000), c34 varchar(4000), c35 varchar(4000),
    c36 varchar(4000), c37 varchar(4000), c38 varchar(4000), c39 varchar(4000), c40 varchar(4000),
    c41 varchar(4000), c42 varchar(4000), c43 varchar(4000), c44 varchar(4000), c45 varchar(4000),
    c46 varchar(4000), c47 varchar(4000), c48 varchar(4000), c49 varchar(4000), c50 varchar(4000),
    c51 varchar(4000), c52 varchar(4000), c53 varchar(4000), c54 varchar(4000), c55 varchar(4000),
    c56 varchar(4000), c57 varchar(4000), c58 varchar(4000), c59 varchar(4000), c60 varchar(4000),
    c61 varchar(4000), c62 varchar(4000), c63 varchar(4000), c64 varchar(4000), c65 varchar(4000),
    c66 varchar(4000), c67 varchar(4000), c68 varchar(4000), c69 varchar(4000), c70 varchar(4000),
    c71 varchar(4000), c72 varchar(4000), c73 varchar(4000), c74 varchar(4000), c75 varchar(4000),
    c76 varchar(4000), c77 varchar(4000), c78 varchar(4000), c79 varchar(4000), c80 varchar(4000),
    c81 varchar(4000), c82 varchar(4000), c83 varchar(4000), c84 varchar(4000), c85 varchar(4000),
    c86 varchar(4000), c87 varchar(4000), c88 varchar(4000), c89 varchar(4000), c90 varchar(4000),
    c91 varchar(4000), c92 varchar(4000), c93 varchar(4000), c94 varchar(4000), c95 varchar(4000),
    c96 varchar(4000), c97 varchar(4000), c98 varchar(4000), c99 varchar(4000), c100 varchar(4000),
    primary key (iload, iline, ntable, nline),
    foreign key (iload) references ida(iload) on delete cascade
)
    """
    ],
    "sqlite": [
    """
create table if not exists ida (
    iload INTEGER not null PRIMARY KEY AUTOINCREMENT,
    idate timestamptz not null default current_timestamp,
    istat smallint not null default 0,
    imess varchar(4000),
    ifile varchar(256),
    iuser varchar(100),
    entity varchar(100),
    arg1 varchar(4000),
    arg2 varchar(4000),
    arg3 varchar(4000),
    arg4 varchar(4000),
    arg5 varchar(4000),
    arg6 varchar(4000),
    arg7 varchar(4000),
    arg8 varchar(4000),
    arg9 varchar(4000)
)
    """,
    """
create table if not exists ida_lines (
    iload int not null,
    iline int not null,
    ntable smallint not null default -1,
    nline int not null default -1,
    istat smallint not null default 0,
    ierrm varchar(4000),
    c1 varchar(4000), c2 varchar(4000), c3 varchar(4000), c4 varchar(4000), c5 varchar(4000),
    c6 varchar(4000), c7 varchar(4000), c8 varchar(4000), c9 varchar(4000), c10 varchar(4000),
    c11 varchar(4000), c12 varchar(4000), c13 varchar(4000), c14 varchar(4000), c15 varchar(4000),
    c16 varchar(4000), c17 varchar(4000), c18 varchar(4000), c19 varchar(4000), c20 varchar(4000),
    c21 varchar(4000), c22 varchar(4000), c23 varchar(4000), c24 varchar(4000), c25 varchar(4000),
    c26 varchar(4000), c27 varchar(4000), c28 varchar(4000), c29 varchar(4000), c30 varchar(4000),
    c31 varchar(4000), c32 varchar(4000), c33 varchar(4000), c34 varchar(4000), c35 varchar(4000),
    c36 varchar(4000), c37 varchar(4000), c38 varchar(4000), c39 varchar(4000), c40 varchar(4000),
    c41 varchar(4000), c42 varchar(4000), c43 varchar(4000), c44 varchar(4000), c45 varchar(4000),
    c46 varchar(4000), c47 varchar(4000), c48 varchar(4000), c49 varchar(4000), c50 varchar(4000),
    c51 varchar(4000), c52 varchar(4000), c53 varchar(4000), c54 varchar(4000), c55 varchar(4000),
    c56 varchar(4000), c57 varchar(4000), c58 varchar(4000), c59 varchar(4000), c60 varchar(4000),
    c61 varchar(4000), c62 varchar(4000), c63 varchar(4000), c64 varchar(4000), c65 varchar(4000),
    c66 varchar(4000), c67 varchar(4000), c68 varchar(4000), c69 varchar(4000), c70 varchar(4000),
    c71 varchar(4000), c72 varchar(4000), c73 varchar(4000), c74 varchar(4000), c75 varchar(4000),
    c76 varchar(4000), c77 varchar(4000), c78 varchar(4000), c79 varchar(4000), c80 varchar(4000),
    c81 varchar(4000), c82 varchar(4000), c83 varchar(4000), c84 varchar(4000), c85 varchar(4000),
    c86 varchar(4000), c87 varchar(4000), c88 varchar(4000), c89 varchar(4000), c90 varchar(4000),
    c91 varchar(4000), c92 varchar(4000), c93 varchar(4000), c94 varchar(4000), c95 varchar(4000),
    c96 varchar(4000), c97 varchar(4000), c98 varchar(4000), c99 varchar(4000), c100 varchar(4000),
    primary key (iload, iline, ntable, nline),
    foreign key (iload) references ida(iload) on delete cascade
)
    """,
    "PRAGMA foreign_keys = ON"
    ],
}


def ida_insert_header_mysql(cur, user_id, filename, spec_name, load_args):
    insert_stmt = \
        """
insert into ida (
    iuser, ifile, entity, {cols}
) values (
    %s,%s,%s,{vals}
)
        """.format(
            cols=','.join(f"arg{i+1}" for i in range(len(load_args))),
            vals=','.join('%s' for i in range(len(load_args)))
        )
    logger.debug("-- insert header\n%s\n", insert_stmt.rstrip())
    cur.execute(insert_stmt, (user_id, filename, spec_name, *load_args))
    cur.execute("select last_insert_id()")
    return cur.fetchone()[0]


def ida_insert_header_oracle(cur, user_id, filename, spec_name, load_args):
    insert_stmt = \
        """
insert into ida (
    iload, iuser, ifile, entity, {cols}
) values (
    ida_seq.nextval,:iuser,:ifile,:entity,{vals}
) returning iload into :iload
        """.format(
            cols=','.join(f"arg{i+1}" for i in range(len(load_args))),
            vals=','.join(f":arg{i+1}" for i in range(len(load_args)))
        )
    logger.debug("-- insert header\n%s\n", insert_stmt.rstrip())
    #iload = cur.var(source['lib'].NUMBER)
    iload = cur.var(int)
    cur.execute(insert_stmt, (user_id, filename, spec_name, *load_args, iload))
    return iload.getvalue()[0]


def ida_insert_header_postgres(cur, user_id, filename, spec_name, load_args):
    insert_stmt = \
        """
insert into ida (
    iuser, ifile, entity, {cols}
) values (
    %s,%s,%s,{vals}
) returning iload
        """.format(
            cols=','.join(f"arg{i+1}" for i in range(len(load_args))),
            vals=','.join('%s' for i in range(len(load_args)))
        )
    logger.debug("-- insert header\n%s\n", insert_stmt.rstrip())
    cur.execute(insert_stmt, (user_id, filename, spec_name, *load_args))
    return cur.fetchone()[0]


def ida_insert_header_sqlite(cur, user_id, filename, spec_name, load_args):
    insert_stmt = \
        """
insert into ida (
    iuser, ifile, entity, {cols}
) values (
    ?,?,?,{vals}
)
        """.format(
            cols=','.join(f"arg{i+1}" for i in range(len(load_args))),
            vals=','.join('?' for i in range(len(load_args)))
        )
    logger.debug("-- insert header\n%s\n", insert_stmt.rstrip())
    cur.execute(insert_stmt, (user_id, filename, spec_name, *load_args))
    #since v3.35 use "returning iload" in insert and cur.fetchone()[0]
    return cur.lastrowid

IDA_INSERT_HEADER = {
    "mysql": ida_insert_header_mysql,
    "oracle": ida_insert_header_oracle,
    "postgres": ida_insert_header_postgres,
    "sqlite": ida_insert_header_sqlite,
}

IDA_INSERT_ROW = """
insert into ida_lines (
    iload, iline, {cols}
) values (
    {vals}
)
"""
IDA_BUILD_INSERT_ROW = {
    "mysql": \
        lambda row:
            IDA_INSERT_ROW.format(
                cols=','.join(f"c{i+1}" for i in range(len(row) - 2)),
                vals=','.join('%s' for i in range(len(row)))
            ),
    "oracle": \
        lambda row:
            IDA_INSERT_ROW.format(
                cols=','.join(f"c{i+1}" for i in range(len(row) - 2)),
                vals=','.join(f":{i+1}" for i in range(len(row)))
            ),
    "postgres": \
        lambda row:
            IDA_INSERT_ROW.format(
                cols=','.join(f"c{i+1}" for i in range(len(row) - 2)),
                vals=','.join('%s' for i in range(len(row)))
            ),
    "sqlite": \
        lambda row:
            IDA_INSERT_ROW.format(
                cols=','.join(f"c{i+1}" for i in range(len(row) - 2)),
                vals=','.join('?' for i in range(len(row)))
            ),
}

IDA_INSERT_ROWS = """
insert into ida_lines (
    iload, iline, ntable, nline, {cols}
) values (
    {vals}
)
"""
IDA_BUILD_INSERT_ROWS = {
    "mysql": \
        lambda row:
            IDA_INSERT_ROWS.format(
                cols=','.join(f"c{i+1}" for i in range(len(row) - 4)),
                vals=','.join('%s' for i in range(len(row)))
            ),
    "oracle": \
        lambda row:
            IDA_INSERT_ROWS.format(
                cols=','.join(f"c{i+1}" for i in range(len(row) - 4)),
                vals=','.join(f":{i+1}" for i in range(len(row)))
            ),
    "postgres": \
        lambda row:
            IDA_INSERT_ROWS.format(
                cols=','.join(f"c{i+1}" for i in range(len(row) - 4)),
                vals=','.join('%s' for i in range(len(row)))
            ),
    "sqlite": \
        lambda row:
            IDA_INSERT_ROWS.format(
                cols=','.join(f"c{i+1}" for i in range(len(row) - 4)),
                vals=','.join('?' for i in range(len(row)))
            ),
}


def ida_insert_many_rows_anydb(cur, stmt, rows):
    cur.executemany(stmt, rows)

IDA_INSERT_MANY_ROWS = {
    "mysql": ida_insert_many_rows_anydb,
    "oracle": ida_insert_many_rows_anydb,
    "postgres": ida_insert_many_rows_anydb,
    "sqlite": ida_insert_many_rows_anydb,
}

IDA_SELECT_ISTAT_2_COUNT = {
    "mysql": """
select count(*) from ida_lines where iload = %s and istat = 2
    """,
    "oracle": """
select count(*) from ida_lines where iload = :iload and istat = 2
    """,
    "postgres": """
select count(*) from ida_lines where iload = %s and istat = 2
    """,
    "sqlite": """
select count(*) from ida_lines where iload = ? and istat = 2
    """,
}
IDA_SELECT_ISTAT_IMESS = {
    "mysql": """
select istat, imess from ida where iload = %s
    """,
    "oracle": """
select istat, imess from ida where iload = :iload
    """,
    "postgres": """
select istat, imess from ida where iload = %s
    """,
    "sqlite": """
select istat, imess from ida where iload = ?
    """,
}
IDA_UPDATE_ISTAT = {
    "mysql": """
update ida set istat = %s where iload = %s
    """,
    "oracle": """
update ida set istat = :istat where iload = :iload
    """,
    "postgres": """
update ida set istat = %s where iload = %s
    """,
    "sqlite": """
update ida set istat = ? where iload = ?
    """,
}
IDA_DELETE_OLD_LOADS = {
    "mysql": """
delete from ida
where entity = %s
    and iload in (
      select iload
      from (
          select iload, row_number() over (partition by entity order by idate desc) rn from ida
          ) q
      where rn > %s
    )
    """,
    "oracle": """
delete from ida
where entity = :1
    and iload in (
      select iload
      from (
          select iload, row_number() over (partition by entity order by idate desc) rn from ida
          ) q
      where rn > :2
    )
    """,
    "postgres": """
delete from ida o
where entity = %s
    and iload not in (
        select iload from ida where entity = o.entity order by idate desc limit %s
    )
    """,
    "sqlite": """
delete from ida as o
where entity = ?
    and iload not in (
        select iload from ida where entity = o.entity order by idate desc limit ?
    )
    """,
}
# END DB SPECIFIC STUFF ########################################################


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
    if not sources[src].get('con'):
        if sources[src].get('con_string'):
            sources[src]['con'] = \
                sources[src]['lib'].connect(sources[src]['con_string'],
                                            **sources[src].get('con_kwargs', dict()))
        else:
            sources[src]['con'] = \
                sources[src]['lib'].connect(**sources[src]['con_kwargs'])
        if sources[src].get('setup'):
            logger.debug('-- setup')
            exec_sql(sources[src]['con'], sources[src].get('setup'))
    return sources[src]['con']


def trace(ts, status):
    """
    Create or rename trace file to show current status.
    """
    if not args.trace:
        return

    safe_spec = re.sub(r'[^\w. \-()\[\]]', '_', args.spec).rstrip('. ').lstrip()
    safe_user = re.sub(r'[^\w. \-()\[\]]', '_', args.user).rstrip('. ').lstrip()
    this_trace = f"dput#{safe_spec}#{safe_user}#{ts}#"
    this_trace_glob = os.path.join(TEMP_DIR, this_trace + '?')
    this_trace_file = os.path.join(TEMP_DIR, this_trace + str(status))

    traces = glob.glob(this_trace_glob)
    assert len(traces) < 2, f"Too many traces {this_trace_glob}: {len(traces)}"

    if len(traces) == 0:
        with open(this_trace_file, 'w', encoding="UTF-8"):
            pass
        all_traces_glob = os.path.join(TEMP_DIR, f"dput#{safe_spec}#{safe_user}#??????????????#?")
        for i, trace_file in enumerate(sorted(glob.glob(all_traces_glob), reverse=True)):
            if i >= PRESERVE_N_TRACES:
                os.remove(trace_file)
    elif len(traces) == 1 and traces[0] != this_trace_file:
        os.rename(traces[0], this_trace_file)
    logger.debug("trace %s", this_trace + str(status))


def process(spec_name, spec, input_file, stat):
    """
    Process spec from config-file.
    """
    return_code = 0

    in_file = input_file or spec.get('file', 'missing.file')
    if not glob.glob(in_file):
        in_file = os.path.join(IN_DIR, in_file)
        #assert glob.glob(in_file), f"Input file not found: {input_file}"
        if not glob.glob(in_file):
            logger.debug("%s - No files to load: %s", spec_name, input_file or spec.get('file', 'missing.file'))
            return return_code

    source = sources[spec['source']]
    filename = os.path.basename(in_file)
    file_ext = filename.split('.')[-1]

    con = None
    cur = None
    file = None
    wb = None
    try:
        # normalize the spec
        if isinstance(spec.get('insert_actions'), str):
            spec['insert_actions'] = [spec['insert_actions']]
        if spec.get('insert_data') and not isinstance(spec['insert_data'], (list, tuple)):
            spec['insert_data'] = [spec['insert_data']]
        if isinstance(spec.get('validate_actions'), str):
            spec['validate_actions'] = [spec['validate_actions']]
        if isinstance(spec.get('process_actions'), str):
            spec['process_actions'] = [spec['process_actions']]

        # validate the spec
        assert file_ext in ('csv', 'xlsx', 'json', 'zip') or spec.get('pass_lines', False), \
            f"Bad file extension \"{file_ext}\" in spec \"{spec_name}\""
        assert sources.get(spec['source']), \
            f"Source \"{spec['source']}\" not defined, spec \"{spec_name}\""
        assert file_ext != 'json' or spec.get('insert_data'), \
            f"Missing \"insert_data\" in spec \"{spec_name}\""
        assert all(isinstance(i, str) for i in spec.get('insert_actions', [])), \
            f"Bad \"insert_actions\" in spec \"{spec_name}\""
        assert all(isinstance(i, str) for i in spec.get('validate_actions', [])), \
            f"Bad \"validate_actions\" in spec \"{spec_name}\""
        assert all(isinstance(i, str) for i in spec.get('process_actions', [])), \
            f"Bad \"process_actions\" in spec \"{spec_name}\""
        assert spec.get('insert_actions') is None or \
            len(spec.get('insert_actions', [])) == len(spec.get('insert_data', [])), \
            f"\"insert_actions\" and \"insert_data\" do not match in spec \"{spec_name}\""
        assert not args.arg or (
            isinstance(args.arg, list) 
            and isinstance(spec.get('bind_args'), dict) 
            and len(args.arg) == len(spec['bind_args'])
            ), f"Command line args and \"bind_args\" do not match, spec \"{spec_name}\""
        load_args = args.arg or spec.get('args', [])
        assert not load_args or 1 <= len(load_args) <= 9, \
            f"Expected 1 to 9 load args, got {len(load_args)}, spec \"{spec_name}\""
        assert all(a is not None for a in load_args), \
            f"Expected specific load args, got None in spec \"{spec_name}\""

        # find files to load
        all_files = []
        recent_files = []
        latest_mtime = stat[spec_name]['mtime']
        for file_name in sorted(glob.glob(in_file)):
            all_files.append(file_name)
            file_mtime = os.stat(file_name).st_mtime
            if file_mtime > stat[spec_name]['mtime']:
                recent_files.append(file_name)
            latest_mtime = max(file_mtime, latest_mtime)

        if (not args.force and not spec.get('force') and not recent_files) or not all_files:
            logger.info("%s - No files to load: %s", spec_name, input_file)
            return return_code

        if args.force or spec.get('force'):
            target_files = all_files
        else:
            target_files = recent_files

        # 1) load data from file(s) into database
        logger.debug("Loading %s, %s", spec_name, in_file)

        con = connection(spec['source'])

        # Initialize/Setup stuff related to this spec.
        if spec.get('setup'):
            logger.debug('-- spec setup')
            exec_sql(con, spec['setup'])

        cur = con.cursor()
        count = 0
        idata = []
        icount = []
        iload = None
        istmt = []
        for ifile in target_files:

            if file_ext == 'zip':
                # unzip if zipfile contains the only file that meets the requirements
                import zipfile
                with zipfile.ZipFile(ifile) as zf:
                    inner_file = zf.namelist()
                    assert len(inner_file) == 1, \
                        f"More than 1 member in file {ifile}"
                    inner_file = inner_file[0]
                    assert os.path.basename(inner_file) == inner_file, \
                        f"Zip file member has path in file {ifile}"
                    inner_name, inner_ext = inner_file.rsplit('.', 1)
                    ifile_path, ifile_name = os.path.split(ifile)
                    assert ifile_name.rsplit('.', 1)[0] in (inner_file, inner_name), \
                        f"Zip file member name is inconsistent with file name {ifile}"
                    assert inner_ext in ('csv', 'json', 'xlsx') or spec.get('pass_lines', False), \
                        f"Zip file member has bad extension \"{inner_ext}\" in file {ifile}"
                    assert inner_ext != 'json' or spec.get('insert_data'), \
                        f"Missing \"insert_data\" in spec \"{spec_name}\""
                    zf.extractall(ifile_path)
                    extracted_file = os.path.join(ifile_path, inner_file)
                if os.path.isfile(extracted_file):
                    if args.delete or spec.get('delete'):
                        os.remove(ifile)
                    ifile = extracted_file
                    in_format = inner_ext
            else:
                in_format = file_ext

            # open file for reading
            if spec.get('pass_lines', False):
                file = open(ifile, 'r', encoding=spec.get('encoding', ENCODING))
                reader = file
            elif in_format == 'csv':
                file = open(ifile, 'r', encoding=spec.get('encoding', ENCODING))
                reader = \
                    csv.reader(
                        file,
                        dialect=spec.get('csv_dialect', CSV_DIALECT),
                        delimiter=spec.get('csv_delimiter', CSV_DELIMITER)
                        #quotechar=spec.get('csv_quotechar', CSV_QUOTECHAR)
                    )
            elif in_format == 'xlsx':
                wb = load_workbook(filename=ifile, read_only=True)
                #reader = wb.worksheets[0]
                reader = wb.worksheets[0].values
            elif in_format == 'json':
                file = open(ifile, 'r', encoding=spec.get('encoding', ENCODING))
                reader = json.load(file)
                assert isinstance(reader, list), f"Bad json file {ifile}"

            # load data from file
            line_no = 0
            for row in reader:

                # create header in table ida
                if not iload:
                    iload = IDA_INSERT_HEADER[source['database']](cur, USER_ID, filename, spec_name, load_args or [None])
                    con.commit()

                count += 1
                line_no += 1
                if line_no <= spec.get('skip_lines', 0):
                    continue

                # prepare insert statements and data to insert
                for n, func in enumerate(spec.get('insert_data', [None])):
                    if len(idata) == n:
                        idata.append([])
                        istmt.append(spec['insert_actions'][n] if spec.get('insert_actions') else None)
                        if istmt[-1]:
                            logger.debug("-- stmt #%s\n\n%s\n", n, istmt[-1].strip())
                        icount.append(0)
                    insert_data = \
                        func(row) if func and func.__code__.co_argcount == 1 else \
                        func(line_no, row) if func and func.__code__.co_argcount == 2 else \
                        func(iload, count, row) if func and func.__code__.co_argcount == 3 else \
                        [row] if spec.get('pass_lines', False) else \
                        row
                    if not insert_data:
                        # insert no row
                        pass
                    elif isinstance(insert_data, (list, tuple)) and not isinstance(insert_data[0], (list, tuple)):
                        # insert a row
                        if spec.get('insert_actions') and spec['insert_actions'][n]:
                            idata[n].append(insert_data)
                        else:
                            idata[n].append((iload, count, *insert_data))
                            if not istmt[n] and idata[n][-1]:
                                istmt[n] = IDA_BUILD_INSERT_ROW[source['database']](idata[n][-1])
                                logger.debug("-- stmt #%s\n\n%s\n", n, istmt[n].strip())
                    elif isinstance(insert_data, (list, tuple)) and isinstance(insert_data[0], (list, tuple)):
                        # insert many rows
                        if spec.get('insert_actions') and spec['insert_actions'][n]:
                            idata[n].extend(insert_data)
                        else:
                            idata[n].extend([(iload, count, n, i+1, *irow) for i, irow in enumerate(insert_data)])
                            if not istmt[n] and idata[n][-1]:
                                istmt[n] = IDA_BUILD_INSERT_ROWS[source['database']](idata[n][-1])
                                logger.debug("-- stmt #%s\n\n%s\n", n, istmt[n].strip())

                # insert prepared data
                for n in range(len(idata)):
                    if len(idata[n]) >= BATCH_SIZE:
                        IDA_INSERT_MANY_ROWS[source['database']](cur, istmt[n], idata[n])
                        icount[n] += len(idata[n])
                        idata[n].clear()

            if in_format in ('csv', 'json') or spec.get('pass_lines', False):
                file.close()
            elif in_format == 'xlsx':
                wb.close()

            # insert the rest of prepared data before removing the file
            for n in range(len(idata)):
                if idata[n]:
                    IDA_INSERT_MANY_ROWS[source['database']](cur, istmt[n], idata[n])
                    icount[n] += len(idata[n])
                    idata[n].clear()
            con.commit()

            if args.delete or spec.get('delete') or file_ext == 'zip':
                os.remove(ifile)
            logger.info("%s", ifile)

        # insert the rest of prepared data
        #for n in range(len(idata)):
        #    if idata[n]:
        #        IDA_INSERT_MANY_ROWS[source['database']](cur, istmt[n], idata[n])
        #        icount[n] += len(idata[n])
        logger.info("Loaded %s of %s rows with iload=%s", str(icount).strip('[]'), count - spec.get('skip_lines', 0), iload)

        # 2) validate loaded data

        err_count = 0
        if spec.get('validate_actions'):

            logger.debug('-- validate')
            for stmt in spec['validate_actions']:
                logger.debug('\n\n%s\n', stmt.strip())
                cur.execute(stmt, (iload,))
            con.commit()

            if spec.get('insert_actions') is None:
                cur.execute(IDA_SELECT_ISTAT_2_COUNT[source['database']], (iload,))
                err_count = cur.fetchone()
                err_count = err_count[0] if err_count else 0
                if err_count > 0:
                    logger.info("Validation found %s bad lines.", err_count)
                else:
                    logger.info("Validation succeded")
            else:
                cur.execute(IDA_SELECT_ISTAT_IMESS[source['database']], (iload,))
                row = cur.fetchone()
                err_count = 1 if row and row[0] == 2 else 0
                if err_count > 0:
                    logger.info("Validation failed with error: %s", row[1])
                else:
                    logger.info("Validation succeded")

        # 3) process loaded data

        if err_count == 0 and spec.get('process_actions'):

            logger.debug('-- process')
            for stmt in spec['process_actions']:
                logger.debug('\n\n%s\n', stmt.strip())
                cur.execute(stmt, (iload,))
            con.commit()

            if spec.get('insert_actions') is None:
                cur.execute(IDA_SELECT_ISTAT_2_COUNT[source['database']], (iload,))
                err_count = cur.fetchone()
                err_count = err_count[0] if err_count else 0
                if err_count > 0:
                    logger.info("Processing found %s bad lines.", err_count)
                else:
                    logger.info("Processing succeeded")
            else:
                cur.execute(IDA_SELECT_ISTAT_IMESS[source['database']], (iload,))
                row = cur.fetchone()
                err_count = 1 if row and row[0] == 2 else 0
                if err_count > 0:
                    logger.info("Processing failed with error: %s", row[1])
                else:
                    logger.info("Processing succeeded")

        # mark as failed or succeeded
        cur.execute(IDA_UPDATE_ISTAT[source['database']], (2 if err_count > 0 else 1, iload,))
        con.commit()

        # delete old loads from ida preserving only last N loads
        #logger.debug('-- keep ida fit')
        #logger.debug('\n\n%s\n', IDA_DELETE_OLD_LOADS[source['database']].strip())
        cur.execute(
            IDA_DELETE_OLD_LOADS[source['database']],
            (spec_name, spec.get('preserve_n_loads', PRESERVE_N_LOADS))
        )
        con.commit()

        # Finalize/Release stuff related to this spec.
        if spec.get('upset'):
            logger.debug('-- spec upset')
            exec_sql(con, spec['upset'])
        con.commit()

        # set stat data no earlier than all files are successfully processed
        if recent_files:
            stat[spec_name]['mtime'] = latest_mtime
    except:
        logger.exception('EXCEPT')
        if sources[spec['source']].get('con'):
            sources[spec['source']]['con'].rollback()
        return_code = 1
    finally:
        if file:
            file.close()
        if wb:
            wb.close()
    return return_code


def main():
    logger.info("-- start %s", ' '.join(sys.argv))

    error_count = 0
    _ts = datetime.now().strftime('%Y%m%d%H%M%S')
    trace(_ts, 0)

    if os.path.isfile(STAT_FILE):
        with open(STAT_FILE, encoding='UTF-8') as f:
            stat = json.load(f)
    else:
        stat = dict()

    for spec_name, spec in specs.items():
        if spec_name not in stat:
            stat[spec_name] = {'mtime': 0}
        if SPEC in (spec_name, 'all', *spec.get('tags', [])):
            spec['source'] = spec.get('source', getattr(cfg, 'SOURCE', None))
            if spec['source'] is None:
                logger.error('Skipping spec "%s" with no source', spec_name)
                error_count += 1
                continue
            src = sources[spec['source']]
            if src.get('lib') is None:
                if src['database'] == 'oracle':
                    # import cx_Oracle
                    # src['lib'] = cx_Oracle
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
                src['setup'] = IDA_SETUP.get(src['database'], []) + src.get('setup', [])
            error_count += process(spec_name, spec, args.in_file, stat)

    for src in sources.values():
        if src.get('con') is not None:
            if src.get('upset'):
                logger.debug("-- upset")
                exec_sql(src['con'], src.get('upset'))
            src['con'].close()
            src['con'] = None

    stat = {k: v for k, v in stat.items() if k in cfg.specs}
    with open(STAT_FILE, 'w', encoding='UTF-8') as f:
        f.write(json.dumps(stat))

    trace(_ts, 1 if error_count == 0 else 2)
    logger.info("-- done %s", f" WITH {error_count} ERRORS" if error_count else '')
    sys.exit(error_count)


if __name__ == '__main__':
    main()
