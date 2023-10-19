#!/usr/bin/python3

import os
import sys
import re
import json
import argparse
import logging
from datetime import date, datetime
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import smtplib


VERSION = '0.2'

NOW_TS = datetime.timestamp(datetime.now())

parser = argparse.ArgumentParser(
    description="Create email message and send it to addressees, as specified in cfg-file spec.",
    epilog="Thanks for using %(prog)s!"
)

parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + VERSION)
parser.add_argument("cfg_file", help="cfg-file name")
parser.add_argument("spec", nargs="?", default="all", help="spec name, defaults to \"all\"")

args = parser.parse_args()

BASENAME = os.path.basename(sys.argv[0])
SCRIPT_DIR = os.path.dirname(os.path.realpath(sys.argv[0]))
CFG_DIR = os.path.join(SCRIPT_DIR, 'cfg')
CFG_NAME = args.cfg_file.split('.')[0]
CFG_FILE = f"{CFG_NAME}.py"
if not os.path.isfile(os.path.join(CFG_DIR, CFG_FILE)):
    sys.stderr.write(
        parser.format_usage() + \
        f"{BASENAME}: error: cfg-file not found: {CFG_FILE}\n"
    )
    sys.exit(1)

sys.path.append(CFG_DIR)
cfg = __import__(CFG_NAME)

SPEC = args.spec
if SPEC not in [*cfg.specs.keys(), 'all']:
    sys.stderr.write(
        parser.format_usage() + \
        f"{BASENAME}: error: spec not found in cfg-file: {SPEC}\n"
    )
    sys.exit(1)

STAT_FILE = os.path.join(CFG_DIR, f'.{CFG_NAME}.json')
BASENAME = os.path.basename(sys.argv[0]).split('.')[0]
LOG_FILE = os.path.join(SCRIPT_DIR, 'log', f'{date.today().isoformat()}_{BASENAME}.log')
DEBUGGING = getattr(cfg, 'DEBUGGING', False)
LOGSTDOUT = getattr(cfg, 'LOGSTDOUT', False)

logging.basicConfig(
    filename=None if LOGSTDOUT else LOG_FILE,
    format='%(asctime)s:%(levelname)s:%(name)s:%(message)s',
    level=logging.INFO
)
logger = logging.getLogger(BASENAME)


def send_mail(cfg, mail, body, mail_format, attachments):
    message = MIMEMultipart()
    message['Subject'] = mail['subject']
    message['From'] = cfg.MAIL_FROM
    message['To'] = mail['to']
    if mail.get('cc'):
        message['Cc'] = mail['cc']
    if mail.get('bcc'):
        message['Bcc'] = mail['bcc']

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
        server = smtplib.SMTP(cfg.MAIL_SERVER)
        server.sendmail(cfg.MAIL_FROM, mail['to'], message.as_string())
    finally:
        server.quit()


def process(spec_name, spec, stat):
    try:
        mail_format = spec_name.split('.')[1]
        assert (
            mail_format in ('html', 'text', 'txt')
            and isinstance(spec, dict)
            and {*spec.keys()} >= {'mail'}
            and isinstance(spec['mail'], dict)
            and {*spec['mail'].keys()} >= {'to', 'subject', 'body'}
            and isinstance(spec['mail']['to'], str)
            and isinstance(spec['mail']['subject'], str)
            and isinstance(spec['mail']['body'], (list, dict, str))
            ), \
            f"Bad spec {spec_name}"

        if not isinstance(spec['mail']['body'], list):
            spec['mail']['body'] = [spec['mail']['body']]

        mail = spec['mail']

        # find latest file modification time 
        latest_mtime = stat[spec_name]
        for part in spec['mail']['body'] + spec['mail'].get('attachments', []):
            if isinstance(part, dict):
                if part.get('file'):
                    if os.path.isfile(part['file']):
                        latest_mtime = max(latest_mtime, os.stat(part['file']).st_mtime)
                    else:
                        logger.info(f"{spec_name} - No file")

        if stat[spec_name] < latest_mtime or spec['mail'].get('always'):

            parts = []
            for part in spec['mail']['body']:
                if isinstance(part, dict) and part.get('file'):
                    with open(part['file'], encoding=part.get('encoding', cfg.ENCODING)) as f:
                        parts.append(f.read())
                    for patt, repl in part.get('substitutions', []):
                        parts[-1] = re.sub(patt, repl, parts[-1])
                elif isinstance(part, str):
                    parts.append(part)

            if mail_format == 'html':
                # combine all parts into body
                body = parts[0]
                for part in parts[1:]:
                    found = re.search(r'<body>(.+</body>)', part, flags=re.DOTALL)
                    if found:
                        body = body.replace('</body>', found[1])
                # compose email message
                greeting = mail.get('greeting', cfg.HTML_GREETING)
                if greeting:
                    body = body.replace('<body>', '<body>\n' + greeting)
                if mail.get('finally'):
                    body = body.replace('</body>', mail['finally'] + '\n</body>')
                signature = mail.get('signature', cfg.HTML_SIGNATURE)
                if signature:
                    body = body.replace('</body>', signature + '\n</body>')
            else: # mail_format in ('txt', 'text')
                body = '\n'.join(parts)
                body = \
                    mail.get('greeting', cfg.TEXT_GREETING) + \
                    body + \
                    mail.get('finally', '') + \
                    mail.get('signature', cfg.TEXT_SIGNATURE)

            attachments = []
            for attachment in mail.get("attachments", []):
                if not attachment.get("MIME"):
                    attachment["MIME"] = "application/octet-stream"
                if not attachment.get("filename"):
                    attachment["filename"] = os.path.basename(attachment["file"])
                attachments.append(attachment)

            send_mail(cfg, mail, body, mail_format, attachments)
            logger.info(f"{spec_name} - Sent")
            stat[spec_name] = NOW_TS

        else:
            logger.info(f"{spec_name} - No new file(s)")


    except:
        logger.exception('EXCEPT')


def main():
    logger.info(f'-- start {" ".join(sys.argv)}')

    if os.path.isfile(STAT_FILE):
        with open(STAT_FILE, encoding="UTF-8") as f:
            stat = json.load(f)
    else:
        stat = dict()

    for spec_name, spec in cfg.specs.items():
        if spec_name not in stat:
            stat[spec_name] = 0
        if SPEC in (spec_name, 'all'):
            process(spec_name, spec, stat)

    stat = {k: v for k, v in stat.items() if k in cfg.specs}
    with open(STAT_FILE, "w", encoding="UTF-8") as f:
        f.write(json.dumps(stat))

    logger.info('-- done')


if __name__ == '__main__':
    main()
