#!/usr/bin/python

from ansible.module_utils.basic import *
import requests
from requests.auth import HTTPDigestAuth

# in 2.3 a playbook can include own modules
from ansible.module_utils.wildfly import *

def main():
    # get base argument spec for wildfly-api support
    argument_spec = wildfly_spec()

    # delete before re-adding
    argument_spec.update({'delete_first': dict(default=False)}),
    # operation must be supported by module
    argument_spec.update({'operation': dict(required=True, choices=['read', 'present', 'absent'])})
    # parameters to operate on resource
    argument_spec.update({'parameters': dict(type='dict')})

    # create module, using ansible spec
    module = AnsibleModule(argument_spec)

    # decide what to do
    operation = module.params['operation']

    # get other important values
    address = module.params['address']
    parameters = module.params['parameters']

    # do operations
    if operation == 'read':
        wildfly_read(address, parameters, module)
    elif operation == 'present':
        wildfly_present(address, parameters, module)
    elif operation == 'absent':
        wildfly_present(address, module)

def wildfly_read(address, parameters, module):
    # we have a result
    result = make_read_request(address, module)

    # return result payload as response
    module.exit_json(changed=False, success=True, result=result)

def wildfly_present(address, parameters, module):
    result = make_read_request(address, module)

    # not updated until something changed
    updated = False 

    # when 'delete_first' is set as an option we need to delete the item if it exists
    if module.params['delete_first'] == True and result:
        make_delete_request(address, module)
        result = None
        updated = True

    updated_properties = None

    # if no result was found then we can, in a straightforward way, add the item
    if not result:
        json = make_wildfly_request(operation="add", address=address, parameters=parameters, module=module)
        check_json_fail(json, module, updated)
        updated = True
    # if a result was found then we need to go about updating/adding properties individually
    else:
        property_result = write_wildfly_attributes(result, parameters, address, module)
        updated = property_result['updated']
        updated_properties = property_result['properties']

    # re-read with updated attributes if an update was made
    if updated:
        result = make_read_request(address, module)

    # exit with return result
    module.exit_json(changed=updated, success=True, result=result, updated_properties=updated_properties)

def wildfly_absent(address, module):
    result = make_read_request(address, module)    

    # if there is no result then nothing to do
    if not result:
        module.exit_json(changed=False, success=True)

    delete_result = make_delete_request(address, module)

    # return ok
    module.exit_json(changed=True, success=True, deleted=result, metadata=delete_result)

def make_delete_request(address, module):
    # make the request
    delete_result = make_wildfly_request(operation='remove', address=address, parameters=None, module=module)

    # check for errors
    check_json_fail(delete_result, module)

    return delete_result    

def make_read_request(address, module):
    json = make_wildfly_request(operation='read-resource', address=address, parameters=None, module=module)

    # resource not found
    if json['outcome'] != 'success' or 'failure-description' in json or not 'result' in json:
        return None

    result = json['result']

    # remove nonsense way that expresion value items are returned in rest api
    for key, value in result.iteritems():
        if value and type(value) is dict and 'EXPRESSION_VALUE' in value:
            value = value['EXPRESSION_VALUE']
            result[key] = value

    return result

def write_wildfly_attributes(found_object, input_parameters, address, module):
    updated = False

    updated_properties = []

    for key, value in input_parameters.iteritems():
        # if the key is in the data source AND the key has the same value we don't need to write the update
        if not (key in found_object and value == found_object[key]):
            # make request and check response
            update_params = { "name": key, "value": value }
            json = make_wildfly_request(operation="write-attribute", address=address, parameters=update_params, module=module)

            check_json_fail(json, module, updated)

            updated_properties.append(key)

            # after one update we need to return 'changed'
            updated = True or updated

    # return if it was updated or not
    return {"updated": updated, "properties": updated_properties}

# import basic ansible module stuff
from ansible.module_utils.basic import *

if __name__ == '__main__':  
    main()