
sphinx:
	cd docs && make html

build:
	python2.4 bootstrap.py
	./bin/buildout -c plone-3.3.cfg

coverage-html:
	./bin/coverage run ./bin/test -s ore.contentmirror --exit-with-status && ./bin/coverage html -d report ore/contentmirror/*py
	gnome-open report/index.html

coverage:
	./bin/test --coverage=_coverage -s ore.contentmirror 

plone-test:
	./bin/instance test --coverage=coverage -s ore.contentmirror --test-path=.