#!/usr/bin/env python3

import os
import sys
import locale
import glob
import re
import json
import argparse
import logging
from datetime import date
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import smtplib
from jinja2 import Environment, FileSystemLoader, select_autoescape


VERSION = '0.3'

#NOW_TS = datetime.timestamp(datetime.now())

parser = argparse.ArgumentParser(
    description="Create email message and send it to addressees, as specified in cfg-file spec.",
    epilog="Thanks for using %(prog)s!"
)

parser.add_argument("-f", "--force", action="store_true", help="send email unconditionally")
parser.add_argument("-v", "--version", action="version", version="%(prog)s " + VERSION)
parser.add_argument("cfg_file", help="cfg-file name")
parser.add_argument("spec", nargs="?", default="all", help="spec name, defaults to \"all\"")

args = parser.parse_args()

BASEDIR, BASENAME = os.path.split(sys.argv[0])

if not os.path.isfile(args.cfg_file) and not os.path.isfile(args.cfg_file + '.py'):
    sys.stderr.write(
        parser.format_usage() + \
        f"{BASENAME}: error: cfg-file not found: {args.cfg_file}\n"
    )
    sys.exit(1)

TEMPLATES_DIR = os.path.join(BASEDIR, 'conf')
if not os.path.isdir(TEMPLATES_DIR):
    TEMPLATES_DIR = os.path.join(BASEDIR, '..', 'conf')
    if not os.path.isdir(TEMPLATES_DIR):
        sys.stderr.write(
            parser.format_usage() + \
            f"{BASENAME}: error: templates dir not found: {TEMPLATES_DIR}\n"
        )
        sys.exit(1)

#USER_DIR = os.environ.get('HOMEPATH', os.environ.get('HOME', ''))
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

STAT_FILE = os.path.join(TEMP_DIR, f".{CFG_MODULE}.json")
# max number of files per message, both inline and attached
FILES_PER_MESSAGE = 10

HTML_GREETING = \
    getattr(cfg, 'HTML_GREETING', """
<p>Hello!</p><p/>
"""
    )
HTML_SIGNATURE = \
    getattr(cfg, 'HTML_SIGNATURE', """
<p/><p>
Have a good day!<br/>
dbang Utilities<br/>
</p>
"""
    )
TEXT_GREETING = \
    getattr(cfg, 'TEXT_GREETING', """
Hello!

"""
    )
TEXT_SIGNATURE = \
    getattr(cfg, 'TEXT_SIGNATURE', """

Have a good day!
dbang Utilities
"""
    )

env = Environment(
    loader=FileSystemLoader([TEMPLATES_DIR, CFG_DIR]),
    autoescape=select_autoescape(['html', 'xml'])
)


def send_mail(config, mail, body, mail_format, attachments):
    message = MIMEMultipart()
    message['Subject'] = mail['subject']
    message['From'] = config.MAIL_FROM
    message['To'] = ', '.join(mail['to'])
    if mail.get('cc'):
        message['Cc'] = ', '.join(mail['cc'])
    if mail.get('bcc'):
        message['Bcc'] = ', '.join(mail['bcc'])

    part = MIMEText(body, 'html' if mail_format == 'html' else 'plain')
    message.attach(part)

    for attachment in attachments:
        with open(attachment['file'], 'rb') as f:
            part = MIMEBase(*(attachment['MIME'].split('/')))
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f"attachment; filename= {attachment['filename']}",
        )
        message.attach(part)

    try:
        server = smtplib.SMTP(config.MAIL_SERVER)
        server.sendmail(config.MAIL_FROM, mail['to'] + mail.get('cc', []) + mail.get('bcc', []), message.as_string())
    finally:
        server.quit()


def process(spec_name, spec, stat):
    """
    Process spec from config-file.
    """
    return_code = 0
    try:
        mail_format = spec_name.split('.')[1]
        assert (
            mail_format in ('html', 'text')
            and isinstance(spec, dict)
            and {*spec.keys()} >= {'mail'}
            and isinstance(spec['mail'], dict)
            and {*spec['mail'].keys()} >= {'to', 'subject', 'body'}
            and isinstance(spec['mail']['to'], list)
            and isinstance(spec['mail']['subject'], str)
            and isinstance(spec['mail']['body'], (list, dict, str))
            ), \
            f"Bad spec {spec_name}"

        if not isinstance(spec['mail']['body'], list):
            spec['mail']['body'] = [spec['mail']['body']]

        mail = spec['mail']

        # find recently updated files
        stat_ = dict()
        all_files = []
        recent_files = []
        for part in spec['mail']['body'] + spec['mail'].get('attachments', []):
            if isinstance(part, dict) and part.get('file'):
                for file_name in sorted(glob.glob(part['file'])):
                    all_files.append(file_name)
                    file_mtime = os.stat(file_name).st_mtime
                    if not stat[spec_name].get(file_name):
                        stat[spec_name][file_name] = {'mtime': 0, 'offset': 0}
                    if not stat_.get(file_name):
                        stat_[file_name] = {'mtime': file_mtime, 'offset': stat[spec_name][file_name]['offset']}
                    if file_mtime > stat[spec_name][file_name]['mtime']:
                        recent_files.append(file_name)
                        #stat_[file_name]['mtime'] = file_mtime
                if len(all_files) == FILES_PER_MESSAGE:
                    break

        if (not args.force and not spec.get('force') and not recent_files) or not all_files:
            logger.info("%s - No files to send", spec_name)
            return return_code

        if args.force or spec.get('force'):
            target_files = all_files
        else:
            target_files = recent_files

        names = []
        parts = []
        for part in spec['mail']['body']:
            if isinstance(part, dict) and part.get('file'):
                for file_name in sorted(glob.glob(part['file'])):
                    if file_name in target_files:
                        with open(file_name, encoding=part.get('encoding', ENCODING)) as f:
                            content = f.read()
                        if part.get('tail', False):
                            content_size = len(content)
                            if stat[spec_name][file_name]['offset'] > 0:
                                content = content[stat[spec_name][file_name]['offset']:]
                            stat_[file_name]['offset'] = content_size
                        if part.get('clip'):
                            findings = re.findall(part['clip'], content, flags=re.MULTILINE|re.DOTALL)
                            if not findings:
                                continue
                            # strip exactly one \n if any
                            parts.append('\n'.join((f[:-1] if f.endswith('\n') else f) for f in findings))
                        else:
                            parts.append(content)
                        for patt, repl in part.get('substitutions', []):
                            parts[-1] = re.sub(patt, repl, parts[-1], flags=re.MULTILINE|re.DOTALL)
                            #print(repr(parts[-1]))
                        names.append(os.path.basename(file_name) if file_name != part['file'] else None)
            elif isinstance(part, str):
                parts.append(part)
                names.append(None)

        template = env.get_template(spec.get('template') or f"hedwig.{mail_format}.jinja")
        if mail_format == 'html':
            for i, part in enumerate(parts):
                found = re.search(r'<body>(.+)</body>', part, flags=re.MULTILINE|re.DOTALL)
                if found:
                    parts[i] = found[1]
            body = \
                template.render(
                    names=names,
                    parts=parts,
                    greeting=mail.get('greeting', HTML_GREETING),
                    signature=mail.get('signature', HTML_SIGNATURE),
                    zip=zip
                )
        elif mail_format == 'text':
            body = \
                template.render(
                    names=names,
                    parts=parts,
                    greeting=mail.get('greeting', TEXT_GREETING),
                    signature=mail.get('signature', TEXT_SIGNATURE),
                    zip=zip
                )

        attachments = []
        for attachment in mail.get('attachments', []):
            for file_name in sorted(glob.glob(attachment['file'])):
                if file_name in target_files:
                    attachments.append(
                        {
                            'file': file_name,
                            'MIME': attachment.get('MIME') or "application/octet-stream",
                            'filename': attachment.get('filename') or os.path.basename(file_name)
                        }
                    )

        if parts or attachments:
            send_mail(cfg, mail, body, mail_format, attachments)
            logger.info("%s - Sent", spec_name)
        else:
            logger.info("%s - Nothing to send", spec_name)

        # set stat data no earlier than all files are successfully processed
        for k, v in stat_.items():
            stat[spec_name][k] = v
    except:
        logger.exception('EXCEPT')
        return_code = 1
    return return_code


def main():
    logger.info("-- start %s", ' '.join(sys.argv))

    error_count = 0
    if os.path.isfile(STAT_FILE):
        with open(STAT_FILE, encoding='UTF-8') as f:
            stat = json.load(f)
    else:
        stat = dict()

    for spec_name, spec in cfg.specs.items():
        if spec_name not in stat:
            stat[spec_name] = {}
        if SPEC in (spec_name, 'all', *spec.get('tags', [])):
            error_count += process(spec_name, spec, stat)

    stat = {k: v for k, v in stat.items() if k in cfg.specs}
    with open(STAT_FILE, 'w', encoding='UTF-8') as f:
        f.write(json.dumps(stat))

    logger.info("-- done %s", f" WITH {error_count} ERRORS" if error_count else '')
    sys.exit(error_count)


if __name__ == '__main__':
    main()
