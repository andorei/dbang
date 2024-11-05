#!/usr/bin/env python3

import os
import sys
import argparse
import logging
import decimal as dec
from datetime import date, datetime
from math import ceil
import re

from jinja2 import Template


VERSION = '0.3'

parser = argparse.ArgumentParser(
    description="Detect discrepancies in two databases as specified in cfg-file specs.",
    epilog="Thanks for using %(prog)s!"
)

parser.add_argument("-v", "--version", action="version", version="%(prog)s " + VERSION)
parser.add_argument("cfg_file", help="cfg-file name")
parser.add_argument("spec", nargs="?", default="all", help="spec name, defaults to \"all\"")
parser.add_argument("-1", "--one", action="store_true", help="find discrepancies and store them")
parser.add_argument("-2", "--two", action="store_true", help="find discrepancies and intersect them with the stored")

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

# keep data in ddiff_ table after test completion
DDIFF_KEEP = False
# number of rows to fetch with one fetch
ONE_FETCH_ROWS = 5000
# number of fetched rows at which we go no futher
MAX_FETCH_ROWS = 1000000
# number of mismatchs at which we go no deeper
MAX_DISCREPANCIES = 1000

DDIFF_SETUP = {
    "mysql": [
        """
create table if not exists ddiff_(
    cfg text,
    spec text,
    run bigint,
    source text,
    c1 text, c2 text, c3 text, c4 text, c5 text, c6 text, c7 text, c8 text, c9 text, c10 text,
    c11 text, c12 text, c13 text, c14 text, c15 text, c16 text, c17 text, c18 text, c19 text, c20 text,
    c21 text, c22 text, c23 text, c24 text, c25 text, c26 text, c27 text, c28 text, c29 text, c30 text,
    c31 text, c32 text, c33 text, c34 text, c35 text, c36 text, c37 text, c38 text, c39 text, c40 text,
    c41 text, c42 text, c43 text, c44 text, c45 text, c46 text, c47 text, c48 text, c49 text, c50 text
)
        """,
        """
create table if not exists ddiff_diffs_(
    cfg text,
    spec text,
    run bigint,
    c1 text, c2 text, c3 text, c4 text, c5 text, c6 text, c7 text, c8 text, c9 text, c10 text,
    c11 text, c12 text, c13 text, c14 text, c15 text, c16 text, c17 text, c18 text, c19 text, c20 text,
    c21 text, c22 text, c23 text, c24 text, c25 text, c26 text, c27 text, c28 text, c29 text, c30 text,
    c31 text, c32 text, c33 text, c34 text, c35 text, c36 text, c37 text, c38 text, c39 text, c40 text,
    c41 text, c42 text, c43 text, c44 text, c45 text, c46 text, c47 text, c48 text, c49 text, c50 text,
    c51 text, c52 text, c53 text, c54 text, c55 text, c56 text, c57 text, c58 text, c59 text, c60 text,
    c61 text, c62 text, c63 text, c64 text, c65 text, c66 text, c67 text, c68 text, c69 text, c70 text,
    c71 text, c72 text, c73 text, c74 text, c75 text, c76 text, c77 text, c78 text, c79 text, c80 text,
    c81 text, c82 text, c83 text, c84 text, c85 text, c86 text, c87 text, c88 text, c89 text, c90 text,
    c91 text, c92 text, c93 text, c94 text, c95 text, c96 text, c97 text, c98 text, c99 text, c100 text
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
    from all_tables
    where table_name in ('DDIFF_')
    ;
    if 0 = table_exists then
        execute immediate '
            create table ddiff_(
                cfg varchar2(4000),
                spec varchar2(4000),
                run number,
                source varchar2(4000),
                c1 varchar2(4000), c2 varchar2(4000), c3 varchar2(4000), c4 varchar2(4000), c5 varchar2(4000),
                c6 varchar2(4000), c7 varchar2(4000), c8 varchar2(4000), c9 varchar2(4000), c10 varchar2(4000),
                c11 varchar2(4000), c12 varchar2(4000), c13 varchar2(4000), c14 varchar2(4000), c15 varchar2(4000),
                c16 varchar2(4000), c17 varchar2(4000), c18 varchar2(4000), c19 varchar2(4000), c20 varchar2(4000),
                c21 varchar2(4000), c22 varchar2(4000), c23 varchar2(4000), c24 varchar2(4000), c25 varchar2(4000),
                c26 varchar2(4000), c27 varchar2(4000), c28 varchar2(4000), c29 varchar2(4000), c30 varchar2(4000),
                c31 varchar2(4000), c32 varchar2(4000), c33 varchar2(4000), c34 varchar2(4000), c35 varchar2(4000),
                c36 varchar2(4000), c37 varchar2(4000), c38 varchar2(4000), c39 varchar2(4000), c40 varchar2(4000),
                c41 varchar2(4000), c42 varchar2(4000), c43 varchar2(4000), c44 varchar2(4000), c45 varchar2(4000),
                c46 varchar2(4000), c47 varchar2(4000), c48 varchar2(4000), c49 varchar2(4000), c50 varchar2(4000)
            )';
    end if;
end;
        """,
        """
declare
    table_exists pls_integer;
begin
    select count(*)
    into table_exists
    from all_tables
    where table_name in ('DDIFF_DIFFS_')
    ;
    if 0 = table_exists then
        execute immediate '
            create table ddiff_diffs_(
                cfg varchar2(4000),
                spec varchar2(4000),
                run number,
                c1 varchar2(4000), c2 varchar2(4000), c3 varchar2(4000), c4 varchar2(4000), c5 varchar2(4000),
                c6 varchar2(4000), c7 varchar2(4000), c8 varchar2(4000), c9 varchar2(4000), c10 varchar2(4000),
                c11 varchar2(4000), c12 varchar2(4000), c13 varchar2(4000), c14 varchar2(4000), c15 varchar2(4000),
                c16 varchar2(4000), c17 varchar2(4000), c18 varchar2(4000), c19 varchar2(4000), c20 varchar2(4000),
                c21 varchar2(4000), c22 varchar2(4000), c23 varchar2(4000), c24 varchar2(4000), c25 varchar2(4000),
                c26 varchar2(4000), c27 varchar2(4000), c28 varchar2(4000), c29 varchar2(4000), c30 varchar2(4000),
                c31 varchar2(4000), c32 varchar2(4000), c33 varchar2(4000), c34 varchar2(4000), c35 varchar2(4000),
                c36 varchar2(4000), c37 varchar2(4000), c38 varchar2(4000), c39 varchar2(4000), c40 varchar2(4000),
                c41 varchar2(4000), c42 varchar2(4000), c43 varchar2(4000), c44 varchar2(4000), c45 varchar2(4000),
                c46 varchar2(4000), c47 varchar2(4000), c48 varchar2(4000), c49 varchar2(4000), c50 varchar2(4000),
                c51 varchar2(4000), c52 varchar2(4000), c53 varchar2(4000), c54 varchar2(4000), c55 varchar2(4000),
                c56 varchar2(4000), c57 varchar2(4000), c58 varchar2(4000), c59 varchar2(4000), c60 varchar2(4000),
                c61 varchar2(4000), c62 varchar2(4000), c63 varchar2(4000), c64 varchar2(4000), c65 varchar2(4000),
                c66 varchar2(4000), c67 varchar2(4000), c68 varchar2(4000), c69 varchar2(4000), c70 varchar2(4000),
                c71 varchar2(4000), c72 varchar2(4000), c73 varchar2(4000), c74 varchar2(4000), c75 varchar2(4000),
                c76 varchar2(4000), c77 varchar2(4000), c78 varchar2(4000), c79 varchar2(4000), c80 varchar2(4000),
                c81 varchar2(4000), c82 varchar2(4000), c83 varchar2(4000), c84 varchar2(4000), c85 varchar2(4000),
                c86 varchar2(4000), c87 varchar2(4000), c88 varchar2(4000), c89 varchar2(4000), c90 varchar2(4000),
                c91 varchar2(4000), c92 varchar2(4000), c93 varchar2(4000), c94 varchar2(4000), c95 varchar2(4000),
                c96 varchar2(4000), c97 varchar2(4000), c98 varchar2(4000), c99 varchar2(4000), c100 varchar2(4000)
            )';
    end if;
end;
        """
    ],
    "postgres": [
        """
create table if not exists ddiff_(
    cfg text,
    spec text,
    run bigint,
    source text,
    c1 text, c2 text, c3 text, c4 text, c5 text, c6 text, c7 text, c8 text, c9 text, c10 text,
    c11 text, c12 text, c13 text, c14 text, c15 text, c16 text, c17 text, c18 text, c19 text, c20 text,
    c21 text, c22 text, c23 text, c24 text, c25 text, c26 text, c27 text, c28 text, c29 text, c30 text,
    c31 text, c32 text, c33 text, c34 text, c35 text, c36 text, c37 text, c38 text, c39 text, c40 text,
    c41 text, c42 text, c43 text, c44 text, c45 text, c46 text, c47 text, c48 text, c49 text, c50 text
)
        """,
        """
create table if not exists ddiff_diffs_(
    cfg text,
    spec text,
    run bigint,
    c1 text, c2 text, c3 text, c4 text, c5 text, c6 text, c7 text, c8 text, c9 text, c10 text,
    c11 text, c12 text, c13 text, c14 text, c15 text, c16 text, c17 text, c18 text, c19 text, c20 text,
    c21 text, c22 text, c23 text, c24 text, c25 text, c26 text, c27 text, c28 text, c29 text, c30 text,
    c31 text, c32 text, c33 text, c34 text, c35 text, c36 text, c37 text, c38 text, c39 text, c40 text,
    c41 text, c42 text, c43 text, c44 text, c45 text, c46 text, c47 text, c48 text, c49 text, c50 text,
    c51 text, c52 text, c53 text, c54 text, c55 text, c56 text, c57 text, c58 text, c59 text, c60 text,
    c61 text, c62 text, c63 text, c64 text, c65 text, c66 text, c67 text, c68 text, c69 text, c70 text,
    c71 text, c72 text, c73 text, c74 text, c75 text, c76 text, c77 text, c78 text, c79 text, c80 text,
    c81 text, c82 text, c83 text, c84 text, c85 text, c86 text, c87 text, c88 text, c89 text, c90 text,
    c91 text, c92 text, c93 text, c94 text, c95 text, c96 text, c97 text, c98 text, c99 text, c100 text
)
        """,
    ],
    "sqlite": [
        """
create table if not exists ddiff_(
    cfg text,
    spec text,
    run bigint,
    source text,
    c1 text, c2 text, c3 text, c4 text, c5 text, c6 text, c7 text, c8 text, c9 text, c10 text,
    c11 text, c12 text, c13 text, c14 text, c15 text, c16 text, c17 text, c18 text, c19 text, c20 text,
    c21 text, c22 text, c23 text, c24 text, c25 text, c26 text, c27 text, c28 text, c29 text, c30 text,
    c31 text, c32 text, c33 text, c34 text, c35 text, c36 text, c37 text, c38 text, c39 text, c40 text,
    c41 text, c42 text, c43 text, c44 text, c45 text, c46 text, c47 text, c48 text, c49 text, c50 text
)
        """,
        """
create table if not exists ddiff_diffs_(
    cfg text,
    spec text,
    run bigint,
    c1 text, c2 text, c3 text, c4 text, c5 text, c6 text, c7 text, c8 text, c9 text, c10 text,
    c11 text, c12 text, c13 text, c14 text, c15 text, c16 text, c17 text, c18 text, c19 text, c20 text,
    c21 text, c22 text, c23 text, c24 text, c25 text, c26 text, c27 text, c28 text, c29 text, c30 text,
    c31 text, c32 text, c33 text, c34 text, c35 text, c36 text, c37 text, c38 text, c39 text, c40 text,
    c41 text, c42 text, c43 text, c44 text, c45 text, c46 text, c47 text, c48 text, c49 text, c50 text,
    c51 text, c52 text, c53 text, c54 text, c55 text, c56 text, c57 text, c58 text, c59 text, c60 text,
    c61 text, c62 text, c63 text, c64 text, c65 text, c66 text, c67 text, c68 text, c69 text, c70 text,
    c71 text, c72 text, c73 text, c74 text, c75 text, c76 text, c77 text, c78 text, c79 text, c80 text,
    c81 text, c82 text, c83 text, c84 text, c85 text, c86 text, c87 text, c88 text, c89 text, c90 text,
    c91 text, c92 text, c93 text, c94 text, c95 text, c96 text, c97 text, c98 text, c99 text, c100 text
)
        """
    ],
}

# default sqlite database for ddiff tables
SQLITE_SOURCE = {
    "database": "sqlite",
    "con_string": os.path.join(os.environ.get('HOMEPATH', os.environ.get('HOME')), '.dbang', 'ddiff.db')
}
# database for ddiff tables
DDIFF_SOURCE = getattr(cfg, 'DDIFF_SOURCE', SQLITE_SOURCE)
DDIFF_SOURCE['setup'] = DDIFF_SETUP[DDIFF_SOURCE['database']] + DDIFF_SOURCE.get('setup', [])

INSERT_RESULTS = """
insert into ddiff_ (
    cfg,spec,run,source,{% for i, col in (c['pk'] + c['cols']) %}c{{loop.index}}{{"," if not loop.last}}{% endfor %})
values (
{%- if database == 'sqlite' %}
    ?,?,?,?,{% for i, col in (c['pk'] + c['cols']) %}?{{"," if not loop.last}}{% endfor %}
{%- elif database == 'postgres' %}
    %s,%s,%s,%s,{% for i, col in (c['pk'] + c['cols']) %}%s{{"," if not loop.last}}{% endfor %}
{%- elif database == 'mysql' %}
    %s,%s,%s,%s,{% for i, col in (c['pk'] + c['cols']) %}%s{{"," if not loop.last}}{% endfor %}
{%- elif database == 'oracle' %}
    :cfg,:spec,:run,:source,{% for i, col in (c['pk'] + c['cols']) %}:{{i}}{{"," if not loop.last}}{% endfor %}
{%- endif %}
)
"""
SELECT_RESULTS = """
with d1 as (
    select {% for col in (c['pk'] + c['cols']) %}c{{loop.index}}{{"," if not loop.last}}{% endfor %}
    from ddiff_
    where cfg='{{cfg}}' and spec = '{{spec}}' and run = {{run[0]}} and source = '{{c['sources'][0]}}'
    {% if database == 'oracle' %}minus{% else %}except{% endif%}
    select {% for col in (c['pk'] + c['cols']) %}c{{loop.index}}{{"," if not loop.last}}{% endfor %}
    from ddiff_
    where cfg='{{cfg}}' and spec = '{{spec}}' and run = {{run[0]}} and source = '{{c['sources'][1]}}'
), d2 as (
    select {% for col in (c['pk'] + c['cols']) %}c{{loop.index}}{{"," if not loop.last}}{% endfor %}
    from ddiff_
    where cfg='{{cfg}}' and spec = '{{spec}}' and run = {{run[0]}} and source = '{{c['sources'][1]}}'
    {% if database == 'oracle' %}minus{% else %}except{% endif%}
    select {% for col in (c['pk'] + c['cols']) %}c{{loop.index}}{{"," if not loop.last}}{% endfor %}
    from ddiff_
    where cfg='{{cfg}}' and spec = '{{spec}}' and run = {{run[0]}} and source = '{{c['sources'][0]}}'
)
{%- if op == '<' or op == '=' %}
select
    {%- for i, col in c['pk'] %}
    coalesce(d1.c{{i}}, d2.c{{i}}) "{{col}}"{{"," if not loop.last or c['cols']}}
    {%- endfor %}
    {%- for i, col in c['cols'] %}
    d1.c{{i}} "DB1 {{col}}", d2.c{{i}} "DB2 {{col}}"{{"," if not loop.last}}
    {%- endfor %}
from d1 left join d2 on {% for i, col in c['pk'] %} d1.c{{i}} = d2.c{{i}}{{" and " if not loop.last}}{% endfor %}
{%- endif %}
{%- if op == '=' %}
union
{%- endif %}
{%- if op == '>' or op == '=' %}
select
    {%- for i, col in c['pk'] %}
    coalesce(d1.c{{i}}, d2.c{{i}}) "{{col}}"{{"," if not loop.last or c['cols']}}
    {%- endfor %}
    {%- for i, col in c['cols'] %}
    d1.c{{i}} "DB1 {{col}}", d2.c{{i}} "DB2 {{col}}"{{"," if not loop.last}}
    {%- endfor %}
from d2 left join d1 on {% for i, col in c['pk'] %} d1.c{{i}} = d2.c{{i}}{{" and " if not loop.last}}{% endfor %}
{%- endif %}
order by {% for i, col in c['pk'] %}{{loop.index}}{{"," if not loop.last}}{% endfor %}
"""
INSERT_DIFFS = """
insert into ddiff_diffs_ (
    cfg,spec,run,{% for i, col in (c['pk'] + c['cols'] + c['cols']) %}c{{loop.index}}{{"," if not loop.last}}{% endfor %})
values (
{%- if database == 'sqlite' %}
    ?,?,?,{% for i, col in (c['pk'] + c['cols'] + c['cols']) %}?{{"," if not loop.last}}{% endfor %}
{%- elif database == 'postgres' %}
    %s,%s,%s,{% for i, col in (c['pk'] + c['cols'] + c['cols']) %}%s{{"," if not loop.last}}{% endfor %}
{%- elif database == 'mysql' %}
    %s,%s,%s,{% for i, col in (c['pk'] + c['cols'] + c['cols']) %}%s{{"," if not loop.last}}{% endfor %}
{%- elif database == 'oracle' %}
    :cfg,:spec,:run,{% for i, col in (c['pk'] + c['cols'] + c['cols']) %}:{{i}}{{"," if not loop.last}}{% endfor %}
{%- endif %}
)
"""
SELECT_DIFFS = """
with t1 as (
    select {% for i in pk_nums %}c{{i}},{% endfor %}
        {% for i in col_nums %}case when c{{i}} != c{{i+1}} then c{{i}}||c{{i+1}} when c{{i}} = c{{i+1}} then null else 'x' end c{{i}}{{"," if not loop.last}}{% endfor %}
    from ddiff_diffs_
    where cfg = '{{cfg}}' and spec = '{{spec}}' and run = (
            select max(run) from ddiff_diffs_ where cfg='{{cfg}}' and spec='{{spec}}' and run != {{run[0]}}
        )
), t2 as (
    select {% for i in pk_nums %}c{{i}},{% endfor %}
        {% for i in col_nums %}case when c{{i}} != c{{i+1}} then c{{i}}||c{{i+1}} when c{{i}} = c{{i+1}} then null else 'x' end c{{i}}{{"," if not loop.last}}{% endfor %}
    from ddiff_diffs_
    where cfg = '{{cfg}}' and spec = '{{spec}}' and run = {{run[0]}}
), tt as (
    select {% for i in pk_nums %}t1.c{{i}}{{"," if not loop.last}}{% endfor %}
    from t1
        join t2 on ({% for i in pk_nums %}t1.c{{i}}{{"," if not loop.last}}{% endfor %}) = ({% for i in pk_nums %}t2.c{{i}}{{"," if not loop.last}}{% endfor %})
    where {% for i in col_nums %}t1.c{{i}} = t2.c{{i}}{{" or " if not loop.last}}{% endfor %}
)
select {% for i in pk_nums %}dd.c{{i}},{% endfor %}{% for i in col_nums %}dd.c{{i}},dd.c{{i+1}}{{"," if not loop.last}}{% endfor %}
from ddiff_diffs_ dd 
    join tt on ({% for i in pk_nums %}dd.c{{i}}{{"," if not loop.last}}{% endfor %}) = ({% for i in pk_nums %}tt.c{{i}}{{"," if not loop.last}}{% endfor %})
where cfg = '{{cfg}}' and spec = '{{spec}}' and run = {{run[0]}}
order by {% for i in pk_nums %}{{loop.index}}{{"," if not loop.last}}{% endfor %}
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
<title>Data Discrepancies Report ({{cfg}}): {{test|escape}}</title>
</head>
<body>
<h2><a href="{{cfg}}.html">Data Discrepancies Report ({{cfg}})</a>: {{test}}</h2>
{%- if rows %}
{%- for row in rows %}
{%- if loop.first %}
{%- if doc %}
<p>{{doc}}</p>
{%- endif %}
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
        <td>{{col[0] if col[0] is not none else '[NULL]'}}</td><td>{{col[1] if col[1] is not none else '[NULL]'}}</td>
        {%- else%}
        <td style="color:red;">{{col[0] if col[0] is not none else '[NULL]'}}</td><td style="color:red;">{{col[1] if col[1] is not none else '[NULL]'}}</td>
        {%- endif %}
    {%- else %}
        <td>{{(col if col is not none else '[NULL]')|escape}}</td>
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
<tr><th>Test</th><th>DB1</th><th>DB2</th><th>Result</th><th>Warning</th><th>Doc</th></tr>
{%- endif %}
<tr>
    <td>{{row[0]|escape}}</td>
    <td>{{row[3]|escape}}</td>
    <td>{{row[4]|escape}}</td>
    <td>{% if row[1] == 0 %}<span style="color:green;">Success.</span>{% elif row[1] == -1 %}Failed to run.{% else %}<a href="{{cfg}}_{{row[0]}}.html" style="color:red;">Found {{row[1]}} discrepancies.</a>{% endif %}</td>
    <td>{% if row[2] %}{% for warn in row[2] %}{{warn|escape}}{{"<br/>" if not loop.last}}{% endfor %}{% endif %}</td>
    <td>{% if row[5] %}{{row[5]|escape}}{% endif %}</td>
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

select_tpl = Template(SELECT_RESULTS)
insert_tpl = Template(INSERT_RESULTS)
select_diffs_tpl = Template(SELECT_DIFFS)
insert_diffs_tpl = Template(INSERT_DIFFS)
test_report_tpl = Template(TEST_REPORT)
run_report_tpl = Template(RUN_REPORT)


def exec_sql(con, sql):
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
    if isinstance(src, str):
        source = sources[src]
    elif isinstance(src, dict):
        source = src
    if not source.get('con'):
        if source.get('con_string'):
            source['con'] = \
                source['lib'].connect(source['con_string'], **source.get('con_kwargs', dict()))
        else:
            source['con'] = source['lib'].connect(**source['con_kwargs'])
        if source['database'] == 'oracle':
            # see https://cx-oracle.readthedocs.io/en/latest/user_guide/sql_execution.html#fetched-number-precision.
            def number_to_decimal(cursor, name, default_type, size, precision, scale):
                if default_type == source['lib'].DB_TYPE_NUMBER:
                    return cursor.var(dec.Decimal, arraysize=cursor.arraysize)
            source['con'].outputtypehandler = number_to_decimal
        if source.get('setup'):
            logger.debug('-- setup')
            exec_sql(source['con'], source['setup'])
    return source['con']


def pump(run, spec_name, spec, con0, argrows, source_idx):
    con = connection(spec['sources'][source_idx])
    cur = con.cursor()
    query = spec['queries'][source_idx]

    cur0 = con0.cursor()
    rowcount = 0
    query_tpl = None

    # to keep the query reasonably short we should split long argrows lists
    # into sereval shorter lists and execute several short selects/inserts
    if argrows:
        parts = ceil(len(argrows) / 200)
    else:
        parts = 1

    logger.debug("-- select %s dataset into ddiff_: %s time(s)", spec['sources'][source_idx], parts)

    for part in range(parts):
        if argrows:
            if query_tpl is None:
                query_tpl = Template(query)
            query = query_tpl.render(argrows=argrows[part*200:part*200+200])
            logger.debug('\n\n%s\n', query.strip())
        else:
            if part == 0:
                logger.debug('\n\n%s\n', query.strip())
        cur.execute(query)

        if spec.get('cols') is None:
            spec['cols'] = [(i + 1, d[0].lower()) for i, d in enumerate(cur.description) if d[0].lower() not in spec['pk']]
            spec['pk'] = [(i + 1, d[0].lower()) for i, d in enumerate(cur.description) if d[0].lower() in spec['pk']]
            spec['insert'] = insert_tpl.render(c=spec, database=DDIFF_SOURCE['database'])
            logger.debug('\n\n%s\n', spec['insert'].strip())

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
                [(CFG_MODULE, spec_name, run[0], spec['sources'][source_idx]) + row for row in res]
            )
    cur.close()
    cur0.close()
    return rowcount


def process(run, spec_name, spec, con0, argrows):
    """
    Process spec from config-file.
    """
    return_code = 0
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
            and spec.get('op', '=').__class__ == str
            and spec.get('op', '=') in ('<', '>', '=')
            ), f"Bad spec {spec_name}"

        if spec.get('cols') is None:
            logger.info("test %s; DB1 = %s, DB2 = %s", spec_name, spec['sources'][0], spec['sources'][1])
            specs[spec_name]['warnings'] = []
            specs[spec_name]['safe_name'] = re.sub(r'[^\w. \-()\[\]]', '_', spec_name).rstrip('. ').lstrip()

        we_have_1st_pass_diffs = False
        if args.two:
            # Check if we have discrepancies from the first pass.
            cur0 = con0.cursor()
            cur0.execute(f"select count(*) from ddiff_diffs_ where cfg='{CFG_MODULE}' and spec='{spec_name}'")
            we_have_1st_pass_diffs = (cur0.fetchone()[0] > 0)

        rows = []
        if not args.two or we_have_1st_pass_diffs:
            # Get 1st and 2nd query results and insert them into ddiff_ table.
            rowcount1 = pump(run, spec_name, spec, con0, argrows, 0)
            rowcount2 = pump(run, spec_name, spec, con0, argrows, 1)

            if MAX_FETCH_ROWS <= max(rowcount1, rowcount2):
                specs[spec_name]['warnings'].append(f"DB1: {rowcount1} rows, DB2: {rowcount2} rows.")

            # Get differences between 1st and 2nd query results.
            select = \
                select_tpl.render(
                    cfg=CFG_MODULE,
                    spec=spec_name,
                    run=run,
                    c=spec,
                    database=DDIFF_SOURCE['database'],
                    op=spec.get('op', '=')
                )
            logger.debug('-- select discrepancies from ddiff_')
            logger.debug('\n\n%s\n', select.strip())
            cur0 = con0.cursor()
            cur0.execute(select)
            rows = cur0.fetchall()

            if rows:
                if spec.get(spec_name) and len(rows) <= MAX_DISCREPANCIES * (100 if args.one or args.two else 1):
                    # Delete intermediate query results from ddiff_ table.
                    con0.rollback()
                    if not spec[spec_name].get('sources'):
                        spec[spec_name]['sources'] = spec['sources']
                    if spec.get('op') and not spec[spec_name].get('op'):
                        spec[spec_name]['op'] = spec['op']
                    process(run, spec_name, spec[spec_name], con0, rows)
                else:
                    titles=(x[0] for x in cur0.description)

                    if args.one or args.two:
                        # Store the found discrepancies in ddiff_diffs_ table.
                        insert_diffs = insert_diffs_tpl.render(c=spec, database=DDIFF_SOURCE['database'])
                        logger.debug('-- insert discrepancies into ddiff_diffs_')
                        logger.debug('\n\n%s\n', insert_diffs.strip())
                        cur0.executemany(
                            insert_diffs,
                            # cx_Oracle requires list here - not a tuple, not a generator expr.
                            [(CFG_MODULE, spec_name, run[0]) + row for row in rows]
                        )

                    if args.two:
                        # Intersect the newly found discrepancies with the stored.
                        select_diffs = \
                            select_diffs_tpl.render(
                                cfg=CFG_MODULE,
                                spec=spec_name,
                                run=run,
                                #c=spec,
                                pk_nums=[i+1 for i in range(len(spec['pk']))],
                                col_nums=[i+1+len(spec['pk']) for i in range(0, len(spec['cols']) * 2, 2)],
                                database=DDIFF_SOURCE['database'],
                            )
                        logger.debug('-- select persistent discrepancies from ddiff_diffs_')
                        logger.debug('\n\n%s\n', select_diffs.strip())
                        cur0.execute(select_diffs)
                        rows = cur0.fetchall()

                    if not args.one and rows:
                        # Generate multi-page test reports OR limit number of rows in the report
                        if spec.get(spec_name) and len(rows) > MAX_DISCREPANCIES * (100 if args.one or args.two else 1):
                            specs[spec_name]['warnings'].append(f"Found {len(rows)} discrepancies, go no deeper.")
                        cols_index = len(spec['pk'])
                        test_report = \
                            test_report_tpl.render(
                                cfg=CFG_MODULE,
                                run=run,
                                test=spec_name,
                                doc=specs[spec_name].get('doc'),
                                rows=tuple(tuple(row[:cols_index]) + tuple(x for x in zip(row[cols_index::2], row[cols_index+1::2])) for row in rows),
                                titles=titles,
                                warnings=specs[spec_name].get('warnings'),
                                sources=specs[spec_name]['sources']
                            )
                        test_report_file = OUT_FILE.format(f"{CFG_MODULE}_{spec_name}")
                        with open(test_report_file, 'w', encoding="UTF-8") as f:
                            f.write(test_report)

                    logger.info("Found %s discrepancies.", len(rows))
                    specs[spec_name]['result'] = len(rows)
            else:
                logger.info("Found %s discrepancies.", len(rows))
                specs[spec_name]['result'] = len(rows)
        else:
            logger.info("Found %s discrepancies.", len(rows))
            specs[spec_name]['result'] = len(rows)

        if not DDIFF_KEEP:
            cur0.execute("delete from ddiff_")
        con0.commit()
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
    logger.debug("args: %s", args)

    con0 = None
    for spec_name, spec in specs.items():
        if SPEC in (spec_name, 'all', *spec.get('tags', [])):
            spec['sources'] = spec.get('sources', getattr(cfg, 'SOURCES', [None, None]))
            if spec['sources'] == [None, None]:
                logger.error('Skipping spec "%s" with no sources', spec_name)
                error_count += 1
                continue
            for src in (sources[spec['sources'][0]], sources[spec['sources'][1]], DDIFF_SOURCE):
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
                        # Setup the adaptor in order to save decimals as text
                        # uniformely without trailing zeros and a trailing dot.
                        def decimal_to_text(d):
                            s = str(d)
                            # postgres decimal 0 might turn into smth like 0E-20
                            return s.rstrip('0').rstrip('.') if '.' in s else '0' if d == 0 else s
                        sqlite3.register_adapter(dec.Decimal, decimal_to_text)
                    else:
                        src['lib'] = None
            con0 = connection(DDIFF_SOURCE)
            error_count += process(run, spec_name, spec, con0, spec.get('argrows', []))

    if not args.one:
        run_results = [
            (spec['safe_name'], spec.get('result', -1), spec.get('warnings'), spec['sources'][0], spec['sources'][1], spec.get('doc'))
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

        if not DDIFF_KEEP:
            cur0 = con0.cursor()
            cur0.execute(f"delete from ddiff_diffs_ where cfg = '{CFG_MODULE}'")
            con0.commit()

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
