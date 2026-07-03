import os
import sys

from sources import sources


# See details on config file's and spec parameters in doc/ddiff.md

DEBUGGING = True
LOGGING = True
PARALLEL_WORKERS = 2

OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'out')
LOG_DIR = os.path.join(os.path.dirname(__file__), '..', 'log')

#RUN_REPORT_TEMPLATE = 'ddiff_sample_run_report.html.jinja'
#SPEC_REPORT_TEMPLATE = 'ddiff_sample_spec_report.html.jinja'

SOURCES = ["<source_one>", "<source_two>"]
#DDIFF_SOURCE = sources["<source_one>"]

specs = {
    "<descriptive spec name>": {
        #"tags": ["<tag1>", "<tag2>"],
        #"doc": "<comments on the spec>"

        #
        # level 1
        #
        "pk": ["<level_1_pk>"],
        "queries": [
            "select <level_1_pk>, <c1>, <c2>, <c3>, <c4>, <c5> from <source_one_table_name>",
            "select <level_1_pk>, <c1>, <c2>, <c3>, <c4>, <c5> from <source_one_table_name>"
        ],
        #
        # level 2
        #
        "<descriptive spec name>": {
            "pk": ["<level_2_pk>"],
            "queries": [
                """
                select <level_2_pk>, <c1>, <c2>, <c3>
                from <source_one_table_name>
                where <level_1_pk> in ({%for r in argrows %}{{r[0]}}{{"," if not loop.last}}{%- endfor %})
                """,
                """
                select <level_2_pk>, <c1>, <c2>, <c3>
                from <source_one_table_name>
                where <level_1_pk> in ({%for r in argrows %}{{r[0]}}{{"," if not loop.last}}{%- endfor %})
                """
            ],
        }
    },
}
