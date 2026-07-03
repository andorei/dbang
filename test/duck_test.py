import os
import sys

import requests

#
# Run sanity test with command line
#     duck.py conf/duck_test.py
# and log file in subdirectory log.
#

#
# SETTINGS USED BY duck
#
# defaults to current working directory
IN_DIR = os.path.join(os.path.dirname(__file__), '..', 'in')
# defaults to False
DEBUGGING = True
# defaults to False
LOGGING = True
# defaults to current working directory
LOG_DIR = os.path.join(os.path.dirname(__file__), '..', 'log')
# output encoding defaults to OS locale encoding
ENCODING = 'UTF-8'
# defaults to 'excel'
#CSV_DIALECT = 'excel'
# defaults to the dialect delimiter
CSV_DELIMITER = ';'
# number of loads preserved per spec defaults to 10
#PRESERVE_N_LOADS = 10
# data source
SOURCE = "dummy"

#
# SETTINGS USED IN specs
#
#HEADERS = { # boobl-goom.WebsiteTEST
#    'Content-Type': 'application/json; charset=utf-8',
#    'Accept': 'application/json',
#    'Authorization': 'SecretKey SBVkiSPGbkN3tQbd87pBSkXEWEuRpfAc'
#}
HEADERS = { # boobl-goom.Offline
    'Content-Type': 'application/json; charset=utf-8',
    'Accept': 'application/json',
    'Authorization': 'SecretKey 0hVKSuiGlP7c4gYgrS23WzAZY44XjwaG'
}



#
# Actions
#
def register_client(rows, logger):
    #URL = 'https://api.mindbox.ru/v3/operations/sync?endpointId=boobl-goom.WebsiteTEST&operation=CRMCustomerRegistration'
    URL = 'https://api.mindbox.ru/v3/operations/async?endpointId=boobl-goom.Offline&operation=CRMCustomerRegistration'

    error_count = 0
    for row in rows:
        payload = {
            "pointOfContact": row['site_code'],
            "customer": {
                "mobilePhone": row['phone'],
                "discountCard": {"ids": {"number": row['card_num']}},
                "timeZone": row['tz_name'],
                "area": {"ids": {"externalId": row['city_code']}},
                "customFields": {"city": row['city_name']},
                "ids": {"clientIDOffline": row['cust_id']}
            }
        }
        if row['first_name']:
            payload['customer']['firstName'] = row['first_name']
        if row['middle_name']:
            payload['customer']['middleName'] = row['middle_name']
        if row['last_name']:
            payload['customer']['lastName'] = row['last_name']
        if row['birthdate']:
            payload['customer']['birthDate'] = row['birthdate']
        if row['sex']:
            payload['customer']['sex'] = row['sex']
        if row['email']:
            payload['customer']['email'] = row['email']
        if row['agree_email'] or row['agree_sms']:
            payload['customer']['subscriptions'] = []
            if row['agree_email']:
                payload['customer']['subscriptions'].append({"pointOfContact": "email"})
            if row['agree_sms']:
                payload['customer']['subscriptions'].append({"pointOfContact": "SMS"})

        try:
            r = requests.post(URL, headers=HEADERS, json=payload)
            if r.status_code == 200:
                logger.debug('client: %s: %s' % (r.json(), payload['customer']['mobilePhone']))
            else:
                logger.error('client: %s: %s' % (r, payload))
                error_count += 1
        except Exception:
            logger.exception('client: %s: EXCEPT' % payload)
            error_count += 1

    return error_count


def print_ok(rows, logger):
    if DEBUGGING:
        logger.debug('print_ok')
    error_count = 0
    for row in rows:
        print(row)
        break
    return error_count


def print_err(rows, logger):
    if DEBUGGING:
        logger.debug('print_err')
    return 1


specs = {
    "print_csv": {
        "tags": ['print'],
        "file": "test.csv",
        "actions": print_ok
    },
    "print_json": {
        "tags": ['print'],
        "file": "test.json",
        "actions": print_ok
    },
    "print_xlsx": {
        "tags": ['print'],
        "file": "test.xlsx",
        "actions": print_ok
    },
    "print_err": {
        "tags": ['print', 'error'],
        "file": "test.csv",
        "actions": print_err
    },
}


sources = {
    'dummy': {}
}
