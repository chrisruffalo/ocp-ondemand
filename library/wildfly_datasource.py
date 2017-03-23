#!/usr/bin/python

from ansible.module_utils.basic import *
from ansible.module_utils.wildfly import *

def main():
    # get base argument spec for wildfly-api support
    argument_spec = wildfly_spec()

    argument_spec.update(dict(
        # state
        state = dict(default='present', choices=['present', 'absent']),
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

def get_datasource_by_name(datasource_name, module):
    json = make_wildfly_request(operation="read-resource", address=[{"subsystem": "datasources"}, {"data-source": datasource_name}], parameters=None, module=module)

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
        json = make_wildfly_request(operation="add", address=[{"subsystem": "datasources"}, {"data-source": datasource_name}], parameters=data['datasource_properties'], module=module)

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
                json = make_wildfly_request(operation="write-attribute", address=[{"subsystem": "datasources"}, {"data-source": datasource_name}], parameters=params, module=module)

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
    json = make_wildfly_request(operation="remove", address=[{"subsystem": "datasources"}, {"data-source": datasource_name}], parameters=None, module=module)

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