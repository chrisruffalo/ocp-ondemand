# On Demand / One-Touch CICD environment with OCP in EC2

## Prerequisite Amazon Configuration
To fully execute this content the following configuration items need to be completed before execution. If these items are not completed the script will not be able to be executed or will fail during the run.

### IAM Group Policies
In order to execute this Ansible content your user needs to have the following permissions:
* AmazonEC2FullAccess
* AmazonVPCFullAccess
* AmazonRoute53FullAccess
* AWSDirectoryServiceFullAccess

## Ansible Configuration
The bulk of the configuration for the Ansible run is contained in two files. The pulbic/unsecure configuration is in `./group_vars/all/main.yml` and the remaining configuration is in `./group_vars/all/vault.yml`. There is a sample template provided at `./group_vars/all/vault.yml.sample`. Every option must have a value provided or the execution will not be able to complete.

