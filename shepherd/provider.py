


# *** CLASSES ***
class Cohort(object):
    """Handles operations for a group of hosts, for a specific provider."""
    # TO-DO: think about having the subclass look up the IDs

    def __init__(self, region, ids, host_map, params):
        """@param host_map is the mapping, for all specified hosts in this
        region, of instance ID to Ansible inventory object."""
        self.instance_ids = ids
        self.host_map = host_map
        self.global_params = params
        self.region = region
        self.logger = params['logger']


    def take_action(self, action):
        pass


    def num_deviants(self, first_run):
        """Used during polling.  Returns the number of instances in a given
        cohort that don't match the state indicated by the given action."""
        return 0
