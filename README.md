# On Demand / One-Touch OCP environment in EC2

## Prerequisites
* Ansible
* Money

## A WARNING!
This costs money to do. It spins up a bunch of instances and it will add up quickly. This is not a cheap thing but it aims to be a fast and correct implementation in EC2 from minimal configuration.

## Ansible Configuration
The bulk of the configuration for the Ansible run is contained in two files. The pulbic/unsecure configuration is in `./group_vars/all/main.yml` and the remaining configuration is in `./group_vars/all/vault.yml`. There is a sample template provided at `./group_vars/all/vault.yml.sample`. Every option must have a value provided or the execution will not be able to complete.

## Prerequisite Amazon Configuration
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



