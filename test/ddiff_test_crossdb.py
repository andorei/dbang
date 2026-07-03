import os
import sys

from sources import sources


# See details on config file's and spec parameters in doc/ddiff.md

DEBUGGING = True
LOGGING = True
PARALLEL_WORKERS = 2

OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'out')
LOG_DIR = os.path.join(os.path.dirname(__file__), '..', 'log')


specs = {
    # mssql first
    "msmy": {
        "tags": ['mssql', 'sqlite_mysql', 'mysql'],
        "sources": ["mssql_source", "mysql_source"],
        "pk": ["code"],
        "queries": [
            """
            select 1 code, 1.0 float_, 'hello' text_, current_date date_, format(current_timestamp, 'yyyy-MM-dd HH:mm:ss') ts_
            """,
            """
            select 1 code, 1.0 float_, 'hello' text_, current_date date_, date_format(current_timestamp, '%Y-%m-%d %H:%i:%s') ts_
            """
       ]
    },
    "msor": {
        "tags": ['mssql', 'mssql_oracle', 'oracle'],
        "sources": ["mssql_source", "oracle_source"],
        "pk": ["code"],
        "queries": [
            """
            select 1 code, 1.0 float_, 'hello' text_, current_date date_, format(current_timestamp, 'yyyy-MM-dd HH:mm:ss') ts_
            """,
            """
            select 1 code, 1.0 float_, 'hello' text_, to_char(current_date, 'YYYY-MM-DD') date_, to_char(current_timestamp, 'YYYY-MM-DD HH24:MI:SS') ts_ from dual
            """
       ]
    },
    "mspg": {
        "tags": ['mssql', 'sqlite_postgresql', 'postgresql'],
        "sources": ["mssql_source", "postgresql_source"],
        "pk": ["code"],
        "queries": [
            """
            select 1 code, 1.0 float_, 'hello' text_, current_date date_, format(current_timestamp, 'yyyy-MM-dd HH:mm:ss') ts_
            """,
            """
            select 1 code, 1.0 float_, 'hello' text_, current_date date_, to_char(current_timestamp, 'YYYY-MM-DD HH24:MI:SS') ts_
            """
       ]
    },
    "msql": {
        "tags": ['mssql', 'mssql_sqlite', 'sqlite'],
        "sources": ["mssql_source", "sqlite_source"],
        "pk": ["code"],
        "queries": [
            """
            select 1 code, 1.0 float_, 'hello' text_, current_date date_, format(current_timestamp, 'yyyy-MM-dd HH:mm:ss') ts_
            """,
            """
            select 1 code, 1.0 float_, 'hello' text_, date(current_timestamp, 'localtime') date_, datetime(current_timestamp, 'localtime') ts_
            """
       ]
    },
    # mysql first
    "myor": {
        "tags": ['mysql', 'mysql_oracle', 'oracle'],
        "sources": ["mysql_source", "oracle_source"],
        "pk": ["code"],
        "queries": [
            """
            select 1 code, 1.0 float_, 'hello' text_, current_date date_, date_format(current_timestamp, '%Y-%m-%d %H:%i:%s') ts_
            """,
            """
            select 1 code, 1.0 float_, 'hello' text_, to_char(current_date, 'YYYY-MM-DD') date_, to_char(current_timestamp, 'YYYY-MM-DD HH24:MI:SS') ts_ from dual
            """
       ]
    },
    "mypg": {
        "tags": ['mysql', 'mysql_postgresql', 'postgresql'],
        "sources": ["mysql_source", "postgresql_source"],
        "pk": ["code"],
        "queries": [
            """
            select 1 code, 1.0 float_, 'hello' text_, current_date date_, date_format(current_timestamp, '%Y-%m-%d %H:%i:%s') ts_
            """,
            """
            select 1 code, 1.0 float_, 'hello' text_, current_date date_, to_char(current_timestamp, 'YYYY-MM-DD HH24:MI:SS') ts_
            """
       ]
    },
    "myql": {
        "tags": ['mysql', 'mysql_sqlite', 'sqlite'],
        "sources": ["mysql_source", "sqlite_source"],
        "pk": ["code"],
        "queries": [
            """
            select 1 code, 1.0 float_, 'hello' text_, current_date date_, date_format(current_timestamp, '%Y-%m-%d %H:%i:%s') ts_
            """,
            """
            select 1 code, 1.0 float_, 'hello' text_, date(current_timestamp, 'localtime') date_, datetime(current_timestamp, 'localtime') ts_
            """
       ]
    },
    "myms": {
        "tags": ['mysql', 'mysql_mssql', 'mssql'],
        "sources": ["mysql_source", "mssql_source"],
        "pk": ["code"],
        "queries": [
            """
            select 1 code, 1.0 float_, 'hello' text_, current_date date_, date_format(current_timestamp, '%Y-%m-%d %H:%i:%s') ts_
            """,
            """
            select 1 code, 1.0 float_, 'hello' text_, current_date date_, format(current_timestamp, 'yyyy-MM-dd HH:mm:ss') ts_
            """
       ]
    },
    # oracle first
    "ormy": {
        "tags": ['oracle', 'oracle_mysql', 'mysql'],
        "sources": ["oracle_source", "mysql_source"],
        "pk": ["code"],
        "queries": [
            """
            select 1 code, 1.0 float_, 'hello' text_, to_char(current_date, 'YYYY-MM-DD') date_, to_char(current_timestamp, 'YYYY-MM-DD HH24:MI:SS') ts_ from dual
            """,
            """
            select 1 code, 1.0 float_, 'hello' text_, current_date date_, date_format(current_timestamp, '%Y-%m-%d %H:%i:%s') ts_
            """
       ]
    },
    "orpg": {
        "tags": ['oracle', 'oracle_postgresql', 'postgresql'],
        "sources": ["oracle_source", "postgresql_source"],
        "pk": ["code"],
        "queries": [
            """
            select 1 code, 1.0 float_, 'hello' text_, to_char(current_date, 'YYYY-MM-DD') date_, to_char(current_timestamp, 'YYYY-MM-DD HH24:MI:SS') ts_ from dual
            """,
            """
            select 1 code, 1.0 float_, 'hello' text_, current_date date_, to_char(current_timestamp, 'YYYY-MM-DD HH24:MI:SS') ts_
            """
       ]
    },
    "orql": {
        "tags": ['oracle', 'oracle_sqlite', 'sqlite'],
        "sources": ["oracle_source", "sqlite_source"],
        "pk": ["code"],
        "queries": [
            """
            select 1 code, 1.0 float_, 'hello' text_, to_char(current_date, 'YYYY-MM-DD') date_, to_char(current_timestamp, 'YYYY-MM-DD HH24:MI:SS') ts_ from dual
            """,
            """
            select 1 code, 1.0 float_, 'hello' text_, date(current_timestamp, 'localtime') date_, datetime(current_timestamp, 'localtime') ts_
            """
       ]
    },
    "orms": {
        "tags": ['oracle', 'oracle_mssql', 'mssql'],
        "sources": ["oracle_source", "mssql_source"],
        "pk": ["code"],
        "queries": [
            """
            select 1 code, 1.0 float_, 'hello' text_, to_char(current_date, 'YYYY-MM-DD') date_, to_char(current_timestamp, 'YYYY-MM-DD HH24:MI:SS') ts_ from dual
            """,
            """
            select 1 code, 1.0 float_, 'hello' text_, current_date date_, format(current_timestamp, 'yyyy-MM-dd HH:mm:ss') ts_
            """
       ]
    },
    # postgresql first
    "pgmy": {
        "tags": ['postgresql', 'postgres_mysql', 'mysql'],
        "sources": ["postgresql_source", "mysql_source"],
        "pk": ["code"],
        "queries": [
            """
            select 1 code, 1.0 float_, 'hello' text_, current_date date_, to_char(current_timestamp, 'YYYY-MM-DD HH24:MI:SS') ts_
            """,
            """
            select 1 code, 1.0 float_, 'hello' text_, current_date date_, date_format(current_timestamp, '%Y-%m-%d %H:%i:%s') ts_
            """
       ]
    },
    "pgor": {
        "tags": ['postgresql', 'postgres_oracle', 'oracle'],
        "sources": ["postgresql_source", "oracle_source"],
        "pk": ["code"],
        "queries": [
            """
            select 1 code, 1.0 float_, 'hello' text_, current_date date_, to_char(current_timestamp, 'YYYY-MM-DD HH24:MI:SS') ts_
            """,
            """
            select 1 code, 1.0 float_, 'hello' text_, to_char(current_date, 'YYYY-MM-DD') date_, to_char(current_timestamp, 'YYYY-MM-DD HH24:MI:SS') ts_ from dual
            """
       ]
    },
    "pgql": {
        "tags": ['postgresql', 'postgres_sqlite', 'sqlite'],
        "sources": ["postgresql_source", "sqlite_source"],
        "pk": ["code"],
        "queries": [
            """
            select 1 code, 1.0 float_, 'hello' text_, current_date date_, to_char(current_timestamp, 'YYYY-MM-DD HH24:MI:SS') ts_
            """,
            """
            select 1 code, 1.0 float_, 'hello' text_, date(current_timestamp, 'localtime') date_, datetime(current_timestamp, 'localtime') ts_
            """
       ]
    },
    "pgms": {
        "tags": ['postgresql', 'postgres_mssql', 'mssql'],
        "sources": ["postgresql_source", "mssql_source"],
        "pk": ["code"],
        "queries": [
            """
            select 1 code, 1.0 float_, 'hello' text_, current_date date_, to_char(current_timestamp, 'YYYY-MM-DD HH24:MI:SS') ts_
            """,
            """
            select 1 code, 1.0 float_, 'hello' text_, current_date date_, format(current_timestamp, 'yyyy-MM-dd HH:mm:ss') ts_
            """
       ]
    },
    # sqlite first
    "qlmy": {
        "tags": ['sqlite', 'sqlite_mysql', 'mysql'],
        "sources": ["sqlite_source", "mysql_source"],
        "pk": ["code"],
        "queries": [
            """
            select 1 code, 1.0 float_, 'hello' text_, date(current_timestamp, 'localtime') date_, datetime(current_timestamp, 'localtime') ts_
            """,
            """
            select 1 code, 1.0 float_, 'hello' text_, current_date date_, date_format(current_timestamp, '%Y-%m-%d %H:%i:%s') ts_
            """
       ]
    },
    "qlor": {
        "tags": ['sqlite', 'sqlite_oracle', 'oracle'],
        "sources": ["sqlite_source", "oracle_source"],
        "pk": ["code"],
        "queries": [
            """
            select 1 code, 1.0 float_, 'hello' text_, date(current_timestamp, 'localtime') date_, datetime(current_timestamp, 'localtime') ts_
            """,
            """
            select 1 code, 1.0 float_, 'hello' text_, to_char(current_date, 'YYYY-MM-DD') date_, to_char(current_timestamp, 'YYYY-MM-DD HH24:MI:SS') ts_ from dual
            """
       ]
    },
    "qlpg": {
        "tags": ['sqlite', 'sqlite_postgresql', 'postgresql'],
        "sources": ["sqlite_source", "postgresql_source"],
        "pk": ["code"],
        "queries": [
            """
            select 1 code, 1.0 float_, 'hello' text_, date(current_timestamp, 'localtime') date_, datetime(current_timestamp, 'localtime') ts_
            """,
            """
            select 1 code, 1.0 float_, 'hello' text_, current_date date_, to_char(current_timestamp, 'YYYY-MM-DD HH24:MI:SS') ts_
            """
       ]
    },
    "qlms": {
        "tags": ['sqlite', 'sqlite_mssql', 'mssql'],
        "sources": ["sqlite_source", "mssql_source"],
        "pk": ["code"],
        "queries": [
            """
            select 1 code, 1.0 float_, 'hello' text_, date(current_timestamp, 'localtime') date_, datetime(current_timestamp, 'localtime') ts_
            """,
            """
            select 1 code, 1.0 float_, 'hello' text_, current_date date_, format(current_timestamp, 'yyyy-MM-dd HH:mm:ss') ts_
            """
       ]
    },
}
