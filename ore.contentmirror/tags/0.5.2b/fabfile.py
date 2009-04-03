

config.update( dict(
    project = "ore.contentmirror",
    version = open('version.txt').read().strip(),
    repo_url = "https://contentmirror.googlecode.com/svn"
    ))

def release( ):
    egg_tag()
    egg_release()
    product_tag()
    product_build( config.version )
    product_release()

def egg_tag( ):
    local('svn cp %(repo_url)s/%(project)s/trunk %(repo_url)s/%(project)s/tags/%(version)s -m "tagging version %(version)s"')
    
def egg_release( ):
    local('python setup.py register')
    local('python setup.py sdist upload')

def product_build( version='trunk' ):
    import fnmatch, os, shutil  
    
    # remove previous build
    version = version.strip()   
        
    if os.path.exists('build/ContentMirror'):
        shutil.rmtree('build/ContentMirror')
        
    if version == 'trunk':
        local('svn export %(repo_url)s/Products.ContentMirror/trunk/Products/ContentMirror build/ContentMirror')  
    else:
        local('svn export %(repo_url)s/Products.ContentMirror/tags/%(version)s/Products/ContentMirror build/ContentMirror')
    
    # copy sqlalchemy egg
    sa_eggs = fnmatch.filter( os.listdir('eggs'), 'SQLAlchemy*' )
    sa_eggs.sort()
    shutil.copytree( 'eggs/%s'%(sa_eggs[-1]), 'build/ContentMirror/eggs/%s'%(sa_eggs[-1]))
    
    # copy zope.sqlalchemy egg
    zsa_eggs = fnmatch.filter( os.listdir('eggs'), 'zope.sqlalchemy*' )
    zsa_eggs.sort()
    shutil.copytree( 'eggs/%s'%(zsa_eggs[-1]), 'build/ContentMirror/eggs/%s'%(zsa_eggs[-1]))
        
    # unpack bdist egg 
    config.cm_egg = 'ore.contentmirror-%(version)s-py2.4.egg'
    
    if os.path.exists('build/%(cm_egg)s'%config):
        shutil.rmtree('build/%(cm_egg)s'%config)

    config.working_dir = os.path.abspath('.')
    os.mkdir('build/%(cm_egg)s'%(config))

    local('MACOSX_DEPLOYMENT_TARGET="10.3" python2.4 setup.py bdist_egg')
    local('cd build/%(cm_egg)s && unzip %(working_dir)s/dist/%(cm_egg)s')
    local('cp -Rf build/%(cm_egg)s build/ContentMirror/eggs')
    #shutil.copyfile('version.txt', 'build/ContentMirror/version.txt')
    
    local('cd build && tar czvf ContentMirror-%(version)s.tar.gz ContentMirror')

def product_tag( ):
    config.project = "Products.ContentMirror"
    local('svn cp %(repo_url)s/ore.contentmirror/trunk/version.txt %(repo_url)s/%(project)s/trunk/ -m "updating version to %(version)s"')            
    local('svn cp %(repo_url)s/%(project)s/trunk %(repo_url)s/%(project)s/tags/%(version)s -m "tagging version %(version)s"')
    
def product_release( ):
    local('googlecode_upload.py -S "Product Release %(version)s" -p contentmirror build/ContentMirror-%(version).tar.gz')
    
