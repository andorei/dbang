# Data Sources

	version 0.3

Data sources, or databases, used by the utilities are defined in dictionary `sources` in file `conf/sources.py`.

Here is an example:

```
import os
import sys

sources = {
    "sqlite-source": {
        "database": "sqlite",
        "con_string": os.path.join(os.path.expanduser('~'), '.dbang', 'dbang.db')
    },
    "postgres-source": {
        "database": "postgres",
        "con_string": "postgresql://username:password@host/database"
        "setup": ["set timezone=\'Asia/Vladivostok\'"]
    },
    "oracle-source": {
        "database": "oracle",
        "con_string": "username/password@host:1521/ORA",
        "setup": ["ALTER SESSION SET TIME_ZONE = '+10:00'"],
        "oracledb_thick_mode": True
    },
    "mysql-source": {
        "database": "mysql",
        "con_string": "",
        "con_kwargs": {'host': 'host', 'database': 'database', 'user': 'username', 'password': 'password'},
        "setup": ["create table if not exists test_table (id int, name varchar(50))"],
        "upset": ["drop table if exists test_table"]
    },
}
```

A data source is described with the following parameters:

* `"database"` - DBMS type, one of `"sqlite"`, `"postgres"`, `"oracle"`, `"mysql"`, used to choose the Python database API module;
* `"con_string"` - DB connection string, used as the first argument when calling `<module>.connect()`;
* `"con_kwargs"` - optional dict of named arguments, used when calling `<module>.connect()`;
* `"setup"` - optional list of strings with SQL statements to execute once upon connecting to the DB;
* `"upset"` - optional list of strings with SQL statements to execute once before closing connection to the DB.
