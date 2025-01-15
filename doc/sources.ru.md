# Источники данных

Источники данных, или БД, с которыми работают утилиты, определяются в файле `conf/sources.py` в словаре (dict) `sources`.

Пример:

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

Каждый источник данных описывается параметрами:

* `"database"` - вид СУБД, одно из: `"sqlite"`, `"postgres"`, `"oracle"`, `"mysql"`, используется для выбора Python модуля DB-API для работы с БД;
* `"con_string"` - строка присоединения к БД, используется при вызове функции `<модуль>.connect()`;
* `"con_kwargs"` - необязательный словарь (dict) именованных аргументов, используется при вызове функции `<модуль>.connect()`;
* `"setup"` - необязательный список (list) строк с предложениями SQL, которые однократно выполняются сразу после установления соединения с БД;
* `"upset"` - необязательный список (list) строк с предложениями SQL, которые однократно выполняются перед закрытием соединения с БД.
