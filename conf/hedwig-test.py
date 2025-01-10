import os
import sys

from sources import hedwig


#
# To ensure all test emails will be sent remove file ~/.dbang/.hedwig-test.json
# which keeps the timestamps for files used in test specs below.
#

#
# SETTINGS USED BY hedwig
#
# MANDATORY MANDATORY MANDATORY MANDATORY MANDATORY MANDATORY MANDATORY

MAIL_SERVER = hedwig.get('MAIL_SERVER', 'localhost')
MAIL_FROM = hedwig.get('MAIL_FROM', 'dbang <dbang@example.net>')

# OPTIONAL OPTIONAL OPTIONAL OPTIONAL OPTIONAL OPTIONAL OPTIONAL OPTIONAL

# defaults to False
DEBUGGING = True
# defaults to False
LOGGING = True
# defaults to current working directory
LOG_DIR = os.path.join(os.path.dirname(__file__), '..', 'log')
# files' encoding defaults to OS locale encoding
ENCODING = 'UTF-8'
# defaults to ISO 86101; use '%c' to align with locale
#DATETIME_FORMAT = '%c'
# defaults to ISO 86101; use '%x' to align with locale
#DATE_FORMAT = '%x'

# defaults to "<p>Hello!</p><p/>"
#HTML_GREETING = "<p>Hello!</p><p/>"
# defaults to "<p/><p>Have a good day!<br/>dbang Utilities<br/></p>"
#HTML_SIGNATURE = "<p/><p>Have a good day!<br/>dbang Utilities<br/></p>"
# defaults to "\nHello!\n\n"
#TEXT_GREETING = "\nHello!\n\n"
# defaults to "\n\nHave a good day!\ndbang Utilities\n"
#TEXT_SIGNATURE = "\n\nHave a good day!\ndbang Utilities\n"

#
# SETTINGS USED IN specs
#
MAIL_TO = hedwig.get('MAIL_TO', 'user@example.net')

TEST_HTML_FILE = os.path.join(os.path.dirname(__file__), '..', 'out', 'test.html')
HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="content-type" content="text/html; charset=UTF-8">
    <style type="text/css">
        th {{background:lightblue; padding: 1px 5px 1px 5px;}}
        td {{background:lightgrey; padding: 1px 5px 1px 5px;}}
    </style>
<title>{title}</title>
</head>
<body>
{body}
</body>
</html>
"""
HTML_LOREM_IPSUM = "<p><span style=\"color:red;\">Lorem</span> <span style=\"color:blue;\">ipsum</span>...</p>"

TEST_TEXT_FILE = os.path.join(os.path.dirname(__file__), '..', 'out', 'test.txt')
TEXT_GUADEAMUS = """Gaudeamus igitur,
iuvenes dum sumus,
gaudeamus igitur,
iuvenes dum sumus.
Post iucundam iuventutem
post molestam senectutem,
nos habebit humus,
nos habebit humus.
"""

TEST_CSV_FILE = os.path.join(os.path.dirname(__file__), '..', 'in', 'test.csv')
TEST_XLSX_FILE = os.path.join(os.path.dirname(__file__), '..', 'in', 'test.xlsx')
TEST_CSV_GLOB = os.path.join(os.path.dirname(__file__), '..', 'in', 'test_000???.csv')


#specs = {
#    # SPEC NAME EXTENSION DETERMINES THE MAIL FORMAT: html or txt
#    "example_spec.html": {
#        # tags to use in CLI instead of spec name
#        "tags": ['example'],
#        # send email regardless file(s) timestamp(s)
#        "force": False,
#        # jinja2 template to build the message body defaults to "hedwig.<format>.jinja"
#        "template": "hedwig.html.jinja"
#        "mail": {
#            # MANDATORY
#            "to": ["me@my.self"],
#            # optional
#            "cc": [],
#            # optional
#            "bcc": [],
#            # MANDATORY
#            "subject": "Qwerty",
#            # greeting defaults to HTML_GREETING
#            "greeting": HTML_GREETING,
#            # MANDATORY body is
#            #    either string
#            "body": "Body here...",
#            #    or dict with file details
#            #"body": {
#            #    "file": os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), 'out', 'example.html'),
#            #    # encoding defaults to ENCODING
#            #    "encoding": ENCODING,
#            #    # optional RE to clip text parts
#            #    "clip": "^.+?ERROR.*\n"
#            #    # optional list of (pattern, repl) pairs to make substitutions
#            #    # e.g. replace relative URLs with absolute ones in html file
#            #    "substitutions": [(r'href="(.+?)"', f'href="http://example.host/out/\\1"')],
#            #    # optional flag to only read new lines in the file(s) read earlier
#            #    "tail": True
#            #},
#            #    or list of strings and dicts
#            #"body": [
#            #    "Body part 1",
#            #    "Body part 2",
#            #    {"file": os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), 'out', 'example.html')},
#            #],
#            # signature defaults to HTML_SIGNATURE
#            "signature": HTML_SIGNATURE,
#            # optional attachments
#            "attachments": [
#                {
#                    "file": os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), 'out', 'example.csv'),
#                    # MIME defaults to application/octet-stream
#                    "MIME": "text/csv",
#                    # filename defaults to "file" filename
#                    "filename": "data.csv"
#                }
#            ]
#        }
#    },
#    "example_spec.txt": {
#        "mail": {
#            "to": "me@my.self",
#            "subject": "Qwerty",
#            # greeting defaults to TEXT_GREETING
#            "greeting": TEXT_GREETING,
#            # see example_spec.html above for body details
#            "body": "Hello there!",
#            # signature defaults to TEXT_SIGNATURE
#            "signature": TEXT_SIGNATURE
#        }
#    }
#}

specs = {
    #
    # bodies of strings
    #
    "helloworld.text": {
        "tags": ['text'],
        "force": True,
        "mail": {
            "to": [MAIL_TO],
            "subject": "{dbang} hello world",
            "body": "Hello world!\n",
        }
    },
    "--commented out.text": {
        "tags": ['text', 'commented'],
        "force": True,
        "mail": {
            "to": [MAIL_TO],
            "subject": "{dbang} commented out",
            "body": "Hello world!\n",
        }
    },
    "helloworld.html": {
        "tags": ['html'],
        "force": True,
        "mail": {
            "to": [MAIL_TO],
            "cc": [MAIL_TO],
            "bcc": [MAIL_TO],
            "subject": "{dbang} hello world",
            "body": "<p>Hello world!</p>",
        }
    },
    "html.html": {
        "tags": ['html'],
        "force": True,
        "mail": {
            "to": [MAIL_TO],
            "subject": "{dbang} html.html",
            "body": [
                HTML_LOREM_IPSUM,
                '<p/><p>See also <a href="https://www.google.com/search?q=lorem+ipsum">google.com</a>.</p>'
            ]
        }
    },
    "htmls.html": {
        "tags": ['html'],
        "force": True,
        "mail": {
            "to": [MAIL_TO],
            "subject": "{dbang} htmls.html",
            "body": [
                HTML_TEMPLATE.format(title="{dbang} html.html", body=HTML_LOREM_IPSUM),
                HTML_TEMPLATE.format(title="{dbang} html.html", body=HTML_LOREM_IPSUM),
                '<p/><p>See also <a href="https://www.google.com/search?q=lorem+ipsum">google.com</a>.</p>'
            ]
        }
    },
    "text.text": {
        "tags": ['text'],
        "force": True,
        "mail": {
            "to": [MAIL_TO],
            "subject": "{dbang} text.text",
            "body": [
                TEXT_GUADEAMUS,
                'See also https://www.google.com/search?q=gaudeamus+igitur\n'
            ]
        }
    },
    "texts.text": {
        "tags": ['text'],
        "force": True,
        "mail": {
            "to": [MAIL_TO],
            "subject": "{dbang} texts.text",
            "body": [
                TEXT_GUADEAMUS,
                TEXT_GUADEAMUS
            ]
        }
    },
    #
    # bodies of files
    #
    "file.html": {
        "tags": ['html'],
        "force": True,
        "mail": {
            "to": [MAIL_TO],
            "subject": "{dbang} file.html",
            "body": {"file": TEST_HTML_FILE}
        }
    },
    "files.html": {
        "tags": ['html'],
        "mail": {
            "to": [MAIL_TO],
            "subject": "{dbang} files.html",
            "body": [
                {"file": TEST_HTML_FILE},
                {
                    "file": TEST_HTML_FILE,
                    "encoding": "UTF-8",
                    "substitutions": [(r'>\s*a\s*</th>', r'>2</th>'), (r'>\s*a\s*\*\s*b\s*</th>', r'>2b</th>')]
                },
                '<p/><p>See also <a href="https://google.com">google.com</a>.</p>'
            ]
        }
    },
    "file.text": {
        "tags": ['text'],
        "force": True,
        "mail": {
            "to": [MAIL_TO],
            "subject": "{dbang} file.text",
            "body": {"file": TEST_TEXT_FILE}
        }
    },
    "files.text": {
        "tags": ['text'],
        "mail": {
            "to": [MAIL_TO],
            "subject": "{dbang} files.text",
            "body": [
                {"file": TEST_TEXT_FILE},
                {
                    "file": TEST_TEXT_FILE,
                    "substitutions": [(r'a', r'A'), (r'e', r'E')]
                },
                'See also https://www.google.com/search?q=lorem+ipsum\n'
            ]
        }
    },
    "glob.text": {
        "tags": ['glob', 'text'],
        "mail": {
            "to": [MAIL_TO],
            "subject": "{dbang} glob.text",
            "body": {"file": TEST_CSV_GLOB}
        }
    },
    #
    # bodies of strings and files
    #
    "html and file.html": {
        "tags": ['html'],
        "mail": {
            "to": [MAIL_TO],
            "subject": "{dbang} html and file.html",
            "greeting": "<p>Привет!</p><p/>",
            "body": [
                HTML_LOREM_IPSUM,
                {"file": TEST_HTML_FILE},
                '<p/><p>See also <a href="https://google.com">google.com</a>.</p>'
             ],
            "signature": "<p/><p>With best regards,<br/>dbang Utilities<br/></p>"
        }
    },
    "text and file.text": {
        "tags": ['text'],
        "mail": {
            "to": [MAIL_TO],
            "subject": "{dbang} text and file.text",
            "greeting": "Привет!\n\n",
            "body": [
                TEXT_GUADEAMUS,
                {"file": TEST_TEXT_FILE},
                'See also https://google.com\n'
             ],
            "signature": "\n\nWith best regards,\ndbang Utilities\n"
        }
    },
    #
    # attachments
    #
    "with attachment.html": {
        "tags": ['attachments', 'html'],
        "mail": {
            "to": [MAIL_TO],
            "subject": "{dbang} with attachment.html",
            "body": [
                "<p>See attached file(s).</p>",
                '<p/><p>See also MIME types at <a href="https://www.google.com/search?q=mime+types">google.com</a>.</p>'
            ],
            "attachments": [
                {
                    "file": TEST_CSV_FILE,
                    "MIME": "text/csv",
                    "filename": "countries.csv"
                }
            ]
        }
    },
    "with attachments.text": {
        "tags": ['attachments', 'text'],
        "mail": {
            "to": [MAIL_TO],
            "subject": "{dbang} with attachments.text",
            "body": [
                "See attached file(s).\n",
                'See also MIME types also https://www.google.com/search?q=mime+types\n'
            ],
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
    "with glob attachments.html": {
        "tags": ['attachments', 'glob', 'html'],
        "mail": {
            "to": [MAIL_TO],
            "subject": "{dbang} with glob attachment.html",
            "body": "<p>See attached file(s).</p>",
            "attachments": [
                {
                    "file": TEST_CSV_GLOB,
                    "MIME": "text/csv"
                },
            ]
        }
    },
    #
    # clippings
    #
    "clippings.text": {
        "tags": ['clippings', 'text'],
        "force": True,
        "mail": {
            "to": [MAIL_TO],
            "subject": "{dbang} clippings.text",
            "body": [
                {
                    "file": TEST_CSV_FILE,
                    "clip": r'^E.+?;..;...;\d\d\d$'
                }
             ],
        }
    },
    "clippings.html": {
        "tags": ['clippings', 'html'],
        "force": True,
        "mail": {
            "to": [MAIL_TO],
            "subject": "{dbang} clippings.html",
            "body": [
                {
                    "file": TEST_CSV_FILE,
                    # find all countries starting with letter E
                    "clip": r'^E.+?;..;...;\d\d\d$',
                    "substitutions": [
                        # plain text line to html table row
                        (r'^(.+?)$', '<tr><td><code>\\1</code></td></tr>'),
                        # result of prev sub into html table
                        (r'(.+)', '<table>\n<tr><th>Findings</th></tr>\n\\1\n</table>')
                    ]
                }
             ],
        }
    },
    "logged errors.html": {
        "tags": ['clippings', 'logs', 'html'],
        "mail": {
            "to": [MAIL_TO],
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
}
