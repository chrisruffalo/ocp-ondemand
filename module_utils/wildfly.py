#!/usr/bin/python

from ansible.module_utils.basic import *
import requests
from requests.auth import HTTPDigestAuth

def wildfly_spec():
    argument_spec = {}
    argument_spec.update(dict(
        # wildfly-connecty-bits  
        host = dict(default='localhost'),
        port = dict(default=9990),
        username = dict(),
        password = dict(no_log=True),
        # address of resource
        address = dict(type='list')
    )
    )

    return argument_spec

def make_wildfly_request(operation, address, parameters, module):
    # data
    data = module.params

    # validate data
    if data['username']:
        if not data['password']:
            module.fail_json(changed=False, success=False, msg="If the module parameter `username` is provided a `password` must also be provided")
        auth = HTTPDigestAuth(data['username'], data['password'])
    else:
        auth = None

    # the url to request
    url = "http://" + data['host'] + ":" + data['port'] + "/management"

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
            # get and check json for failure
            return r.json()
        except ValueError as e:
            r.raise_for_status()
            # uhoh - status not raised
            module.fail_json(changed=False, success=False, msg="The response from the server did not contain valid JSON: " + r.text)
    except requests.exceptions.HTTPError as e:
        module.fail_json(changed=False, success=False, msg="There was an the making a request to `" + url + "`, " + str(e) + ": " + r.text)    

def check_json_fail(json, module, changed=False):
    if not json:
        module.fail_json(changed=changed, success=False, msg="A null response was not expected")

    if not 'outcome' in json or json['outcome'] != 'success' or 'failure-description' in json:
        msg = "An unspecified error has occurred"
        if json['failure-description']:
            msg = json['failure-description']
        module.fail_json(changed=changed, success=False, msg=msg)