#!/usr/bin/python
# using https://github.com/ansible/ansible/blob/devel/lib/ansible/modules/cloud/amazon/ec2.py as a template
# and https://github.com/ansible/ansible/blob/devel/lib/ansible/modules/cloud/amazon/ec2_vpc_nat_gateway.py too!

from ansible.module_utils.basic import *

# ensure boto is present
try:
    import botocore
    import boto3
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

def main():

    # get base ec2 argument spec
    argument_spec = ec2_argument_spec()

    argument_spec.update(dict(
        state = dict(default='present', choices=['present', 'absent']),
        name = dict(),
        short_name = dict(required = True),
        password = dict(no_log=True),
        description = dict(default=''),
        size = dict(default='Small', choices=['Small', 'Large']),
        vpcId = dict(),
        subnets = dict(type='list')
    )
    )

    # choices (present or absent)
    choice_map = {
      "present": ds_createdirectory_present,
      "absent": ds_createdirectory_absent, 
    }

    # create module, using ansible spec
    module = AnsibleModule(argument_spec)

    # no BOTO was not found
    if not HAS_BOTO:
        module.fail_json(msg='botocore/boto3 required for this module')

    # get client
    try:
        region, ec2_url, aws_connect_kwargs = (
            get_aws_connection_info(module, boto3=True)
        )
        client = (
            boto3_conn(
                module, conn_type='client', resource='ds',
                region=region, endpoint=ec2_url, **aws_connect_kwargs
            )
        )
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Boto3 Client Error - " + str(e.msg))

    # do module based on choice
    success, has_changed, metadata, err_msg = choice_map.get(module.params['state'])(client, module.params)

    # module exit
    if not success:
        module.fail_json(changed=has_changed, success=success, msg=err_msg)
    else:
        module.exit_json(changed=has_changed, success=success, **metadata)

# matches on short name
def ds_is_directory_present(client, data):
    # describe current directories
    response = client.describe_directories()

    # determine if a DS with short name provided is available
    short_name = data['short_name']

    # scan directories
    for directory in response['DirectoryDescriptions']:
        if directory['ShortName'] == short_name:
            return True, directory

    return False, None

def ds_createdirectory_present(client, data):
    # check if the directory exists
    exists, directory = ds_is_directory_present(client, data)

    # if the directory exists, just return some details
    if exists and not "Deleting" == directory['Stage']:
        return True, False, directory, None

    # if name is null (and if description is null) they are both = short_name
    short_name = data['short_name']

    if not data['description']:
        data['description'] = short_name

    if not data['name']:
        data['name'] = short_name

    # request
    directory_request = {
        "Name": data['name'],
        "ShortName": short_name,
        "Password": data['password'],
        "Description": data['description'],
        "Size": data['size'],
        "VpcSettings": {
            "VpcId": data['vpcId'],
            "SubnetIds": data['subnets']
        }
    }

    # now we can create the directory
    # see: https://docs.aws.amazon.com/directoryservice/latest/devguide/API_CreateDirectory.html
    # see: https://boto3.readthedocs.io/en/latest/reference/services/ds.html#DirectoryService.Client.create_directory
    try:
        create_response = client.create_directory(**directory_request)
    except botocore.exceptions.ClientError as e:
        return False, False, None, str(e)

    # get id from response
    directory_id = create_response['DirectoryId']

    # look up details
    describe_request = {"DirectoryIds": [directory_id]}
    try:
        response = client.describe_directories(**describe_request)
    except botocore.exceptions.ClientError as e:
        return False, False, None, str(e)

    # return the description
    return True, True, response['DirectoryDescriptions'][0], ""

def ds_createdirectory_absent(client, data):

    # check if the directory exists
    exists, directory = ds_is_directory_present(client, data)

    # if the directory does not exist just return success without change
    if not exists or "Deleting" == directory['Stage']:
        return True, False, {}, None

    # get directory id
    directory_id = directory['DirectoryId']

    # request
    directory_delete_request = { "DirectoryId": directory_id }

    # if the directory does exist do something about it
    # see: https://boto3.readthedocs.io/en/latest/reference/services/ds.html#DirectoryService.Client.delete_directory
    try:
        create_response = client.delete_directory(**directory_delete_request)
    except botocore.exceptions.ClientError as e:
        return False, False, None, str(e)

    return True, False, directory_delete_request, None

# import module snippets (same as ec2 module)
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

if __name__ == '__main__':  
    main()