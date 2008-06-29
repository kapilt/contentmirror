import sys, os
from zope import interface

product_location = os.path.join( os.path.dirname(__file__) )
                                 
eggs = map(
    lambda x: os.path.join( product_location, 'eggs', x ),                                    
    os.listdir( os.path.join( product_location, 'eggs') )
            )
sys.path.extend( eggs )

class IMirrorInstaller( interface.Interface ):
    pass

def installer( *args ):
    return None
    
def initialize( context ): pass
