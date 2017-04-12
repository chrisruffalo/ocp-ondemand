#!/usr/bin/python

from ansible.module_utils.basic import *

# in 2.3 a playbook can include own modules
from ansible.module_utils.wildfly import *

def main():
    # get base argument spec for wildfly-api support
    argument_spec = wildfly_spec()

    # operation must be supported by module
    argument_spec.update({'operation': dict(required=True, choices=['read', 'set', 'undefine'])})

    # requires a key and value pair to operate on
    argument_spec.update({'key': dict(required=True)})
    argument_spec.update({'value': dict()})

    # create module, using ansible spec
    module = AnsibleModule(argument_spec)

    # decide what to do
    operation = module.params['operation']

    # get other important values
    address = module.params['address']
    key = module.params['key']
    value = module.params['value']

    # do operations
    if operation == 'read':
        wildfly_read_attribute(address, key, module)
    elif operation == 'set':
        # check for value
        if not value:
            module.fail_json(changed=False, success=False, msg="With the set operation a parameter with the name 'value' must be specified.")
        # execute
        wildfly_set_attribute(address, key, value, module)
    elif operation == 'undefine':
        wildfly_undefine_attribute(address, key, module)

def wildfly_read_attribute_request(address, key, module):
    parameters = {'name': key}
    return make_wildfly_request('read-attribute', address, parameters, module)

def wildfly_read_attribute(address, key, module):
    # make request
    json = wildfly_read_attribute_request(address, key, module)

    # resource not found, undefined value
    if json['outcome'] != 'success' or 'failure-description' in json or not 'result' in json:
        value = 'Undefined'
    else:
        value = json['result']

    # return response
    module.exit_json(changed=False, success=True, key=key, value=value)

def wildfly_set_attribute(address, key, value, module):
    # make request to get intitial value
    json = wildfly_read_attribute_request(address, key, module)

    # resource not found, undefined value
    if json['outcome'] != 'success' or 'failure-description' in json or not 'result' in json:
        initial_value = None
    else:
        initial_value = str(json['result'])
        
    # if old value == value, exit
    if value == initial_value or str(value) == str(initial_value):
        # no changes made (value was the same) so success and return value
        module.exit_json(changed=False, success=True, key=key, value=value)

    # command parameters for writing attribute
    parameters = {
        'name': key,
        'value': str(value)
    }

    # write attribute
    json = make_wildfly_request('write-attribute', address, parameters, module)

    # check for failure
    check_json_fail(json, module)

    # exit with change
    module.exit_json(changed=True, success=True, key=key, value=value, previous_value=initial_value)

def wildfly_undefine_attribute(address, key, module):
    # make request to get intitial value
    json = wildfly_read_attribute_request(address, key, module)

    # resource not found, undefined value
    if json['outcome'] != 'success' or 'failure-description' in json or not 'result' in json or json.result == 'undefined':
        module.exit_json(changed=False, success=True, key=key, deleted_value=initial_value)

    # otherwise, delete
    parameters = { 'name': value }
    json = make_wildfly_request('undefine-attribute', address, parameters, module)

    # check for failure
    check_json_fail(json, module)
    
# import basic ansible module stuff
from ansible.module_utils.basic import *

if __name__ == '__main__':  
    main()


