import sys, os, fnmatch
from zope import interface

product_location = os.path.join( os.path.dirname(__file__) )

# product installation is eggless, so we bundle eggs and install them onto 
# sys path at runtime            
included_eggs = [ os.path.join( product_location, 'eggs', egg) for egg \
    in os.listdir( os.path.join( product_location, 'eggs') ) ]
sys.path.extend( included_eggs )    
zope_eggs = [ e for e in included_eggs if 'zope.' in e.rsplit('/')[-1]]

# we have to patch already imported zope module to include any new zope eggs
# magical, alternatives welcome. if the notion bothers you, use the egg install.
if zope_eggs and 'zope' in sys.modules:
    import zope as zope_module
    [zope_module.__path__.insert( 0, e) for e in zope_eggs ]
    del sys.modules['zope'] 
    import zope
    for n in dir( zope_module):
        v = getattr( zope_module, n)
        if isinstance( v, type(zope_module) ):
            setattr( zope, n, v)
    
class IMirrorInstaller( interface.Interface ):
    pass

def installer( *args ):
    return None
    
def initialize( context ): pass
