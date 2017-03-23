#!/usr/bin/python

from ansible.module_utils.basic import *
import requests
from requests.auth import HTTPDigestAuth

def wildfly_spec():
    argument_spec = {}
    argument_spec.update(dict(
        # wildfly-connecty-bits  
        wildfly_host = dict(default='localhost'),
        wildfly_port = dict(default=9990),
        wildfly_username = dict(),
        wildfly_password = dict(no_log=False),
    )
    )

    return argument_spec

def make_wildfly_request(operation, address, parameters, module):
    # data
    data = module.params

    # validate data
    if data['wildfly_username']:
        if not data['wildfly_password']:
            module.fail_json(changed=False, success=False, msg="If the value `wildfly_username` is provided a `wildfly_password` must also be provided")

        auth = HTTPDigestAuth(data['wildfly_username'], data['wildfly_password'])
    else:
        auth = None

    # the url to request
    url = "http://" + data['wildfly_host'] + ":" + data['wildfly_port'] + "/management"

    # create payload from inputs
    payload = {}
    if parameters:
        payload = parameters.copy()
    payload['operation'] = operation
    payload['address'] = address

    # create headers
    headers = {"Content-Type": "application/json"}

    # make request
    try: 
        if auth:
            # make authenticated request
            r = requests.post(url, headers=headers, json=payload, auth=auth)
        else:
            # make unauthenticated request
            r = requests.post(url, headers=headers, json=payload)
        
        # if there is no readable json content then we need to 
        # raise up the status, if there is content we can continue
        try:
            return r.json()
        except ValueError as e:
            r.raise_for_status()
            # uhoh - status not raised
            module.fail_json(changed=False, success=False, msg="The response from the server did not contain valid JSON: " + r.text)
    except requests.exceptions.HTTPError as e:
        module.fail_json(changed=False, success=False, msg="There was an the making a request to `" + url + "`, " + str(e) + ": " + r.text)

def check_json_fail(json, module, changed=False):
    if json['outcome'] != 'success' or 'failure-description' in json:
        msg = "An unspecified error has occurred"
        if json['failure-description']:
            msg = json['failure-description']
        module.fail_json(changed=changed, success=False, msg=msg)
