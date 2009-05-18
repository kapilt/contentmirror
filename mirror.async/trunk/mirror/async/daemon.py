import logging, optparse

log = logging.getLogger('mirror.async')

class ZopeEnvironment( object ):
    
    def setup(self):
        "create the server"
        # read the zope configuration
        zopeconfig = os.path.realpath(self.config.get('default', 'zopeconfig'))
        log.info('Parsing zope configuration from "%s"', zopeconfig)
        from Zope2.Startup.run import configure
        
        # important: it tries to access options. Do not allow this.
        sys.argv = [] 
        configure(zopeconfig)
        log.info('Starting up zope application')
        import Zope2
        app = Zope2.app()
        return self.make_request_context( app )
            
    def make_request_context(self, app):
        from AccessControl.SecurityManagement import newSecurityManager
        from AccessControl.SecurityManager import setSecurityPolicy
        from Testing.makerequest import makerequest
        from Products.CMFCore.tests.base.security import (
            PermissiveSecurityPolicy, 
            # AnonymousUser, 
            OmnipotentUser,
            )

        _policy = PermissiveSecurityPolicy()
        _oldpolicy = setSecurityPolicy(_policy)
        newSecurityManager(None, OmnipotentUser().__of__(self.app))
        return makerequest(self.app)


class Daemon( object ):
    pass


usage = """\
Content Mirror Async Processor
"""
def main( ):
    import optparse
    parser = optparse.OptionParser( usage=usage )
    # command line usage
    parser.add_option()
    
    options, args = parser.parse_args()
    processor = AsyncProcessor( app, options.site_path )
    processor()

    