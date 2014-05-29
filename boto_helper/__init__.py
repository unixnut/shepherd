#! /usr/bin/python

import botocore.session
import boto
# this is just used to get the environment variables that aws-cli uses
import awscli


class Credentials(object):
    """Loads credentials and the name of the default region from .aws/config.
    Stuffs the credentials into the boto module's in-memory credentials store.  
    Doesn't need to provide the ability to return credentials.
    
    Use default_region() to get the default region that was specified in .aws/config."""
    def __init__(self):
        # Just make a session 
        boto_session = botocore.session.Session(awscli.EnvironmentVariables)
        creds = boto_session.get_credentials()
        self._default_region = boto_session.get_config()['region']

        # Now create an in-memory copy of the [Credentials] section,
        # as if it came from .boto
        boto.config.add_section('Credentials')
        # ...and populate it with whichever creds were fetched from .aws/config
        boto.config.set('Credentials', 'aws_access_key_id', creds.access_key)
        boto.config.set('Credentials', 'aws_secret_access_key', creds.secret_key)
        # TO-DO: 
        ## boto.config.set('Credentials', 'security_token', creds.token)


    def default_region(self):
        return self._default_region



if __name__ == "__main__":
    print "hi from " + __file__
    c = Credentials()
    print c.default_region()

