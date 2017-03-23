#!/usr/bin/python

from ansible.module_utils.basic import *
import requests
from requests.auth import HTTPDigestAuth

def main():

    # get base ec2 argument spec
    argument_spec = {}

    argument_spec.update(dict(
        # state
        state = dict(default='present', choices=['present', 'absent']),
        # wildfly-connecty-bits  
        wildfly_host = dict(default='localhost'),
        wildfly_port = dict(default=9990),
        wildfly_username = dict(),
        wildfly_password = dict(no_log=False),
        # datasource specific bits
        datasource_name = dict(required=True),
        datasource_properties = dict(default={}, type='dict')
    )
    )

    # create module, using ansible spec
    module = AnsibleModule(argument_spec)

    # decide what to do
    state = module.params['state']

    if state == 'present':
        has_changed, success, metadata, msg = datasource_create(module)
    else:
        has_changed, success, metadata, msg = datasource_remove(module)

    # module exit
    if not success:
        module.fail_json(changed=has_changed, success=success, msg=err_msg)
    else:
        # fix name
        if not 'name' in metadata:
            metadata['name'] = module.params['datasource_name']
        # return
        module.exit_json(changed=has_changed, success=success, datasource=metadata)


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
            r.json()
        except ValueError as e:
            r.raise_for_status()

        # direct response return                
        return r        
    except requests.exceptions.HTTPError as e:
        module.fail_json(changed=False, success=False, msg="There was an error contacting the wildfly server (" + url + "), " + str(e) + ": " + r.text)

def check_json_fail(json, module, changed=False):
    if json['outcome'] != 'success' or 'failure-description' in json:
        msg = "An unspecified error has occurred"
        if json['failure-description']:
            msg = json['failure-description']
        module.fail_json(changed=changed, success=False, msg=msg)

def get_datasource_by_name(datasource_name, module):
    response = make_wildfly_request(operation="read-resource", address=[{"subsystem": "datasources"}, {"data-source": datasource_name}], parameters=None, module=module)
    json = response.json()

    # datasource not found
    if json['outcome'] != 'success' or 'failure-description' in json or not 'result' in json:
        return None

    # otherwise, return json result
    return json['result']

def datasource_create(module):
    data = module.params

    datasource_name = data['datasource_name']
    datasource_properties = data['datasource_properties']

    # commonly left out or can't remember the right format so we just automagically fix it here
    if not 'jndi-name' in datasource_properties:
        datasource_properties['jndi-name'] = "java:jboss/datasources/" + datasource_name

    # lookup datasource
    datasource = get_datasource_by_name(datasource_name, module)

    # track change
    updated = False

    # we need to add the datasource directly
    if not datasource:
        response = make_wildfly_request(operation="add", address=[{"subsystem": "datasources"}, {"data-source": datasource_name}], parameters=data['datasource_properties'], module=module)
        json = response.json()

        # handle failure response
        check_json_fail(json, module)

        # updated at this point
        updated = True
    else:
        # ok, this is a little tricky... we need to check the incoming parameters and ensure they are set
        # and if they are not set or are different we need to change them by using the write command
        for key, value in datasource_properties.iteritems():
            # if the key is in the data source AND the key has the same value we don't need to write the update
            if not (key in datasource and datasource_properties[key] == datasource[key]):
                # make request and check response
                params = { "name": key, "value": value }
                response = make_wildfly_request(operation="write-attribute", address=[{"subsystem": "datasources"}, {"data-source": datasource_name}], parameters=params, module=module)
                json = response.json()
                check_json_fail(json, module, updated)

                # after one update we need to return 'changed'
                updated = True

    # get datasource again with updated attributes
    datasource = get_datasource_by_name(datasource_name, module)    

    # return response
    return updated, True, datasource, None

def datasource_remove(module):
    data = module.params
    datasource_name = data['datasource_name']

    datasource = get_datasource_by_name(datasource_name, module)

    # we are done here
    if not datasource:
        return False, True, {}, None

    # we need to delete the datasource
    response = make_wildfly_request(operation="remove", address=[{"subsystem": "datasources"}, {"data-source": datasource_name}], parameters=None, module=module)
    json = response.json()

    # failure response
    check_json_fail(json, module)

    # if deleted then we can put the original datasource out in the metdata
    metadata = {}
    metadata['datasource'] = datasource

    return True, True, metadata, None

# import module snippets (same as ec2 module)
from ansible.module_utils.basic import *

if __name__ == '__main__':  
    main()