#!/usr/bin/python3

import os
import sys
import csv
import logging
import decimal as dec
from datetime import date, datetime


DEBUGGING = False
LOGSTDOUT = True

BASENAME = os.path.basename(sys.argv[0])
if len(sys.argv) not in (2, 3):
    sys.stderr.write(
        f"""
        Error: Wrong number of arguments.
        Usage: {BASENAME} <cfg-file> [<spec> | all]
        """
    )
    sys.exit(1)

SCRIPT_DIR = os.path.dirname(os.path.realpath(sys.argv[0]))
CFG_DIR = os.path.join(SCRIPT_DIR, 'cfg')
CFG_NAME = sys.argv[1].split('.')[0]
CFG_FILE = f"{CFG_NAME}.py"
if not os.path.isfile(os.path.join(CFG_DIR, CFG_FILE)):
    sys.stderr.write(
        f"""
        Error: Config-file {CFG_FILE} not found.
        Usage: {BASENAME} <cfg-file> [<spec> | all]
        """
    )
    sys.exit(1)

sys.path.append(CFG_DIR)
cfg = __import__(CFG_NAME)
sources = cfg.sources
specs = cfg.specs

SPEC = sys.argv[2] if len(sys.argv) == 3 else 'all'
if SPEC not in [*specs.keys(), 'all']:
    sys.stderr.write(
        f"""
        Error: Spec {SPEC} not found in config-file.
        Usage: {BASENAME} <cfg-file> [<spec> | all]
        """
    )
    sys.exit(1)

for source in sources.values():
    if source["database"] == "oracle":
        import cx_Oracle
        source["lib"] = cx_Oracle
    elif source["database"] == "postgres":
        import psycopg2
        source["lib"] = psycopg2
    elif source["database"] == "sqlite":
        import sqlite3
        source["lib"] = sqlite3
    else:
        source["lib"] = None

BASENAME = os.path.basename(sys.argv[0]).split('.')[0]
LOG_FILE = os.path.join(SCRIPT_DIR, 'log', f'{date.today().isoformat()}_{BASENAME}.log')
#OUT_DIR = os.path.join(SCRIPT_DIR, 'out')  # set in config-file

# number of rows to fetch with one fetch
ONE_FETCH_ROWS = 5000

HTML_FIRST = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="content-type" content="text/html; charset=UTF-8">
    <style type="text/css">
        th {{background:lightblue; padding: 1px 5px 1px 5px;}}
        td {{background:lightgrey; padding: 1px 5px 1px 5px; text-align: left;}}
    </style>
<title>{title}</title>
</head>
<body>
<h2>{title}</h2>
<p>{run[1]}</p>
<table>
"""
HTML_LAST = """
</table>
</body>
</html>
"""

logging.basicConfig(
    filename=None if LOGSTDOUT else LOG_FILE,
    format='%(asctime)s:%(levelname)s:%(name)s:%(message)s',
    level=logging.INFO
)
logger = logging.getLogger(BASENAME)


def connection(src):
    if not sources[src].get('con'):
        sources[src]['con'] = sources[src]['lib'].connect(sources[src]['con_string'])
        if sources[src].get('init'):
            if isinstance(sources[src]['init'], str):
                sources[src]['init'] = [sources[src]['init']]
            cur = sources[src]['con'].cursor()
            for init in sources[src]['init']:
                cur.execute(init)
            cur.close()
    return sources[src]['con']


def process(run, spec_name, spec):
    try:
        out_base, out_format = spec_name.split('.')
        assert (
            out_format in ('html', 'csv')
            and isinstance(spec, dict)
            and {*spec.keys()} >= {'source', 'query'}
            and isinstance(spec['source'], str)
            and isinstance(spec['query'], str)
            and sources.get(spec['source'])
            ), f"Bad spec {spec_name}"

        logger.info(f"{spec_name}; DB = {spec['source']}")

        con = connection(spec['source'])
        cur = con.cursor()
        query = spec['query']
        if DEBUGGING:
            logger.info('\n\n' + query.strip() + '\n')
        cur.execute(query)

        if not spec.get('titles'):
            spec['titles'] = [d[0] for d in cur.description]

        dec_sep = spec.get('dec_separator', '.')
        out_path = spec.get('out_dir', cfg.OUT_DIR)

        file = None
        rowcount = 0
        while True:
            rows = cur.fetchmany(ONE_FETCH_ROWS)
            if not rows:
                break
            rowcount += len(rows)
            # initialize
            if file is None:
                out_file = os.path.join(out_path, f"{CFG_NAME}_{out_base}.out")
                if out_format == "html":
                    file = open(out_file, "w", encoding=spec.get("encoding", cfg.HTML_ENCODING))
                    file.write(HTML_FIRST.format(run=run, title=spec.get('title', out_base)))
                    file.write(
                        '<tr><th>' +
                        '</th><th>'.join(spec['titles']) +
                        '</th></tr>'
                    )
                elif out_format == "csv":
                    file = open(out_file, "w", encoding=spec.get("encoding", cfg.CSV_ENCODING))
                    csv_writer = \
                        csv.writer(
                            file,
                            dialect=spec.get('dialect', cfg.CSV_DIALECT),
                            delimiter=spec.get('delimiter', cfg.CSV_DELIMITER),
                            lineterminator='\n'
                        )
                    csv_writer.writerow(spec['titles'])
            # write next chunk of rows
            for row in rows:
                if out_format == "html":
                    file.write(
                        '<tr>' +
                        '</td>'.join(
                            '<td>' if f == None else \
                            '<td style="text-align:center;">' + f.strftime(cfg.PY_DATE_FORMAT) if isinstance(f, date) else \
                            '<td style="text-align:center;">' + f.strftime(cfg.PY_DATETIME_FORMAT) if isinstance(f, datetime) else \
                            '<td>' + str(f) if not isinstance(f, (int, float, dec.Decimal)) else \
                            '<td style="text-align:right;">' + str(f).replace('.', dec_sep) \
                            for f in row
                        ) + '</td></tr>'
                    )
                elif out_format == "csv":
                    csv_writer.writerow(
                        '' if f == None else \
                        f.strftime(cfg.PY_DATE_FORMAT) if isinstance(f, date) else \
                        f.strftime(cfg.PY_DATETIME_FORMAT) if isinstance(f, datetime) else \
                        f if not isinstance(f, (float, dec.Decimal)) or dec_sep == '.' else \
                        str(f).replace('.', dec_sep) \
                        for f in row
                    )
        # finalize
        if file:
            if out_format == "html":
                file.write(HTML_LAST)
            elif out_format == "csv":
                pass
            file.close()
            _out_file = out_file.rstrip('out') + out_format
            # os.rename: On Windows, if dst exists a FileExistsError is always raised.
            if os.path.isfile(_out_file):
                os.remove(_out_file)
            os.rename(out_file, _out_file)
        logger.info(f"Wrote {rowcount} rows.")

        cur.close()
        con.rollback()

    except:
        logger.exception('EXCEPT')
        for src in sources.values():
            if src.get('con'):
                src['con'].rollback()


def main():
    logger.info(f'-- start {" ".join(sys.argv)}')

    _temp = datetime.now()
    run = [
        int(_temp.strftime('%Y%m%d%H%M%S')),
        _temp.strftime('%Y-%m-%d %H:%M:%S'),
        _temp.strftime('%Y-%m-%d_%H-%M-%S')
    ]

    for spec_name, spec in specs.items():
        if SPEC in (spec_name, 'all'):
            process(run, spec_name, spec)

    for src in sources.values():
        if src.get('con'):
            src['con'].close()
            src['con'] = None

    logger.info('-- done')


if __name__ == '__main__':
    main()
