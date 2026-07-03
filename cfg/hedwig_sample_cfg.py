import os
import sys

# import MAIL_* global variables with mail server related data
from sources import *


# See details on config file's and spec parameters in doc/hedwig.md

DEBUGGING = True
LOGGING = True

LOG_DIR = os.path.join(os.path.dirname(__file__), '..', 'log')

ENCODING = 'UTF-8'

#HTML_GREETING = "<p>Hello!</p><p/>"
#HTML_SIGNATURE = "<p/><p>Have a good day!<br/>dbang Utilities<br/></p>"
#TEXT_GREETING = "\nHello!\n\n"
#TEXT_SIGNATURE = "\n\nHave a good day!\ndbang Utilities\n"

specs = {
    "<descriptive spec name>.html": {
        #"tags": ["example"],
        #"force": False,
        #"template": "hedwig_sample.html.jinja"
        "mail": {
            "to": "<recipient@email.address>",
            #"cc": [],
            #"bcc": [],
            "subject": "<subject>",
            #"greeting": HTML_GREETING,
            "body": {
                "file": os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), 'out', '<example>.html'),
                #"encoding": ENCODING,
                #"clip": "<regexp to clip text from file>"
                #"substitutions": [(r'<regexp>', r'<subst>')],
                #"tail": True
            },
            #"signature": HTML_SIGNATURE,
            #"attachments": [
            #    {
            #        "file": os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), 'out', '<example>.csv'),
            #        "MIME": "text/csv",
            #        "filename": "<attached file name>.csv"
            #    }
            #]
        }
    },
    "<descriptive spec name>.txt": {
        #"tags": ["example"],
        #"force": False,
        #"template": "hedwig_sample.text.jinja"
        "mail": {
            "to": "<recipient@email.address>",
            #"cc": [],
            #"bcc": [],
            "subject": "<subject>",
            #"greeting": TEXT_GREETING,
            "body": [
                "<text here>",
                {"file": os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), 'out', '<example>.txt')}
            ],
            #"signature": TEXT_SIGNATURE
            #"attachments": [
            #    {
            #        "file": os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), 'out', '<example>.csv'),
            #        "MIME": "text/csv",
            #        "filename": "<attached file name>.csv"
            #    }
            #]
        }
    }
}
