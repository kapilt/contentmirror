test:
	./bin/test

sphinx:
	cd docs && make html

build-3.3:
	python2.4 bootstrap.py
	./bin/buildout -c plone-3.3.cfg

build-3.2:
	python2.4 bootstrap.py
	./bin/buildout -c plone-3.2.cfg

build-3.1:
	python2.4 bootstrap.py
	./bin/buildout -c plone-3.1.cfg


coverage-html:
	./bin/coverage run ./bin/test -s ore.contentmirror --exit-with-status && ./bin/coverage html -d report ore/contentmirror/*py
	gnome-open report/index.html

coverage:
	./bin/coverage run ./bin/test --exit-with-status && ./bin/coverage report ore/contentmirror/*py


plone-test:
	./bin/instance test --coverage=coverage -s ore.contentmirror --test-path=.

