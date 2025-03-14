# dbang

	версия 0.3

Читать на других языках: [английский](README.md).

Утилиты **dbang**
*  проверяют логическую полноту и целостность данных в БД
	* [`ddiff.py`](doc/ddiff.ru.md) - выполняет запросы к двум БД и формирует отчет о расхождениях,
	* [`dtest.py`](doc/dtest.ru.md) - выполняет запросы к БД и формирует отчет о найденных проблемах,
* выгружают и загружают данные из/в БД согласно спецификациям в конфиг-файле
	* [`dget.py`](doc/dget.ru.md) - выгружает данные из БД в файлы CSV, XLSX, JSON, HTMLl,
	* [`dput.py`](doc/dput.ru.md) - загружает данные из файлов CSV, XLSX, JSON в таблицы БД,
* формируют и отправляют е-мейл согласно спецификациям в конфиг-файле
	* [`hedwig.py`](doc/hedwig.ru.md) - на основе файлов создает и отправляет е-мейл.

Утилиты работают с СУБД Oracle, PostgreSQL, SQLite и MySQL посредством DB-API модулей Python.

## Установка

Утилиты **dbang** написаны на Python 3 и зависят от нескольких пакетов Python, указанных в файле [`requirements.txt`](requirements.txt).

Для установки утилит **dbang**
1. Скачайте [сжатый архив последнего релиза](https://github.com/andorei/dbang/releases/latest).
2. Распакуйте его в директории по вашему выбору.
3. Установите с помощью `pip` необходимые зависимости из файла [`requirements.txt`](requirements.txt)
```
cd dbang-<version>
pip install -r requirements.txt
```

## Использование

Утилиты запускаются командной строкой

```
python <utility>.py [options] <config-file> [<spec> | all]
```

где 
* `<utility>` – одно из `ddiff`, `dtest`, `dget`, `dput` or `hedwig`,
* `options` – опции командной строки, свои для каждой утилиты,
* `<config-file>` – имя конфиг-файла, а
* `<spec>` - имя спецификации в конфиг-файле. Если `<spec>` не указано, то выполняются все спецификации из конфиг-файла.

Чтобы познакомиться со всеми опциями утилиты, запустите ее с опцией `--help`.

Разумеется, на Linux вы можете сделать утилиты исполняемыми и запускать их просто по имени, не вызывая python в командной строке.

Утилиты **dbang**
* выполняют спецификации из конфиг-файлов, написанных на Python,
* пишут информационные и отладочные сообщения в лог-файлы, если в конфиг-файле включен режим логирования или отладки,
* сохраняют результаты работы и логи в директориях, заданных в конфиг-файле переменными `OUT_DIR` и `LOG_DIR`, соответственно, или в текущей директории, если эти переменные не определены.

## Примеры использования

Директория `conf` содержит тестовые конфиг-файлы, написанные как с целью тестирования, так и с целью демонстрации возможностей утилит. Все тестовые конфиг-файлы используют источники данных, определенные в конфигурационном файле `sources.py`, который отсутствует сразу после установки.

Создайте файл `sources.py` в директории `conf` самостоятельно, скопировав имеющийся файл `sample-sources.py`. После этого вы сможете запустить утилиты с конфиг-файлами, которые работают с локальной БД sqlite3:

```
cd dbang-<version>
./ddiff.py conf/ddiff-test-sqlite
./dtest.py conf/dtest-test-sqlite
./dget.py conf/dget-test-sqlite
./dput.py conf/dput-test-sqlite all
```

В директории `out` вы найдете
* отчет о расхождениях в данных, сформированный `ddiff`,
* отчет о качестве данных, сформированный `dtest`,
* файлы с данными, извлеченными `dget` из базы данных.

В директории `log` вы найдете лог-файлы каждой из утилит.

Для выполнения тестовых конфиг-файлов для СУБД Oracle, PostgreSQL или MySQL, отредактируйте в файле `sources.py` параметры подключения для источника `"oracle-source"`, `"postgres-source"` или `"mysql-source"`.  После этого утилиты, запущенные с соответствующими конфиг-файлами, подключатся к указанной вами БД.

Прежде чем запустить `hedwig.py` с тестовым конфиг-файлом `hedwig-test.py`, присвойте правильные значения переменным `MAIL_SERVER` и `MAIL_TO` в конфиг-файле. После этого выполните команду

```
./hedwig.py conf/hedwig-test
```

и проверьте входящую почту.

## Что дальше

Чтобы эффективно пользоваться утилитами **dbang**, вам нужно научиться создавать конфиг-файлы с необходимыми вам спецификациями.

В качестве шаблона для вашего конфиг-файла можно взять один из тестовых конфиг-файлов. Сохраните его под новым именем и внесите необходимые изменения.

Вы можете настроить запуск утилит с теми или иными конфиг-файлами по расписанию (с помощью `crontab` в Linux или Планировщика заданий в Windows) с последующей рассылкой сформированных отчетов и выгруженных файлов по электронной почте утилитой `hedwig`.

* [`sources.py`](doc/sources.ru.md)
* [`<config-file>.py`](doc/conf.ru.md)
* [`ddiff.py`](doc/ddiff.ru.md)
* [`dtest.py`](doc/dtest.ru.md)
* [`dget.py`](doc/dget.ru.md)
* [`dput.py`](doc/dput.ru.md)
* [`hedwig.py`](doc/hedwig.ru.md)

## Участие в проекте

Делайте pull запросы. Для значительных изменений открывайте, пожалуйста, issue для предварительного обсуждения изменений, которые хотите внести.

Не забывайте обновлять тесты (тестовые конфиг-файлы).

## Лицензия

[MIT](LICENSE)
