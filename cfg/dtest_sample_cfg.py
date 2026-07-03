import os
import sys

from sources import sources


# See details on config file's and spec parameters in doc/dtest.md

DEBUGGING = True
LOGGING = True
PARALLEL_WORKERS = 2

OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'out')
LOG_DIR = os.path.join(os.path.dirname(__file__), '..', 'log')

# defaults to embedded template
#RUN_REPORT_TEMPLATE = 'dtest_sample_run_report.html.jinja'
# defaults to embedded template
#SPEC_REPORT_TEMPLATE = 'dtest_sample_spec_report.html.jinja'

SOURCE = "<source_one>"

specs = {
    "<descriptive spec name>": {
        #"tags": ["example"],
        #"doc": "<assertion to test>",
        #"source": SOURCE,
        #"setup": [],
        "query": "select 1 'one' where 1 != 1",
        #"upset": []
    },
}
