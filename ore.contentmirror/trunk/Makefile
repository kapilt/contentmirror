
build:
	python2.4 bootstrap.py
	./bin/buildout -c plone-3.3.cfg

coverage:
	./bin/coverage run ./bin/test -s ore.contentmirror --exit-with-status && ./bin/coverage html -d report ore/contentmirror/*py

plone-test:
	./bin/instance test --coverage=coverage -s ore.contentmirror --test-path=.