# Constants:
SRC_DIRECTORY := $(shell pwd)
SRC_src := $(addprefix $(SRC_DIRECTORY), /src)
SRC_templates := $(addprefix $(SRC_DIRECTORY), /templates)
SRC_static := $(addprefix $(SRC_DIRECTORY), /static)
SRC_env := $(addprefix $(SRC_DIRECTORY), /env)

APACHE_WSGI := $(addprefix $(SRC_DIRECTORY), /apache/reduction_service_wsgi.conf)
REQUIREMENTS := $(addprefix $(SRC_DIRECTORY), /requirements/production.txt)

WWW_PREFIX := /var/www/reduction_service

all:
	@echo "Run make install to install the reduction application locally"

venv: env/bin/activate
	@echo "Check if virtualenv is working"
	bash -c "source env/bin/activate; env/bin/python -c 'import os; os.environ[\"VIRTUAL_ENV\"]'"

env/bin/activate: $(REQUIREMENTS)
	@echo "Virtual env instalation"
	test -d env || virtualenv env
	bash -c "source env/bin/activate; env/bin/pip install -r $(REQUIREMENTS)"
	touch env/bin/activate

check: venv

install: webapp

webapp: check
	# Make sure the install directories exist
	test -d $(WWW_PREFIX) || mkdir -m 0755 -p $(WWW_PREFIX)
	test -d $(WWW_PREFIX)/app || mkdir -m 0755 $(WWW_PREFIX)/app
	test -d $(WWW_PREFIX)/static || mkdir -m 0755 $(WWW_PREFIX)/static

	# Install application code
	cp -R $(SRC_src) $(WWW_PREFIX)/app
	cp -R $(SRC_templates) $(WWW_PREFIX)/app
	cp -R $(SRC_static) $(WWW_PREFIX)/app
	cp -R $(SRC_env) $(WWW_PREFIX)

	bash -c " \
		cd $(WWW_PREFIX)/app/src; \
		source $(WWW_PREFIX)/env/bin/activate; \
		$(WWW_PREFIX)/env/bin/python manage.py collectstatic --noinput; \
		$(WWW_PREFIX)/env/bin/python manage.py makemigrations; \
		$(WWW_PREFIX)/env/bin/python manage.py migrate --fake-initial; \
	"
	# Prepare web monitor cache: RUN THIS ONCE BY HAND
	#cd $(WWW_PREFIX)/app/src; python manage.py createcachetable webcache

	# Development environment
	# test -d /etc/apache2/other && cp $(WWW_PREFIX)/apache/dev_django_wsgi.conf /etc/apache2/other/reduction_service_wsgi.conf

	# Linux server environment
	test -d /etc/httpd/conf.d && cp $(APACHE_WSGI) /etc/httpd/conf.d/

	@echo "\n\nReady to go: run apachectl restart\n"

clean:
	rm -rf $(WWW_PREFIX)/*
	#rm -f /etc/apache2/other/reduction_service_wsgi.conf
	rm -f /etc/httpd/conf.d/reduction_service_wsgi.conf

.PHONY: check
.PHONY: clean
.PHONY: install
.PHONY: webapp
