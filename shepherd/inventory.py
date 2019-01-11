from __future__ import absolute_import

import exceptions
import os.path

from ansible.parsing.dataloader import DataLoader
## from ansible.inventory.data import InventoryData
from ansible.inventory.manager import InventoryManager
import ansible.errors


# *** CLASSES ***
class InventoryError(exceptions.RuntimeError):
    pass


class InventoryFileMissing(InventoryError):
    pass


class NoHostsError(exceptions.RuntimeError):
    pass


# *** FUNCTIONS ***
def collate(host_pattern, inventory_filename, logger):
    """Create a multi-dimensional array grouping hosts by provider and region."""

    if not os.path.exists(inventory_filename):
        raise InventoryFileMissing("Inventory file missing: " + inventory_filename)
    try:
        ## i = ansible.inventory.Inventory(inventory_filename)
        loader = DataLoader()
        i = InventoryManager(loader, inventory_filename)
    except ansible.errors.AnsibleError, e:
        raise InventoryError(str(e))

    hosts = i.get_hosts(host_pattern)

    if not hosts:
        raise NoHostsError
    
    host_maps = {}
    for host in hosts:
        # Attempt to look up various cloud info in the Ansible host file
        try:
            ## provider=host.get_variables()
            provider = host.vars['cloud_provider']
            instance_id = host.vars['cloud_instance_id']
            region = host.vars['cloud_region']

            if not provider in host_maps:
                host_maps[provider] = {}

            if not region in host_maps[provider]:
                host_maps[provider][region] = {}

            host_maps[provider][region][instance_id] = host
        except KeyError:
            logger.report_warning("host '%s' doesn't have necessary cloud info" % (host.name,))

    return host_maps
