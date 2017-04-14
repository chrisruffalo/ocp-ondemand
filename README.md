# On Demand / Low-Touch OCP environment in EC2

## Prerequisites
* Ansible
* Money
* Git

## A WARNING!
This costs money to do. It spins up a bunch of instances and it will add up quickly. This is not a cheap thing but it aims to be a fast and correct implementation in EC2 from minimal configuration.

## Local Configuration
There are several things you will need to perform locally to execute this content. It aims to be a minimal touch solution but there are still human interactions that are required at various points.

### Preparing the local Environment
Create a directory inside of this directory called `static`. Change into that directory and check out the OCP content with `git clone https://github.com/openshift/openshift-ansible.git`.

### Ansible Configuration
The bulk of the configuration for the Ansible run is contained in two files. The pulbic/unsecure configuration is in `./group_vars/all/main.yml` and the remaining configuration is in `./group_vars/all/vault.yml`. There is a sample template provided at `./group_vars/all/vault.example`. Every option must have a value provided or the execution will not be able to complete.

## Amazon Configuration
To fully execute this content the following configuration items need to be completed before execution. If these items are not completed the script will not be able to be executed or will fail during the run.

### IAM Group Policies
In order to execute this Ansible content your user needs to have the following permissions:
* AmazonEC2FullAccess
* AmazonVPCFullAccess
* AmazonRoute53FullAccess
* AmazonRDSFullAccess

### DNS Configuration
Create (in the Amazon Route53 Domain Management tool) a domain that you will use as the target domain for the "cloud" you are creating. (Say for example I used "cloud.rain.org.") You do not have to buy or register this domain with Amazon and the Ansible content makes sure that the target domain exists in Route53.

You will need to then set up your domain to use the nameservers given by Amazon or to point to the domain as the authority for some subdomain of a domain you own. Say that you own "rain.org" and pointed the "cloud" NS records at the records given by Amazon. You could also just buy a domain from Amazon and use that.

### Certificate Creation
Once you have set up DNS you can create a certificate that can be used in the **region you are hosting your application in**. You would need to create the certificate as being from both the hosted zone and "\*." as a prefix to the hosted zone. Say you used "cloud.rain.org" and "\*.cloud.rain.org". Once you have the certificate created you will need to confirm it in the email you get and then set the `vault_certificate_arn` as the ARN from the certificate.

## Planned Features
* Amazon VPC-contained instance
* OCP 3.X installation and configuration
* Keycloak identity management
* Gluster storage array backend

