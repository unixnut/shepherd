Cloud-support
=============

Various command line tools and libraries to make using AWS and other providers
more convenient.

[Shepherd](shepherd)
----------
This is a tool for controlling a stable of hosts listed in an
[Ansible][] [inventory file][Ansible_inventory].  (By the use of
non-standard Ansible variables that identify the cloud provider, region
and ID of the host.)  It can also show their status.

    [Ansible]: http://www.ansible.com/
    [Ansible_inventory]: http://docs.ansible.com/intro_inventory.html

boto_helper
-----------
Allows your programs that use [boto] to enjoy the magic and flexibility
of the `.aws/config` file used by [aws-cli] instead of the putrid mess
that is the `.boto` file used by the boto library by default.

The documentation can be described as a code snippet.  Just do this:

```python
import boto.ec2
import boto_helper

c = boto_helper.Credentials()

ec2 = boto.ec2.connect_to_region(c.default_region())
```
    
There is no need for `boto_helper.Credentials` to return credentials,
because the constructor feeds them to the `boto` library's config
submodule where they are available to all API calls.

Note that this module is mainly used during testing, because in production
you'll either use `AssumeRole` and get the credentials from the AWS EC2
metadata server, or you'll use a .boto file with just the credentials
you need.

  [aws-cli]: http://aws.amazon.com/cli/ "AWS Command Line Interface"
  [boto]: https://github.com/boto/boto "Python interface to Amazon Web Services"

