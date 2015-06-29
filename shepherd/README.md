Shepherd
========

This is a tool for controlling a stable of hosts listed in an
[Ansible][] [inventory file][Ansible_inventory].  (By the use of
non-standard Ansible variables that identify the cloud provider, region
and ID of the host.)  It can also show their status.

Unlike Ansible, the purpose of Shepherd is to manage hosts without
having to log into them.  Actions are perfomed by contacting the API of
one or more cloud providers.

Shepherd is intended to be used like [virsh][] or service(1).  Currently (v0.8),
only [AWS][] is supported.

  [Ansible]: http://www.ansible.com/
  [Ansible_inventory]: http://docs.ansible.com/intro_inventory.html
  [virsh]: http://libvirt.org/virshcmdref.html
  [AWS]:   http://aws.amazon.com

Why not use Ansible's Dynamic Inventory feature?
------------------------------------------------
The [Dynamic Inventory][dyn] plugin allow Ansible to pull down
a list of hosts from a cloud provider and then manage them.

However, it can be handy to keep track hosts with names that are
different from those in the AWS EC2 instance name tag, for example.
Therefore the intent of Shepherd is to make the inventory file the locus
of host management.  It is deliberately not dynamic.

  [dyn]: http://docs.ansible.com/intro_dynamic_inventory.html


Installation
------------

Setup
-----

A [Makefile](Makefile) is provided that uses an internal AWK script to
generate an Ansible inventory file from your .ssh/config file.  This
brings all the regular Ansible variables across from corresponding
SSH settings in the file.

Note that the Makefile currently ignores all hosts in .ssh/config that
aren't preceeded by a comment line that starts with an AWS EC2 instance ID.

YMMV.


Usage
-----
Shepherd takes an action argument on the command line, plus a host
pattern that will match one or more hosts in the  can be used in one of
two ways.

[virsh][] mode:

    shepherd <action> <host-pattern>
    shepherd list

...where <action> is one of:-

  - dominfo
  - start
  - reboot
  - shutdown
  - destroy

service(1) mode:

    shepherd <host-pattern> <action>

...where <action> is one of:-

  - status
  - start
  - restart
  - stop
  - kill

Also, the following AWS action names can be used instead:

  - start
  - reboot
  - shutdown
  - terminate

Options
-------

Examples
--------
