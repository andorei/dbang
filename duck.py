#!/usr/bin/env python3

import os
import sys
import locale
import re
import glob
import csv
import json
import argparse
import logging
from datetime import date, datetime

from openpyxl import load_workbook


VERSION = '0.3.1'

parser = argparse.ArgumentParser(
    description="Load data from file into DB, as specified in cfg-file spec.",
    epilog="Thanks for using %(prog)s!"
)

#parser.add_argument("-a", "--arg", action="append", help="pass one or more arguments to SQL query")
parser.add_argument("-d", "--delete", action="store_true", help="delete loaded data file(s)")
parser.add_argument("-f", "--force", action="store_true", help="load data file(s) unconditionally")
parser.add_argument("-t", "--trace", action="store_true", help="enable tracing")
parser.add_argument("-u", "--user", action="store",
                    default=os.environ.get('USER', os.environ.get('USERNAME', 'DBANG')),
                    help="set username")
parser.add_argument("-v", "--version", action="version", version="%(prog)s " + VERSION)
parser.add_argument("cfg_file", help="cfg-file name")
parser.add_argument("spec", help="spec name")
parser.add_argument("in_file", nargs="?", default=None, help="input file name")

args = parser.parse_args()

BASENAME = os.path.basename(sys.argv[0])
if not os.path.isfile(args.cfg_file) and not os.path.isfile(args.cfg_file + '.py'):
    sys.stderr.write(
        parser.format_usage() + \
        f"{BASENAME}: error: cfg-file not found: {args.cfg_file}\n"
    )
    sys.exit(1)

USER_DIR = os.path.expanduser('~')
if not os.path.isdir(USER_DIR):
    sys.stderr.write(
        parser.format_usage() + \
        f"{BASENAME}: error: user's home dir not found: {USER_DIR}\n"
    )
    sys.exit(1)
TEMP_DIR = os.path.join(USER_DIR, '.dbang')
if not os.path.isdir(TEMP_DIR):
    os.mkdir(TEMP_DIR)

CUR_DIR = os.getcwd()
CFG_DIR = os.path.abspath(os.path.dirname(args.cfg_file) or CUR_DIR)
CFG_MODULE = os.path.basename(args.cfg_file).rsplit('.', 1)[0]
sys.path.append(CFG_DIR)
cfg = __import__(CFG_MODULE)
sources = cfg.sources
specs = cfg.specs

SPEC = args.spec
# filter out specs commented out with leading --
specs = {k:v for k,v in specs.items() if not k.startswith('--')}
if SPEC not in [*specs.keys(), 'all', *(tag for val in specs.values() if val.get('tags') for tag in val['tags'])]:
    sys.stderr.write(
        parser.format_usage() + \
        f"{BASENAME}: error: spec not found in cfg-file: {SPEC}\n"
    )
    sys.exit(1)

IN_DIR = getattr(cfg, 'IN_DIR', CUR_DIR)
if not os.path.isdir(IN_DIR):
    sys.stderr.write(
        parser.format_usage() + \
        f"{BASENAME}: error: in dir not found: {IN_DIR}\n"
    )
    sys.exit(1)

DEBUGGING = getattr(cfg, 'DEBUGGING', False)
LOGGING = getattr(cfg, 'LOGGING', DEBUGGING)
LOG_DIR = getattr(cfg, 'LOG_DIR', CUR_DIR)
if LOGGING and not os.path.isdir(LOG_DIR):
    sys.stderr.write(
        parser.format_usage() + \
        f"{BASENAME}: error: log dir not found: {LOG_DIR}\n"
    )
    sys.exit(1)
LOG_FILE = os.path.join(LOG_DIR, f"{date.today().isoformat()}_{BASENAME.rsplit('.', 1)[0]}.log")
logging.basicConfig(
    filename=LOG_FILE,
    #encoding='utf-8', # encoding needs Python >=3.9
    format="%(asctime)s:%(levelname)s:%(name)s:%(message)s",
    level=logging.DEBUG if DEBUGGING else logging.INFO if LOGGING else logging.CRITICAL + 1
)
logger = logging.getLogger(BASENAME.rsplit('.', 1)[0])

locale.setlocale(locale.LC_TIME, '')
# datetime format for strftime depends on locale by default
DATETIME_FORMAT = getattr(cfg, 'DATETIME_FORMAT', '%c')
DATE_FORMAT = getattr(cfg, 'DATE_FORMAT', '%x')
# output file encoding by default
ENCODING = getattr(cfg, 'ENCODING', locale.getpreferredencoding())

CSV_DIALECT = getattr(cfg, 'CSV_DIALECT', 'excel')
CSV_DELIMITER = getattr(cfg, 'CSV_DELIMITER', csv.get_dialect(CSV_DIALECT).delimiter)

USER_ID = args.user
STAT_FILE = os.path.join(TEMP_DIR, f".{CFG_MODULE}.json")
# number of loads preserved per entity
#PRESERVE_N_LOADS = getattr(cfg, 'PRESERVE_N_LOADS', 10)
PRESERVE_N_TRACES = getattr(cfg, 'PRESERVE_N_TRACES', 10)

BATCH_SIZE = 1000


def trace(ts, status):
    """
    Create or rename trace file to show current status.
    """
    if not args.trace:
        return

    safe_spec = re.sub(r'[^\w. \-()\[\]]', '_', args.spec).rstrip('. ').lstrip()
    safe_user = re.sub(r'[^\w. \-()\[\]]', '_', args.user).rstrip('. ').lstrip()
    this_trace = f"dput#{safe_spec}#{safe_user}#{ts}#"
    this_trace_glob = os.path.join(TEMP_DIR, this_trace + '?')
    this_trace_file = os.path.join(TEMP_DIR, this_trace + str(status))

    traces = glob.glob(this_trace_glob)
    assert len(traces) < 2, f"Too many traces {this_trace_glob}: {len(traces)}"

    if len(traces) == 0:
        with open(this_trace_file, 'w', encoding="UTF-8"):
            pass
        all_traces_glob = os.path.join(TEMP_DIR, f"dput#{safe_spec}#{safe_user}#??????????????#?")
        for i, trace_file in enumerate(sorted(glob.glob(all_traces_glob), reverse=True)):
            if i >= PRESERVE_N_TRACES:
                os.remove(trace_file)
    elif len(traces) == 1 and traces[0] != this_trace_file:
        os.rename(traces[0], this_trace_file)
    logger.debug("trace %s", this_trace + str(status))


def process(spec_name, spec, input_file, stat):
    """
    Process spec from config-file.
    """
    return_code = 0

    in_file = input_file or spec.get('file', 'missing.file')
    if not glob.glob(in_file):
        in_file = os.path.join(IN_DIR, in_file)
        #assert glob.glob(in_file), f"Input file not found: {input_file}"
        if not glob.glob(in_file):
            logger.debug("%s - No files to load: %s", spec_name, input_file or spec.get('file', 'missing.file'))
            return return_code

    source = sources[spec['source']]
    filename = os.path.basename(in_file)
    in_format = filename.split('.')[-1]

    err_count = 0
    file = None
    wb = None
    try:
        # normalize the spec
        if spec.get('data') and not isinstance(spec['data'], (list, tuple)):
            spec['data'] = [spec['data']]
        if not isinstance(spec.get('actions'), (list, tuple)):
            spec['actions'] = [spec['actions']]

        # validate the spec
        assert in_format in ('csv', 'xlsx', 'json'), \
            f"Bad format \"{in_format}\" in spec \"{spec_name}\""
        assert sources.get(spec['source']) is not None, \
            f"Source \"{spec['source']}\" not defined, spec \"{spec_name}\""
        #XXXassert in_format != 'json' or spec.get('data'), \
        #XXX    f"Missing \"data\" in spec \"{spec_name}\""
        assert all(callable(i) for i in spec.get('actions', [])), \
            f"Bad \"actions\" in spec \"{spec_name}\""
        assert spec.get('data') is None or \
            len(spec.get('actions', [])) == len(spec.get('data', [])), \
            f"\"actions\" and \"data\" do not match in spec \"{spec_name}\""

        # find files to process
        all_files = []
        recent_files = []
        latest_mtime = stat[spec_name]['mtime']
        for file_name in sorted(glob.glob(in_file)):
            all_files.append(file_name)
            file_mtime = os.stat(file_name).st_mtime
            if file_mtime > stat[spec_name]['mtime']:
                recent_files.append(file_name)
            latest_mtime = max(file_mtime, latest_mtime)

        if (not args.force and not spec.get('force') and not recent_files) or not all_files:
            logger.info("%s - No files to process: %s", spec_name, input_file)
            return return_code

        if args.force or spec.get('force'):
            target_files = all_files
        else:
            target_files = recent_files

        logger.debug("Processing %s, %s", spec_name, in_file)

        if not source.get('up'):
            if source.get('setup') and callable(source['setup']):
                logger.debug("-- setup")
                source['setup']()
            source['up'] = True

        pdata = []
        pcount = []
        count = 0
        for ifile in target_files:

            # open file for reading
            if in_format == 'csv':
                file = open(ifile, 'r', encoding=spec.get('encoding', ENCODING))
                reader = \
                    csv.reader(
                        file,
                        dialect=spec.get('csv_dialect', CSV_DIALECT),
                        delimiter=spec.get('csv_delimiter', CSV_DELIMITER)
                        #quotechar=spec.get('csv_quotechar', CSV_QUOTECHAR)
                    )
            elif in_format == 'xlsx':
                wb = load_workbook(filename=ifile, read_only=True)
                #reader = wb.worksheets[0]
                reader = wb.worksheets[0].values
            elif in_format == 'json':
                file = open(ifile, 'r', encoding=spec.get('encoding', ENCODING))
                reader = json.load(file)
                assert isinstance(reader, list), f"Bad json file {ifile}"

            for row in reader:
                count += 1
                if count <= spec.get('skip_lines', 0):
                    continue

                # prepare data for processing
                for n, func in enumerate(spec.get('data', [None])):
                    if len(pdata) == n:
                        pdata.append([])
                        pcount.append(0)
                    _data = func(row) if func else row
                    if not _data:
                        # skip the row
                        pass
                    elif isinstance(_data, dict) and in_format == 'json':
                        #XXX process a JSON object
                        pdata[n].append(_data)
                    elif isinstance(_data, (list, tuple)) and not isinstance(_data[0], (list, tuple)):
                        # process a row
                        pdata[n].append(_data)
                    elif isinstance(_data, (list, tuple)) and isinstance(_data[0], (list, tuple)):
                        # process many rows
                        pdata[n].extend(_data)

                # process prepared data
                for n in range(len(pdata)):
                    if len(pdata[n]) >= BATCH_SIZE:
                        err_count += spec['actions'][n](pdata[n], logger)
                        pcount[n] += len(pdata[n])
                        pdata[n].clear()

            if in_format in ('csv', 'json'):
                file.close()
            elif in_format == 'xlsx':
                wb.close()

            if err_count == 0 and (args.delete or spec.get('delete')):
                os.remove(ifile)
            logger.info("%s", ifile)

        # process the rest of prepared data
        for n in range(len(pdata)):
            if pdata[n]:
                err_count += spec['actions'][n](pdata[n], logger)
                pcount[n] += len(pdata[n])
        logger.info("Processed %s of %s rows%s",
            str(pcount).strip('[]'),
            count - spec.get('skip_lines', 0),
            f" WITH {err_count} ERRORS" if err_count else ''
        )

        # set stat data no earlier than all files are successfully processed
        if recent_files:
            stat[spec_name]['mtime'] = latest_mtime
    except:
        logger.exception('EXCEPT')
        if sources[spec['source']].get('con'):
            sources[spec['source']]['con'].rollback()
        return_code = 1
    finally:
        if file:
            file.close()
        if wb:
            wb.close()
    return 1 if err_count else 0


def main():
    logger.info("-- start %s", ' '.join(sys.argv))

    error_count = 0
    _ts = datetime.now().strftime('%Y%m%d%H%M%S')
    trace(_ts, 0)

    if os.path.isfile(STAT_FILE):
        with open(STAT_FILE, encoding='UTF-8') as f:
            stat = json.load(f)
    else:
        stat = dict()

    for spec_name, spec in specs.items():
        if spec_name not in stat:
            stat[spec_name] = {'mtime': 0}
        if SPEC in (spec_name, 'all', *spec.get('tags', [])):
            spec['source'] = spec.get('source', getattr(cfg, 'SOURCE', None))
            if spec['source'] is None:
                logger.error('Skipping spec "%s" with no source', spec_name)
                error_count += 1
                continue
            error_count += process(spec_name, spec, args.in_file, stat)

    for src in sources.values():
        if src.get('up'):
            if src.get('upset') and callable(src['upset']):
                logger.debug("-- upset")
                src['upset']()
            src['up'] = None

    stat = {k: v for k, v in stat.items() if k in cfg.specs}
    with open(STAT_FILE, 'w', encoding='UTF-8') as f:
        f.write(json.dumps(stat))

    trace(_ts, 1 if error_count == 0 else 2)
    logger.info("-- done%s", f" WITH {error_count} ERRORS" if error_count else '')
    sys.exit(error_count)


if __name__ == '__main__':
    main()
