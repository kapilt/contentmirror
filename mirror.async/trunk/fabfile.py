config.update( dict(
    project = "mirror.async",
    version = open('version.txt').read().strip(),
    repo_url = "https://contentmirror.googlecode.com/svn"
    ))
    
def test( ):
    local("MACOSX_DEPLOYMENT_TARGET=10.3 ./bin/test -s mirror.async")        
    
def report( ):
    local("MACOSX_DEPLOYMENT_TARGET=10.3 ./bin/coverage-test -s mirror.async")    
    local("MACOSX_DEPLOYMENT_TARGET=10.3 ./bin/coverage")
    local('open -a Safari ./coverage/report/all.html')
    
def release( ):
    egg_tag()
    egg_release()
    product_tag()    

def egg_tag( ):
    local('svn cp %(repo_url)s/%(project)s/trunk %(repo_url)s/%(project)s/tags/%(version)s -m "tagging version %(version)s"')
    
def egg_release( ):
    local('python setup.py register')
    local('python setup.py sdist upload')
