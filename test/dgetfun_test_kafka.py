import os
import sys
import logging

import requests

from sources import sources


DEBUGGING = True
LOGGING = True
OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'out')
LOG_DIR = os.path.join(os.path.dirname(__file__), '..', 'log')
ENCODING = 'UTF-8'


# Kafka stuff ##################################################################

CLIENT_CODE = 'TEST'
PROXY_NODES = ['http://rukafka1.md.int:8082', 'http://rukafka2.md.int:8082', 'http://rukafka3.md.int:8082']
#PROXY_NODES = ['http://rukafka3.md.int:8082']

OVERRIDE_OFFSET = False
SUBSCRIBE_OR_ASSIGN = 'ASSIGN'
CONF_DIR = os.path.join(os.path.dirname(__file__), '..', 'conf')

klogger = logging.getLogger('kafka')


def write_conf_file(filename, content):
    conf_file = os.path.join(CONF_DIR, filename)
    with open(conf_file, 'w', encoding='utf-8') as f:
        f.write(content)


def read_conf_file(filename):
    conf_file = os.path.join(CONF_DIR, filename)
    try:
        with open(conf_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        content = None
    return content


def next_node(node=None):
    if node in PROXY_NODES:
        i = (PROXY_NODES.index(node) + 1) % len(PROXY_NODES)
    else:
        i = 0
    write_conf_file('kafka.node', PROXY_NODES[i])
    return PROXY_NODES[i]


def curr_node():
    node = read_conf_file('kafka.node')
    if node in PROXY_NODES:
        return node
    else:
        return next_node()


proxy_node = curr_node()

def create_consumer(c_url, c_group, c_instance, content_type, retry=5):
    global proxy_node

    for i in range(retry, 0, -1):
        try:
            response = requests.post(
                '{}/consumers/{}'.format(c_url, c_group),
                headers={'Content-Type': 'application/vnd.kafka.v2+json'},
                json={
                    "name": c_instance,
                    "format": content_type,
                    "auto.offset.reset": "earliest",
                    "auto.commit.enable": True
                },
                timeout=60
            )
            break
        except:
            if i > 1:
                time.sleep(5)
                klogger.info('-- a) % : retry %s' % (c_group, i))
                continue
            else:
                klogger.exception('EXCEPT')
                # switch proxy node and return
                proxy_node = next_node(proxy_node)
                return None
    return response


def subscribe_or_assign(c_url, c_group, c_instance, c_topic, retry=5):
    global proxy_node

    for i in range(retry, 0, -1):
        try:
            if SUBSCRIBE_OR_ASSIGN == 'SUBSCRIBE':
            # Subscribe to c_topics[0]
                response = requests.post(
                    '{}/consumers/{}/instances/{}/subscription'.format(c_url, c_group, c_instance),
                    headers={'Content-Type': 'application/vnd.kafka.v2+json'},
                    json={"topics": [c_topic]},
                    timeout=60
                )
            else:
                # Assign partition 0 of c_topics[0]
                response = requests.post(
                    '{}/consumers/{}/instances/{}/assignments'.format(c_url, c_group, c_instance),
                    headers={'Content-Type': 'application/vnd.kafka.v2+json'},
                    json={"partitions": [{"topic": c_topic, "partition": 0}]},
                    timeout=60
                )
            break
        except:
            if i > 1:
                time.sleep(5)
                klogger.info('-- b) %s : retry %s' % (c_group, i))
                continue
            else:
                klogger.exception('EXCEPT')
                # switch proxy node and return
                proxy_node = next_node(proxy_node)
                return None
    return response


def consume(kasp, retry=5):
    global proxy_node
    content_type = kasp.get('content_type', 'avro')

    assert content_type in ('avro', 'json'), 'Content type should be either avro or json.'

    c_url = kasp.get('proxy_node', proxy_node)
    c_topic = kasp.get('topic', key)
    c_group = kasp.get('group', '%s_%s' % (CLIENT_CODE.lower(), c_topic))
    c_instance = kasp.get('instance', '%s_%s_1' % (CLIENT_CODE.lower(), c_topic))
    c_batch_size = kasp.get('batch_size')
    c_max_files = kasp.get('max_files')
    #klogger.info('-- get %s' % c_topic)

    try:

        response = subscribe_or_assign(c_url, c_group, c_instance, c_topic)
        if response is None:
            return

        if 404 == response.status_code and response.json().get('error_code') == 40403:
            # 404 Error code 40403 - Consumer instance not found.
            klogger.info('-- create consumer group %s' % c_group)
            response = create_consumer(c_url, c_group, c_instance, content_type)
            if response is None:
                return

            if not 200 <= response.status_code < 300 and response.status_code != 409:
                # 409 Error code 40902 – Consumer instance with the specified name already exists
                klogger.error('a) Kafka %s' % response + (' ' + response.text if response.text else ''))
                return

            response = subscribe_or_assign(c_url, c_group, c_instance, c_topic)
            if response is None:
                return

        if not 200 <= response.status_code < 300:
            klogger.error('b) Kafka %s' % response + (' ' + response.text if response.text else ''))
            return

        try:
            node, offset = read_conf_file("%s.offset" % c_group).split(';')
        except:
            node = None
            offset = None
        if node and offset and (node != proxy_node or OVERRIDE_OFFSET):
            # Override offset for the consumer group
            offset = int(offset)

            for i in range(retry, 0, -1):
                try:
                    response = requests.post(
                        '{}/consumers/{}/instances/{}/positions'.format(c_url, c_group, c_instance),
                        headers={'Content-Type': 'application/vnd.kafka.v2+json'},
                        json={"offsets": [{"topic": c_topic, "partition": 0, "offset": offset}]},
                        timeout=60
                    )
                    break
                except:
                    if i > 1:
                        time.sleep(5)
                        klogger.info('-- c) %s : retry %s' % (c_group, i))
                        continue
                    else:
                        klogger.exception('EXCEPT')
                        # switch proxy node and return
                        proxy_node = next_node(proxy_node)
                        return

            if not 200 <= response.status_code < 300:
                klogger.error('c) Kafka %s' % response + (' ' + response.text if response.text else ''))
                return
            if DEBUGGING:
                klogger.info('%15s:%15s: set %s' % (c_group, c_topic, offset))
            write_conf_file("%s.offset" % c_group, "%s;%s" % (proxy_node, offset))

        # Consume messages
        seqnum = 0
        offset = None
        while True:
            for i in range(retry, 0, -1):
                try:
                    response = requests.get(
                        '{}/consumers/{}/instances/{}/records'.format(c_url, c_group, c_instance),
                        headers={'Accept': 'application/vnd.kafka.' + content_type + '.v2+json'},
                        timeout=60
                    )
                    break
                except:
                    if i > 1:
                        time.sleep(5)
                        klogger.info('-- d) %s : retry %s' % (c_group, i))
                        continue
                    else:
                        klogger.exception('EXCEPT')
                        # switch proxy node and return
                        proxy_node = next_node(proxy_node)
                        return

            if response.status_code == 200:
                # [{'topic': 'avrotest', 'key': None, 'value': {'name': 'Andrei'}, 'partition': 0, 'offset': 8235}]     
                records = response.json()
                if records:
                    yield records
                else:
                    break
            else:
                klogger.error('d) Kafka %s' % response + (' ' + response.text if response.text else ''))
                break

        if offset:
            write_conf_file("%s.offset" % c_group, "%s;%s" % (proxy_node, offset + 1))

        # commit all consumed messages
        #response = requests.post(
        #    '{}/consumers/{}/instances/{}/offsets'.format(c_url, c_group, c_instance),
        #    headers={'Content-Type': 'application/vnd.kafka.v2+json'},
        #    timeout=60
        #)
        #if not 200 <= response.status_code < 300:
        #    klogger.error('e) Kafka %s' % response + (' ' + response.text if response.text else ''))
        #    return

    except:
        klogger.exception('EXCEPT')


def cn_evt():
    return consume(
        {
            #"content_type": "avro",
            #"proxy_node": 'http://kafka.my:8082',
            "topic": "stock_evt"
            #"group": "<client_code>_<topic>",
            #"instance": "<client_code>_<topic>_1",
        }
    )


specs = {
    "cn_evt": {
        "source": cn_evt,
        "file": "%(datetime)s_%(seqn)s_cn_evt.json",
        "rows_per_file": 100,
        "max_files": 50, # XXX
        "pass_lines": True
    },
}
