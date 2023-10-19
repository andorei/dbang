# hedwig. Sending files (and more) by email

`hedwig` creates email messages and sends them to addressees according to specs in config-files. They may be either text messages (`text/plain`) or html ones (`text/html`), and they may have attached files.

Here is an example of minimalistic specs for sending messages `Hello world!` as text and as html. Message format is explicitly specified with spec name extension:

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

If you add these specs in test config-fie `hedwig-test.py` and run them you'll get the emails with the following content:

```
Hello!

Hello world!

Have a good day!
dbang Utilities
```

The greeting and the signature were added automatically. They are set in the config-file with globsl variables `TEXT_GREEETING` and `TEXT_SIGNATURE` – for text messages – and `HTML_GREEETING` and `HTML_SIGNATURE` – for html messages.

You may override greeting and signature directly in a spec. Add also add a few words before the signature with parameter `"finally"`:

```
specs = {
    ...
    "helloworld.txt": {
        "mail": {
            "to": "me@my.self",
            "subject": "{dbang} hello world",
            "greeting": "Salut!\n\n",
            "body": "Hello world!",
            "finally": "\nWating for your answer.\n",
            "signature": "\n\nBye :)\n",
            "always": True
        }
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

Spec parameter `"always": True` forces `hedwig` to send the message unconditionally.

Th thing is that main purpose of `hedwig` is sending by emal files created by utilities `ddiff`, `dtest`, `dput`. (Of course you may send files created by other means.) If a given file has been sent, then running spec again will not result in sending it again – `hedwig` remembers the modification time of sent file and will only send this file again after it is updated.

For example, if `dtest` utility generates a file with data quality report once a day, and `hedwig` runs hourly and executes all of the specs in a given config-file, then email with the report will only be send once a day – after the report file gets updated.

To send the email unconditionally you use parameter `"always": True`. Then it doesn't matter if the email is based on file or just contain a text specified with parameter `"body"`.

Here is an example of two specs to compose the message body from the text file and the html file:

```
import os
import sys

...

specs = {
    ...
    "file.txt": {
        "mail": {
            "to": "me@my.self",
            "subject": "{dbang} file.txt",
            "body": {
                "file": os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), 'out', 'test.txt')
            }
        }
    },
    "file.html": {
        "mail": {
            "to": "me@my.self",
            "subject": "{dbang} file.html",
            "body": {
                "file": os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), 'out', 'test.html')
            }
        }
    },
    ...
}
```

These are the specs from the test config-file `hedwig-test.py`. Run them and see the result in the inbox of your email client.

Spec parameter `"body"` allows to define the message body

* as text – with a `str` literal, see specs for `Hello world!` emails,
* as file – with a dict with key `"file"`, see the example above,
* as a composition of texts and files – with a list containing stings and dicts.

Here is an example spec where the message body is composed of the text and the content of the file:

```
TEST_TEXT_FILE = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), 'out', 'test.txt')
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
                {"file": TEST_TEXT_FILE}
             ]
        }
    },
    ...
}
```

Pay attention to the fact that, accoring to the spec, the message will only be sent once. Executing the spec repeatedly will not result in generating and sending a message again until the file `TEST_TEXT_FILE` gets updated. If you want `hedwig` to send the message unconditionally then use spec parameter `"always": True`.

The definition of a file which goes to a message body may contain 3 parameters:

* `"file"` specifies path to the file,
* `"encoding"` optionally sets the file encoding that differs from the one set with global variable `ENCODING`,
* `"substitutions"` optionally sets the list of pairs (pattern, replacement) to make substitutions in the file content.

You specify file(s) that should be attached to the email message with spec parameter `"attachments"`. This parameter is the list of files to be attached.

Here is an example specification with file attachments:

```
TEST_CSV_FILE = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), 'in', 'test.csv')
TEST_XLSX_FILE = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), 'in', 'test.xlsx')

...

specs = {
    ...
    "with attachments.txt": {
        "mail": {
            "to": "me@my.self",
            "subject": "{dbang} with attachments.txt",
            "body": "See attached files.",
            "finally": '\nSee also MIME types also https://www.google.com/search?q=mime+types\n',
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

The dictionary that desribes the file to attach may contain 3 parameters:

* `"file"` specifies path to the file,
* `"MIME"` optionally sets the MIME type for the file,
* `"filename"` optionally sets the filename for the attached file.

You might want to specify `"filename"` if this name differs from the original name of the file, as in the above example.

Test config-file `hedwig-test.py` contains comments on all the spec parameters. Read it carefully and familiarize yourself with all the parameters.
