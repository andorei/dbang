import os

sources = {
    #
    # Sample data sources used in dbang test specs.
    #
    "mssql_source": {
        "database": "mssql",
        "con_string": "Server=host;Database=database;UID=username;PWD=password;Authentication=SqlPassword;TrustServerCertificate=yes",
        "con_kwargs": {}
    },
    "mysql_source": {
        "database": "mysql",
        "con_string": "",
        "con_kwargs": {'host': 'host', 'database': 'database', 'user': 'username', 'password': 'password'}
    },
    "oracle_source": {
        "database": "oracle",
        "con_string": "username/password@host:1521/ORA",
        "oracledb_thick_mode": True
    },
    "postgresql_source": {
        "database": "postgres",
        "con_string": "postgresql://username:password@host/database"
    },
    "sqlite_source": {
        "database": "sqlite",
        "con_string": os.path.join(os.path.expanduser('~'), '.dbang', 'dbang.db')
    }
}

#
# Sensitive mail parameters to be imported into hedwig cfg-file.
#
MAIL_SERVER = 'smtp.example.net'
MAIL_FROM = 'user@example.net'
MAIL_TO = 'user@example.net'
#MAIL_USER = 'user'
#MAIL_PASSWORD = 'password'
#MAIL_PORT = 587
#MAIL_USE_TLS = True
