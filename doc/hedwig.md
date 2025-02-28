# hedwig. Sending Files (and More) by Email

	version 0.3

The `hedwig` utility creates email messages and sends them to addressees according to specs in config files. They may be either text messages (`text/plain`) or HTML ones (`text/html`), and they may have attached files.

* [How It Works](#how-it-works)
* [Message Body](#message-body)
* [Attached Files](#attached-files)
* [Notifications Based on File Content](#notifications-based-on-file-content)
* [Command Line Arguments](#command-line-arguments)
* [Config File Parameters](#config-file-parameters)
* [Spec Parameters](#spec-parameters)

## How It Works

Here is an example of minimalistic specs for sending messages `Hello world!` as text and as HTML. Message format is explicitly specified with spec name extension:

```
specs = {
    ...
    "helloworld.txt": {
        "mail": {
            "to": "me@my.self",
            "subject": "{dbang} hello world",
            "body": "Hello world!",
            "always": True
        }
    },
    "helloworld.html": {
        "mail": {
            "to": "me@my.self",
            "subject": "{dbang} hello world",
            "body": "&lt;html>&lt;body&gt;&lt;p&gt;Hello world!&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;",
            "always": True
        }
    },
    ...
}
```

If you add these specs in test config file `hedwig-test.py` and run them you'll get the emails with the following content:

```
Hello!

Hello world!

Have a good day!
dbang Utilities
```

The greeting and the signature were added automatically. They are set in the config file with global variables `TEXT_GREEETING` and `TEXT_SIGNATURE` – for text messages – and `HTML_GREEETING` and `HTML_SIGNATURE` – for HTML messages.

You may override greeting and signature directly in a spec:

```
specs = {
    ...
    "helloworld.txt": {
        "mail": {
            "to": "me@my.self",
            "subject": "{dbang} hello world",
            "greeting": "Салют!\n\n",
            "body": [
                "Hello world!",
                "\nЖду ответа как соловей лета.\n"
            ],
            "signature": "\n\nПока :)\n"
        },
        "force": True
    },
    ...
}
```

The result will be:

```
Salut!

Hello world!

Waiting for your answer.

Bye :)
```

Spec parameter `"force": True` instructs `hedwig` to send the message unconditionally.

The thing is that main purpose of `hedwig` is sending by email files created by utilities `ddiff`, `dtest`, `dput`. (Of course you may send files created by other means.) If a given file has been sent, then running spec again will not result in sending it again – `hedwig` remembers the modification time of sent file and will only send this file again after it is updated.

For example, if [`dtest` utility](dtest.md) generates a file with data quality report once a day, and `hedwig` runs hourly and executes all the specs in a given config file, then email with the report will only be sent once a day – after the report file gets updated.

To send the email unconditionally you use parameter `"force": True`. The same effect you get when running `hedwing` with [command line option](#commad-line-arguments) `-f` or `--force`.

## Message Body

Here is an example of two specs to compose the message body from the text file and the HTML file:

```
import os
import sys

OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'out')
...

specs = {
    ...
    "file.txt": {
        "mail": {
            "to": "me@my.self",
            "subject": "{dbang} file.txt",
            "body": {
                "file": os.path.join(OUT_DIR, 'test.txt')
            }
        }
    },
    "file.html": {
        "mail": {
            "to": "me@my.self",
            "subject": "{dbang} file.html",
            "body": {
                "file": os.path.join(OUT_DIR, 'test.html')
            }
        }
    },
    ...
}
```

These are the specs from the test config file `hedwig-test.py`. Run them and see the result in the inbox of your email client.

Spec parameter `"body"` allows defining the message body

* as text – with a `str` literal, see specs for `Hello world!` emails,
* as file – with a dict with key `"file"`, see the example above,
* as a composition of texts and files – with a list containing strings and dicts.

Here is an example spec where the message body is composed of the text and the content of the file:

```
import os
import sys

OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'out')

TEXT_GUADEAMUS = """Gaudeamus igitur,
iuvenes dum sumus,
gaudeamus igitur,
iuvenes dum sumus.
Post iucundam iuventutem
post molestam senectutem,
nos habebit humus,
nos habebit humus.
"""

...

specs = {
    ...
    "text and file.txt": {
        "mail": {
            "to": "me@my.self",
            "subject": "{dbang} text and file.txt",
            "body": [
                TEXT_GUADEAMUS,
                {"file": os.path.join(OUT_DIR, 'test.txt')}
             ]
        }
    },
    ...
}
```

Pay attention to the fact that, according to the spec, the message will only be sent once. Executing the spec repeatedly will not result in generating and sending a message again until the file `test.txt` gets updated.

If you want `hedwig` to send the message unconditionally then use spec parameter `"force": True` or [command line option](#commad-line-arguments) `-f` or `--force`.

The definition of a file which goes to a message body may contain the following parameters:

* `"file"` – path to a single file or [glob-pattern](https://docs.python.org/3/library/glob.html) for multiple files,
* `"encoding"` – (optional) file encoding that differs from the one set with global variable `ENCODING`,
* `"tail"` – (optional) `True` - read from a text file (e.g. log file) only lines added after previous run of the utility; `False` - read all lines,
* `"clip"` – (optional) Python regular expression to find pieces of interest in a file content (after applying `"tail"`), the rest of a file content is ignored,
* `"substitutions"` – (optional) list of pairs `(<pattern>, <replacement>)` to make substitutions in a file content (after applying `"clip"`).

Test config file `hedwig-test.py` contains comments on all the spec parameters. Read it carefully and familiarize yourself with all the parameters.

## Attached Files

You specify file(s) that should be attached to the email message with spec parameter `"attachments"`. This parameter is a list of files to be attached.

Here is an example specification with file attachments:

```
import os
import sys

IN_DIR = os.path.join(os.path.dirname(__file__), '..', 'in')

TEST_CSV_FILE = os.path.join(IN_DIR, 'test.csv')
TEST_XLSX_FILE = os.path.join(IN_DIR, 'test.xlsx')

...

specs = {
    ...
    "with attachments.txt": {
        "mail": {
            "to": "me@my.self",
            "subject": "{dbang} with attachments.txt",
            "body": "See attached files.",
            "attachments": [
                {
                    "file": TEST_CSV_FILE,
                    "MIME": "text/csv",
                    "filename": "countries.csv"
                },
                {
                    "file": TEST_XLSX_FILE,
                    "MIME": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    "filename": "countries.xlsx"
                },
            ]
        }
    },
    ...
}
```

In the dict that describes file(s) to attach:

* `"file"` specifies path to a file or [glob-pattern](https://docs.python.org/3/library/glob.html) for multiple files,
* `"MIME"` optionally sets the MIME type for the file,
* `"filename"` optionally sets the filename for the attached file.

You might want to specify `"filename"` if this name differs from the original name of the file, as in the above example.

## Notifications Based on File Content

All the `dbang` utilities write to log files messages of the same format.

Here is a piece of `dput` log file with error message:

```
2025-01-09 13:19:35,086:INFO:25544:-- start dput.py conf\dput_xxx zzz
2025-01-09 13:19:35,154:INFO:25544:C:\devel\data\zzz.csv
2025-01-09 13:19:35,159:INFO:25544:Loaded 249 of 249 rows with iload=48
2025-01-09 13:19:35,164:ERROR:25544:EXCEPT
Traceback (most recent call last):
  File "C:\devel\dbang\dput.py", line 708, in process
    assert file_ext in ('csv', 'xlsx', 'json', 'zip'), \
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Bad file extension "dat" in spec "special_zzz"
2025-01-09 13:19:35,185:INFO:25544:-- done  WITH 1 ERRORS
```

The next spec allows finding error messages in all log files in the `LOG_DIR` directory and send them by email:

```
import os
import sys

LOG_DIR = os.path.join(os.path.dirname(__file__), '..', 'log')

...

specs = {
	...
    "logged errors.html": {
        "mail": {
            "to": "me@my.self",
            "subject": "{dbang} logged errors.html",
            "body": [
                {
                    "file": os.path.join(LOG_DIR, '????-??-??_*.log'),
                    "tail": True,
                    # find all ERROR reports
                    "clip": r'^\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d,\d\d\d:ERROR:[^\n]*\n(?:(?!\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d,\d\d\d:)[^\n]*\n)*',
                    "substitutions": [
                        (r'(.+)', '<code><pre>\n\\1\n</pre></code>')
                    ],
                }
             ],
        }
    },
    ...
}
```

Notice that the parameter `"tail": True` tells `hedwig` only read lines from files that were added after the utility previous run. Thus, the result of running `hedwig` with the spec will be only email messages with newly logged errors.

## Command Line Arguments

```
$ ./hedwig.py -h
usage: hedwig.py [-h] [-f] [-v] cfg_file [spec]

Create email message and send it to addressees, as specified in cfg-file spec.

positional arguments:
  cfg_file       cfg-file name
  spec           spec name, defaults to "all"

options:
  -h, --help     show this help message and exit
  -f, --force    send email unconditionally
  -v, --version  show program's version number and exit

Thanks for using hedwig.py!
```

The only mandatory argument is config file name `cfg_file`.

If `spec` is provided then the utility executes only the named spec or specs with the given tag. If `spec` is omitted then all specs from the config file are executed.

Option `-f` or `--force` instructs the `hedwig` utility to build and send an email message even in case when files used to build a message have not changed since the last spec execution. The `hedwig` utility registers paths and modification times of processed files in a special file `~/.<cfg-file>.json` and by default only builds and sends email messages based on files not yet processed.

## Config File Parameters

Config file parameters are variables with names in uppercase that define context for executing specs from that config file. See also [Config Files Structure](conf.md).

The `hedwig` config file parameters are described below.

| Parameter         | Default Value                                          | Description                                  |
| ----------------- | ------------------------------------------------------ | -------------------------------------------- |
| `DEBUGGING`       | `False`                                                | Debugging mode?                              |
| `LOGGING`         | = DEBUGGING                                            | Write to log file?                           |
| `LOG_DIR`         | `./`                                                   | Path to the directory with log files.        |
| `DATETIME_FORMAT` | `"%Y-%m-%d %H:%M:%S%z"`                                | Datetime format; defaults to ISO 86101.      |
| `DATE_FORMAT`     | `"%Y-%m-%d"`                                           | Date format; defaults to ISO 86101.          |
| `ENCODING`*       | `locale.getpreferredencoding()`                        | Input file(s) encoding.                      |
| `HTML_GREETING`*  | `<p>Hello!</p><p/>`                                    | Greeting for email messages in HTML format.  |
| `HTML_SIGNATURE`* | `<p/><p>Have a good day!<br/>dbang Utilities<br/></p>` | Signature for email messages in HTML format. |
| `TEXT_GREETING`*  | `"\nHello!\n\n"`                                       | Greeting for plain text email messages.      |
| `TEXT_SIGNATURE`* | `"\n\nHave a good day!\ndbang Utilities\n`             | Signature for plain text email messages.     |
| `MAIL_SERVER`     |                                                        | SMTP server address.                         |
| `MAIL_FROM`       |                                                        | Email address of a sender.                   |
\* config file parameter marked with asterisk may be overridden at spec level with a corresponding spec parameter.

## Spec Parameters

Specs are found in a config file in the `specs` dictionary and contain **spec parameters**. See also [Config Files Structure](conf.md).

Spec parameters for `hedwig` utility are described below. If not explicitly described as mandatory, a spec parameter is optional and may be omitted.

| Spec Parameter        | Description                                                                                                                                                           |
| --------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `"tags"`              | List of tags attached to the spec.                                                                                                                                    |
| `"doc"`               | Short description/comment on a spec.                                                                                                                                  |
| `"force"`             | Build and send an email message unconditionally.                                                                                                                      |
| `"template"`          | Jinja2 шаблон для формирования тела письма. По умолчанию используются шаблоны `hedwig.text.jinja` для текстовых писем и `hedwig.html.jinja` для писем формата `html`. |
| **`"mail"`**          | Python dictionary with a message properties.                                                                                                                          |
| **`mail["to"]`**      | **MANDATORY** email address "To", a string (`str`) or a list of strings.                                                                                              |
| `mail["cc"]`          | Email address "Copy To", a string (`str`) or a list of strings.                                                                                                       |
| `mail["bcc"]`         | Email address "BCC", a string (`str`) or a list of strings.                                                                                                           |
| **`mail["subject"]`** | **MANDATORY** message subject (`str`).                                                                                                                                |
| `mail["greeting"]`    | A greeting (`str`).                                                                                                                                                   |
| **`mail["body"]`**    | **MANDATORY** message body, see [Message Body](#message-body).                                                                                                        |
| `mail["signature"]`   | A signature (`str`).                                                                                                                                                  |
| `mail["attachments"]` | List of attached files, see [Attached Files](#attached-files).                                                                                                        |
