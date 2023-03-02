# vim: set fileencoding=utf-8 :



import re
import boto3
import botocore.exceptions

from .. import errors
from .. import formatting
from .. import provider
from ..utils import messages


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

ACTION_STATE_MAP = {'status':      EC2_STATE_NONE,
                    'fullstatus':  EC2_STATE_NONE,
                    'start':       EC2_STATE_RUNNING,
                    'restart':     EC2_STATE_RUNNING,
                    'stop':        EC2_STATE_STOPPED,
                    'kill':        EC2_STATE_TERMINATED}

boto_session = None

__all__ = []


# *** CLASSES ***
class PerRegionCohort(provider.Cohort):
    instances = None
    desired_state = EC2_STATE_NONE

    def __init__(self, region, ids, host_map, params):
        """@param host_map is the mapping, for all specified hosts in this
        region, of instance ID to Ansible inventory object."""

        super(PerRegionCohort, self).__init__(region, ids, host_map, params)

        # Validate the public cloud region to avoid a
        # botocore.exceptions.EndpointConnectionError
        if not region in params['aws_regions']:
            raise errors.ProviderError("Unknown cloud region " + region)

        try:
            self.ec2 = boto_session.resource("ec2", region_name=region)
            # Force an API request to validate the credentials
            vpcs = self.ec2.vpcs.all()
            ## list((iter(vpcs)))
                # No VPCs
        except botocore.exceptions.EndpointConnectionError as e:
            raise errors.NetworkError("timeout or connection error")
        except botocore.exceptions.ClientError:
            raise errors.AuthError("Permission denied")
        except botocore.exceptions.NoCredentialsError:
            raise errors.AuthError("No credentials")


    def populate(self):
        if not self.instances:
            self.instances = self.ec2.instances.filter(InstanceIds=self.instance_ids)


    def show_host(self, instance, action):
        host = self.host_map[instance.id]

        state = self.convert_state(instance.state)

        if action == 'status':
            # TO-DO: Return a tuple instead
            # Used to be "%s \t%s\t%s"
            formatting.print_host(host.name, instance.id, state)
        elif action == 'fullstatus':
            # à la knife node show
            # TO-DO: Ansible groups, EC2 tags
            info = { 'az': instance.placement['AvailabilityZone'],
                     'image_id': instance.image_id,
                     'instance_type': instance.instance_type,
                     'launch_time': instance.launch_time,
                     'private_ip': instance.private_ip_address }
            if instance.ipv6_address:
                info['ipv6'] = instance.ipv6_address
            if instance.public_ip_address:
                info['public_ip'] = instance.public_ip_address
                if instance.public_dns_name:
                    info['fqdn'] = instance.public_dns_name
                else:
                    # Reverse-resolve the public IP and use that for the FQDN
                    import socket
                    addr_info = socket.gethostbyaddr(instance.public_ip_address)
                    info['fqdn'] = addr_info[0]

            if instance.vpc_id:
                ## template += """
                ##             VPC: {vpc_id} (<name>), {subnet_id} (<name>)""".format(subnet_id=instance.subnet_id,
                ##                                                                subnet_name="",
                ##                                                                vpc_id=instance.vpc_id,
                ##                                                                vpc_name="")
                info['vpc_info'] = instance.vpc_id
                vpcs = self.ec2.vpcs.filter(VpcIds=[instance.vpc_id])
                i_vpc = next(iter(vpcs))
                if 'Name' in i_vpc.tags:
                    info['vpc_info'] += " (%s)" % i_vpc.tags['Name']
                info['vpc_info'] += ", " + instance.subnet_id
                if 'Name' in instance.subnet.tags:
                    info['vpc_info'] += " (%s)" % i_subnet.tags['Name']

            # Templates have everything starting on column 0, like for the output
            # (Backslashes avoid leading newline.)
            # TO-DO: use Jinja2 or something instead
            if 'fqdn' in info:
                template = """\
FQDN: {fqdn}
"""
            else:
                template = ""

            template += """\
Instance type: {instance_type}
Location:      {az} (availability zone)
IP addrs:      """

            # Addresses
            if 'public_ip' in info:
                template += "{public_ip} "
            template += "{private_ip}"
            if 'ipv6' in info:
                template += " {ipv6}"

            if 'vpc_info' in info:
                template += """
VPC: {vpc_info}"""
            template += """
Launch time:   {launch_time} from AMI: {image_id}"""

            formatting.print_host(host.name, instance.id, state,
                                  template.format(**info))


    def take_action(self, action):
        super(PerRegionCohort, self).take_action(action)

        self.desired_state = ACTION_STATE_MAP[action]
        
        d = self.global_params['dry_run']

        try:
            if action == 'status' or action == 'fullstatus':
                self.populate()
                for instance in self.instances:
                    # List the instance, unless its state doesn't match a
                    # limitation that's in force
                    if (instance.state['Code'] == EC2_STATE_RUNNING or not self.global_params['only_running']) and \
                       (instance.state['Code'] == EC2_STATE_STOPPED or not self.global_params['only_stopped']):
                        # Look up the inventory object from the EC2 object's ID
                        self.show_host(instance, action)

            elif action == 'start':
                self.ec2.instances.filter(InstanceIds=self.instance_ids).start(DryRun=d)
            elif action == 'stop':
                self.ec2.instances.filter(InstanceIds=self.instance_ids).stop(DryRun=d)
            elif action == 'restart':
                self.ec2.instances.filter(InstanceIds=self.instance_ids).reboot(DryRun=d)
            elif action == 'kill':
                if self.global_params['confirm']:
                    self.ec2.instances.filter(InstanceIds=self.instance_ids).terminate(DryRun=d)
                else:
                    messages.report_notice("Not killing instances because -y wasn't specified")
                    raise SystemExit(0)
            else:
                raise errors.ActionError("Unknown action '%s'" % (action,))
        except botocore.exceptions.EndpointConnectionError as e:
            raise errors.NetworkError("timeout or connection error")
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == "DryRunOperation":
                # Equivalent to HTTP code 412, "Precondition Failed"
                self.logger.info(str(e.response['Error']['Message']))
            elif e.response['Error']['Code'] == "UnauthorizedOperation":
                print(dir(e))
                raise errors.AuthError("Permission denied")
            elif e.response['Error']['Code'] == "InvalidInstanceID.NotFound":
                raise errors.InstanceError(str(e.response['Error']['Message'])) from e
            else:
                # InvalidParameterValue, MissingParameter, etc.
                # etc.
                raise


    def num_deviants(self, first_run):
        """Used during polling.  Returns the number of instances in a given
        cohort that don't match the state indicated by the given action."""

        self.populate()

        # Check current state of the instances in the cohort
        undesired_count = 0
        if self.global_params['debug']:
            print('[%d:]' % self.desired_state, end=' ')
        for instance in self.instances:
            if not first_run:
                try:
                    instance.load()
                except ValueError:
                    raise errors.InstanceError("instance no longer exists; instance ID = ",
                                               instance.id)
            if instance.state['Code'] != self.desired_state:
                undesired_count += 1
                if self.global_params['debug']:
                    print('[%d != %d]' % (instance.state['Code'],
                                          self.desired_state),
                                          end=' ')
            else:
                if self.global_params['debug']:
                    print('[%d]' % instance.state['Code'], end=' ')
            # previous_state_code

        if self.global_params['debug']:
            print("%d deviants in AWS region %s" % (undesired_count, self.region))

        return undesired_count


    @classmethod
    def convert_state(cls, state):
        """A string representation of the instance state."""
        if state['Code'] == EC2_STATE_STOPPED:
            return "off"
        else:
            return state['Name']



# *** FUNCTIONS ***
def init(params):
    global boto_session

    if params['aws_profile']:
        boto_session = boto3.session.Session(profile_name=params['aws_profile'])
    else:
        boto_session = boto3.session.Session()

    params['aws_regions'] = boto_session.get_available_regions("ec2")
