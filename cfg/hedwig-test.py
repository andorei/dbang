import os
import sys


#
# To ensure all test emails will be sent remove cfg/.hedwig-test.json
# which keeps the timestamps for files used in test specs below.
#


# MANDATORY constants used by hedwig.py

MAIL_SERVER = 'localhost'
MAIL_FROM = 'dbang <dbang@dbang.dbang>'

ENCODING = 'UTF-8'

HTML_GREETING = """
<p>Hello!</p><p/>
"""
HTML_SIGNATURE = """
<p/><p>
Have a good day!<br/>
dbang Utilities<br/>
</p>
"""
TEXT_GREETING = """
Hello!

"""
TEXT_SIGNATURE = """

Have a good day!
dbang Utilities
"""


# OPTIONAL CONSTANTS

DEBUGGING = True
#LOGSTDOUT = False


# CUSTOM CONSTANTS USED IN specs BELOW

MAIL_TO = 'me@my.self'

TEST_HTML_FILE = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), 'out', 'test.html')
HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="content-type" content="text/html; charset=UTF-8">
    <style type="text/css">
        th {{background:lightblue; padding: 1px 5px 1px 5px;}}
        td {{background:lightgrey; padding: 1px 5px 1px 5px; text-align: center;}}
    </style>
<title>{title}</title>
</head>
<body>
{body}
</body>
</html>
"""
HTML_LOREM_IPSUM = "<p><span style=\"color:red;\">Lorem</span> <span style=\"color:blue;\">ipsum</span>...</p>"

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

TEST_CSV_FILE = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), 'in', 'test.csv')
TEST_XLSX_FILE = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), 'in', 'test.xlsx')


#specs = {
#    # SPEC NAME EXTENSION DETERMINES THE MAIL FORMAT: html or txt
#    "example_spec.html": {
#        "mail": {
#            # MANDATORY
#            "to": "me@my.self",
#            # optional
#            "cc": "",
#            # optional
#            "bcc": "",
#            # MANDATORY
#            "subject": "Qwerty",
#            # just send email unconditionally
#            "always": False,
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
#            #    # optional list of (pattern, repl) pairs to make substitutions
#            #    # e.g. replace relative URLs with absolute ones in html file
#            #    "substitutions": [(r'href="(.+?)"', f'href="http://example.host/out/\\1"')],
#            #},
#            #    or list of strings and dicts
#            #"body": [
#            #    "Body part 1",
#            #    "Body part 2",
#            #    {"file": os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), 'out', 'example.html')}
#            #],
#            # optional text just before the signature
#            "finally": '<p/><p>See also <a href="https://google.com">google.com</a>.</p>',
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
#            # optional text just before the signature
#            "finally": "\nSee also https://google.com\n",
#            # signature defaults to TEXT_SIGNATURE
#            "signature": TEXT_SIGNATURE
#        }
#    }
#}

specs = {
    "helloworld.txt": {
        "mail": {
            "to": MAIL_TO,
            "subject": "{dbang} hello world",
            "body": "Hello world!",
            "always": True,
        }
    },
    "helloworld.html": {
        "mail": {
            "to": MAIL_TO,
            "subject": "{dbang} hello world",
            "body": "<html><body><p>Hello world!</p></body></html>",
            "always": True,
        }
    },
    #
    # bodies of strings
    #
    "html.html": {
        "mail": {
            "to": MAIL_TO,
            "subject": "{dbang} html.html",
            "always": True,
            "body": HTML_TEMPLATE.format(title="{dbang} html.html", body=HTML_LOREM_IPSUM),
            "finally": '<p/><p>See also <a href="https://www.google.com/search?q=lorem+ipsum">google.com</a>.</p>'
        }
    },
    "htmls.html": {
        "mail": {
            "to": MAIL_TO,
            "subject": "{dbang} htmls.html",
            "always": True,
            "body": [
                HTML_TEMPLATE.format(title="{dbang} html.html", body=HTML_LOREM_IPSUM),
                HTML_TEMPLATE.format(title="{dbang} html.html", body=HTML_LOREM_IPSUM)
            ],
            #"finally": '<p/><p>See also <a href="https://www.google.com/search?q=lorem+ipsum">google.com</a>.</p>'
        }
    },
    "text.txt": {
        "mail": {
            "to": MAIL_TO,
            "subject": "{dbang} text.txt",
            "always": True,
            "body": TEXT_GUADEAMUS,
            "finally": '\nSee also https://www.google.com/search?q=gaudeamus+igitur\n'
        }
    },
    "texts.txt": {
        "mail": {
            "to": MAIL_TO,
            "subject": "{dbang} texts.txt",
            "always": True,
            "body": [
                TEXT_GUADEAMUS,
                TEXT_GUADEAMUS
            ],
            #"finally": '\nSee also https://www.google.com/search?q=gaudeamus+igitur\n'
        }
    },
    #
    # bodies of files
    #
    "file.html": {
        "mail": {
            "always": True,
            "to": MAIL_TO,
            "subject": "{dbang} file.html",
            "body": {"file": TEST_HTML_FILE},
            "finally": '<p/><p>See also <a href="https://google.com">google.com</a>.</p>'
        }
    },
    "files.html": {
        "mail": {
            "to": MAIL_TO,
            "subject": "{dbang} files.html",
            "body": [
                {"file": TEST_HTML_FILE},
                {
                    "file": TEST_HTML_FILE,
                    "encoding": "UTF-8",
                    "substitutions": [(r'>\s*a\s*</th>', r'>2</th>'), (r'>\s*a\s*\*\s*b\s*</th>', r'>2b</th>')]
                }
            ],
            "finally": '<p/><p>See also <a href="https://google.com">google.com</a>.</p>'
        }
    },
    "file.txt": {
        "mail": {
            "always": True,
            "to": MAIL_TO,
            "subject": "{dbang} file.txt",
            "body": {"file": TEST_TEXT_FILE},
            "finally": '\nSee also https://www.google.com/search?q=lorem+ipsum\n'
        }
    },
    "files.txt": {
        "mail": {
            "to": MAIL_TO,
            "subject": "{dbang} files.txt",
            "body": [
                {"file": TEST_TEXT_FILE},
                {
                    "file": TEST_TEXT_FILE,
                    "substitutions": [(r'a', r'A'), (r'e', r'E')]
                }
            ],
            "finally": '\nSee also https://www.google.com/search?q=lorem+ipsum\n'
        }
    },
    #
    # bodies of strings and files
    #
    "html and file.html": {
        "mail": {
            "to": MAIL_TO,
            "subject": "{dbang} html and file.html",
            "greeting": "<p>Привет!</p><p/>",
            "body": [
                HTML_TEMPLATE.format(title="{dbang} html and file.html", body=HTML_LOREM_IPSUM),
                {"file": TEST_HTML_FILE}
             ],
            "finally": '<p/><p>See also <a href="https://google.com">google.com</a>.</p>',
            "signature": "<p/><p>With best regards,<br/>dbang Utilities<br/></p>"
        }
    },
    "text and file.txt": {
        "mail": {
            "to": MAIL_TO,
            "subject": "{dbang} text and file.txt",
            "greeting": "Привет!\n\n",
            "body": [
                TEXT_GUADEAMUS,
                {"file": TEST_TEXT_FILE}
             ],
            "finally": '\nSee also https://google.com\n',
            "signature": "\n\nWith best regards,\ndbang Utilities\n"
        }
    },
    #
    # attachments
    #
    "with attachment.html": {
        "mail": {
            "to": MAIL_TO,
            "subject": "{dbang} with attachment.html",
            "body": HTML_TEMPLATE.format(title="{dbang} with attachment.html", body="See attached file."),
            "finally": '<p/><p>See also MIME types at <a href="https://www.google.com/search?q=mime+types">google.com</a>.</p>',
            "attachments": [
                {
                    "file": TEST_CSV_FILE,
                    "MIME": "text/csv",
                    "filename": "countries.csv"
                }
            ]
        }
    },
    "with attachments.txt": {
        "mail": {
            "to": MAIL_TO,
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
}
