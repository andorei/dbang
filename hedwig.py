#!/usr/bin/python3

import os
import sys
import re
import json
import logging
from datetime import date, datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import smtplib


DEBUGGING = True
LOGSTDOUT = False

NOW_TS = datetime.timestamp(datetime.now())

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

SPEC = sys.argv[2] if len(sys.argv) == 3 else 'all'
if SPEC not in [*cfg.specs.keys(), 'all']:
    sys.stderr.write(
        f"""
        Error: Spec {SPEC} not found in config-file.
        Usage: {BASENAME} <cfg-file> [<spec> | all]
        """
    )
    sys.exit(1)

STAT_FILE = os.path.join(CFG_DIR, f'.{CFG_NAME}.json')
BASENAME = os.path.basename(sys.argv[0]).split('.')[0]
LOG_FILE = os.path.join(SCRIPT_DIR, 'log', f'{date.today().isoformat()}_{BASENAME}.log')

logging.basicConfig(
    filename=None if LOGSTDOUT else LOG_FILE,
    format='%(asctime)s:%(levelname)s:%(name)s:%(message)s',
    level=logging.INFO
)
logger = logging.getLogger(BASENAME)


def send_mail(cfg, mail, body):
    # Create message container - the correct MIME type is multipart/alternative.
    msg = MIMEMultipart('alternative')
    msg['Subject'] = mail['subject']
    msg['From'] = cfg.MAIL_FROM
    msg['To'] = mail['to']
    if mail.get('cc'):
        msg['Cc'] = mail['cc']
    if mail.get('bcc'):
        msg['Bcc'] = mail['bcc']
    # Create html part and attach it to the message
    part = MIMEText(body, 'html')
    msg.attach(part)
    try:
        server = smtplib.SMTP(cfg.MAIL_SERVER)
        server.sendmail(cfg.MAIL_FROM, mail['to'], msg.as_string())
    finally:
        server.quit()


def process(spec_name, spec, stat):
    try:
        assert (
            isinstance(spec, dict)
            and {*spec.keys()} >= {'mail'}
            and isinstance(spec['mail'], dict)
            and {*spec['mail'].keys()} >= {'to', 'subject', 'sources'}
            and isinstance(spec['mail']['to'], str)
            and isinstance(spec['mail']['subject'], str)
            and isinstance(spec['mail']['sources'], list)
            ), \
            f"Bad spec {spec_name}"

        mail = spec['mail']

        # find latest file modification time 
        latest_mtime = stat[spec_name]
        for source in spec['mail']['sources']:
            assert \
                source.get('file.html', source.get('html')), \
                f"Bad or empty source in spec {spec_name}"
            if source.get('file.html'):
                if os.path.isfile(source['file.html']):
                    latest_mtime = max(latest_mtime, os.stat(source['file.html']).st_mtime)
                else:
                    logger.info(f"{spec_name} - No file")

        if stat[spec_name] < latest_mtime:

            # read all source docs and make substitutions
            docs = []
            for source in spec['mail']['sources']:
                if source.get('file.html'):
                    with open(source['file.html'], encoding=source.get('encoding', cfg.HTML_ENCODING)) as f:
                        docs.append(f.read())
                elif source.get('html'):
                    docs.append(source['html'])
                for patt, repl in source.get('substitutions', []):
                    docs[-1] = re.sub(patt, repl, docs[-1])

            # combine all source docs into one
            body = docs[0]
            for doc in docs[1:]:
                found = re.search(r'<body>(.+</body>)', doc, flags=re.DOTALL)
                if found:
                    body = body.replace('</body>', found[1])

            # compose email message as specified
            greeting = mail.get('greeting', cfg.MAIL_GREETING)
            if greeting:
                body = body.replace('<body>', '<body>\n' + greeting)
            if mail.get('finally'):
                body = body.replace('</body>', mail['finally'] + '\n</body>')
            signature = mail.get('signature', cfg.MAIL_SIGNATURE)
            if signature:
                body = body.replace('</body>', signature + '\n</body>')

            send_mail(cfg, mail, body)
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
