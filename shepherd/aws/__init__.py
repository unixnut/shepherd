# vim: set fileencoding=utf-8 :
from __future__ import absolute_import

import sys
import re
import boto
import boto.ec2
import boto.vpc

from .. import errors
from .. import formatting
from .. import provider


# -- API request/response stuff --
http_messages = { 400: "Problem with info",
                  401: "Authorisation failed",
                  403: "Permission denied",
                  412: "Dry-run mode" }

EC2_STATE_PENDING       = 0
EC2_STATE_RUNNING       = 16
EC2_STATE_SHUTTING_DOWN = 32
EC2_STATE_TERMINATED    = 48
EC2_STATE_STOPPING      = 64
EC2_STATE_STOPPED       = 80
EC2_STATE_NONE          = -1

action_state_map = {'status':      EC2_STATE_NONE,
                    'fullstatus':  EC2_STATE_NONE,
                    'start':       EC2_STATE_RUNNING,
                    'restart':     EC2_STATE_RUNNING,
                    'stop':        EC2_STATE_STOPPED,
                    'kill':        EC2_STATE_TERMINATED}

__all__ = []


# *** CLASSES ***
class PerRegionCohort(provider.Cohort):
    instances = None
    desired_state = EC2_STATE_NONE

    def __init__(self, region, ids, host_map, params):
        """@param host_map is the mapping, for all specified hosts in this
        region, of instance ID to Ansible inventory object."""

        super(PerRegionCohort,self).__init__(region, ids, host_map, params)

        try:
            # When letting the boto library read the credentials, tell it which profile to use, if any.
            # TO-DO: test with .aws/credentials and .boto
            if params['use_boto']:
                profile = params.get("profile")
            else:
                profile = None
            self.ec2 = boto.vpc.connect_to_region(region, profile_name=profile)
        except boto.exception.NoAuthHandlerFound, e:
            raise errors.AuthError("No credentials")

        if not self.ec2:
            raise errors.ProviderError("Unknown cloud region " + region)


    def take_action(self, action):
        super(PerRegionCohort,self).take_action(action)

        logger = self.global_params['logger']
        self.desired_state = action_state_map[action]

        try:
            if action == 'status' or action == 'fullstatus':
                self.instances = self.ec2.get_only_instances(instance_ids=self.instance_ids)
                for instance in self.instances:
                    # List the instance, unless its state doesn't match a
                    # limitation that's in force
                    if (instance.state_code == EC2_STATE_RUNNING or not self.global_params['only_running']) and \
                       (instance.state_code == EC2_STATE_STOPPED or not self.global_params['only_stopped']):
                        # Look up the inventory object from the EC2 object's ID
                        host = self.host_map[instance.id]

                        if action == 'status':
                            # TO-DO: Return a tuple instead
                            # Used to be "%s \t%s\t%s"
                            formatting.print_host(host.name, instance.id, instance.state)
                        elif action == 'fullstatus':
                            # à la knife node show
                            # TO-DO: Ansible groups, EC2 tags
                            info = { 'az': instance.placement,
                                     'image_id': instance.image_id,
                                     'instance_type': instance.instance_type,
                                     'launch_time': instance.launch_time,
                                     'private_ip': instance.private_ip_address,
                                     'public_ip': instance.ip_address }
                            if instance.public_dns_name:
                                info['fqdn'] = instance.public_dns_name
                            elif instance.ip_address:
                                import socket
                                addr_info = socket.gethostbyaddr(instance.ip_address)
                                info['fqdn'] = addr_info[0]

                            if instance.vpc_id:
                                ## template += """
                                ##             VPC: {vpc_id} (<name>), {subnet_id} (<name>)""".format(subnet_id=instance.subnet_id,
                                ##                                                                subnet_name="",
                                ##                                                                vpc_id=instance.vpc_id,
                                ##                                                                vpc_name="")
                                info['vpc_info'] = instance.vpc_id
                                vpcs = self.ec2.get_all_vpcs(vpc_ids=[instance.vpc_id])
                                i_vpc = vpcs[0]
                                if 'Name' in i_vpc.tags:
                                    info['vpc_info'] += " (%s)" % i_vpc.tags['Name']
                                info['vpc_info'] += ", " + instance.subnet_id
                                subnets = self.ec2.get_all_subnets(subnet_ids=[instance.subnet_id])
                                i_subnet = subnets[0]
                                if 'Name' in i_subnet.tags:
                                    info['vpc_info'] += " (%s)" % i_subnet.tags['Name']

                            # TO-DO: use Jinja2 or something instead
                            if 'fqdn' in info:
                                template = "FQDN: {fqdn}\n"
                            else:
                                template = ""
                            template += """\
Instance type: {instance_type}
Location:      {az} (availability zone)
IP addrs:      {public_ip} {private_ip}"""
                            if 'vpc_info' in info:
                                template += """
VPC: {vpc_info}"""
                            template += """
Launch time:   {launch_time} from AMI: {image_id}"""

                            formatting.print_host(host.name, instance.id, instance.state,
                                                  template.format(**info))

            elif action == 'start':
                self.ec2.start_instances(instance_ids=self.instance_ids, dry_run=self.global_params['dry_run'])
            elif action == 'stop':
                self.ec2.stop_instances(instance_ids=self.instance_ids, dry_run=self.global_params['dry_run'])
            elif action == 'restart':
                self.ec2.reboot_instances(instance_ids=self.instance_ids, dry_run=self.global_params['dry_run'])
            elif action == 'kill':
                if self.global_params['confirm']:
                    self.ec2.terminate_instances(instance_ids=self.instance_ids, dry_run=self.global_params['dry_run'])
                else:
                    logger.report_notice("Not killing instances because -y wasn't specified")
                    sys.exit(0)
            else:
                raise errors.ActionError("Unknown action '%s'" % (action,))
        except boto.exception.EC2ResponseError, e:
            # An error occurred when making the API request.

            # Unlike other exceptions, don't use str(e), because this
            # outputs everything including the response body
            http_code = e.args[0]
            category_str = http_messages.get(http_code, "Unknown error (code %d)" % (http_code,))

            if http_code == 412:    # Precondition Failed: means dry run
                logger.report_notice(category_str,
                             "-- further info:\n ",
                             e.message)
                sys.exit(0)
            elif http_code == 401:  # Unauthorized
                raise errors.AuthError(category_str + " -- further info:\n  " + e.message)
            elif http_code in (400, 403):   # Bad Request, Forbidden
                # Find IDs of missing instance(s) in the response body, e.g.
                #     The instance IDs 'i-1414202a, i-3d4e0607' do not exist
                # or  The instance ID 'i-234aa3a9' does not exist
                # (Do all matching first because otherwise stacked if-else doesn't work.)
                match_single = re.search(r"instance ID '(i-[0-9a-f]*)'", e.args[2])
                match_multiple = re.search(r"instance IDs '(i-[0-9a-f]*[^']*)'", e.args[2])
                if match_single:
                    host = self.host_map[match_single.group(1)]
                    logger.report_error(category_str,
                                 "for host '%s':\n " % (host.name,),
                                 e.message)
                elif match_multiple:
                    id_list_string = match_multiple.group(1)
                    id_list = id_list_string.split(", ")
                    assert len(id_list) >= 2

                    # actual error message, then list each host on a separate line
                    logger.report_error(category_str,
                                 "for hosts; instance IDs do not exist:")
                    for id in id_list:
                        host = self.host_map[id]
                        print >> sys.stderr, "\t%s (%s)" % (host.name, id)
                else:
                    # Something went wrong when trying to see which instance ID was bad
                    logger.report_error(category_str,
                                 "-- bad instance ID; further info:\n ",
                                 e.message)

                # This won't cause an additional message
                raise errors.MissingInstanceError("Instance ID problem")
            else:
                raise errors.InstanceError("Unknown instance problem", http_code)


    def num_deviants(self, first_run):
        """Used during polling.  Returns the number of instances in a given
        cohort that don't match the state indicated by the given action."""
        logger = self.global_params['logger']

        if not self.instances:
            self.instances = self.ec2.get_only_instances(instance_ids=self.instance_ids)

        undesired_count = 0
        if self.global_params['debug']:
            print '[%d:]' % self.desired_state,
        for instance in self.instances:
            if not first_run:
                try:
                    instance.update(validate=True)
                except ValueError:
                    raise errors.InstanceError("instance no longer exists; instance ID = ", instance.id)
            if instance.state_code != self.desired_state:
                undesired_count += 1
                if self.global_params['debug']:
                    print '[%d != %d]' % (instance.state_code, self.desired_state),
            else:
                if self.global_params['debug']:
                    print '[%d]' % instance.state_code,
            # previous_state_code

        if self.global_params['debug']:
            print "%d deviants in AWS region %s" % (undesired_count, self.region)

        return undesired_count



# *** FUNCTIONS ***
def init(params):
    if not params['use_boto']:
        ## print "params['use_boto'] is False!"
        # Use aws-cli config file for credentials
        import boto_helper
        c = boto_helper.Credentials(params.get("profile"))
