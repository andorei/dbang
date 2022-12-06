import os
import sys


# MANDATORY constants used by hedwig.py

MAIL_SERVER = 'localhost'
MAIL_FROM = 'dbang <dbang@dbang.dbang>'
MAIL_GREETING = """
<p>Hello!</p><p/>
"""
MAIL_SIGNATURE = """
<p/><p>
Have a good day!<br/>
dbang Utilities<br/>
</p>
"""
HTML_ENCODING = 'UTF-8'

# Optional constants used in specs below

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

#specs = {
#    "example_spec": {
#        "mail": {
#            # MANDATORY
#            "to": "me@my.self",
#            # optional
#            "cc": "",
#            # optional
#            "bcc": "",
#            # MANDATORY
#            "subject": "Qwerty",
#            # greeting defaults to MAIL_GREETING
#            "greeting": MAIL_GREETING,
#            # MANDATORY source(s) for email body
#            "sources": [
#                # specify one or more 'file.html' or 'html'
#                {
#                    "file.html": os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), 'out', 'example.html'),
#                    # encoding defaults to HTML_ENCODING
#                    "encoding": HTML_ENCODING,
#                    # optional list of (pattern, repl) pairs to make substitutions
#                    # e.g. replace relative URLs with absolute ones in html file
#                    "substitutions": [(r'href="(.+?)"', f'href="http://example.host/out/\\1"')],
#                },
#                {
#                    "html": HTML_TEMPLATE.format(title='Title here', body='<p>Body here.</p>')
#                }
#            ]
#            # optional text just before the signature
#            "finally": '<p/><p>See also <a href="https://google.com">google.com</a>.</p>',
#            # signature defaults to MAIL_SIGNATURE
#            "signature": MAIL_SIGNATURE
#        }
#    }
#}

specs = {
    "file.html": {
        "mail": {
            "to": "trofimov.aa@boobl-goom.ru",
            "subject": "{dbang} file.html",
            "sources": [
                {"file.html": TEST_HTML_FILE}
            ],
            "finally": f'<p/><p>See also <a href="https://google.com">google.com</a>.</p>'
        }
    },
    "combined files": {
        "mail": {
            "to": "trofimov.aa@boobl-goom.ru",
            "subject": "{dbang} combined files",
            "sources": [
                {
                    "file.html": TEST_HTML_FILE,
                    #"encoding": "UTF-8",
                    #"substitutions": []
                },
                {
                    "file.html": TEST_HTML_FILE,
                    "encoding": "UTF-8",
                    "substitutions": [(r'>\s*a\s*</th>', r'>2</th>'), (r'>\s*a\s*\*\s*b\s*</th>', r'>2b</th>')]
                }
             ],
            "finally": f'<p/><p>See also <a href="https://google.com">google.com</a>.</p>'
        }
    },
    "combined doc and file": {
        "mail": {
            "to": "trofimov.aa@boobl-goom.ru",
            "subject": "{dbang} combined doc and file",
            "greeting": "<p>Привет!</p><p/>",
            "sources": [
                {"html": HTML_TEMPLATE.format(title="{dbang} hello-body-customized", body="<p>Lorem ipsum...</p>")},
                {"file.html": TEST_HTML_FILE}
             ],
            "finally": f'<p/><p>See also <a href="https://google.com">google.com</a>.</p>',
            "signature": "<p/><p>With best regards,<br/>dbang Utilities<br/></p>"
        }
    },
}
