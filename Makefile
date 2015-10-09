# Constants:
SRC_DIRECTORY := $(shell pwd)
SRC_src := $(addprefix $(SRC_DIRECTORY), /src)
SRC_templates := $(addprefix $(SRC_DIRECTORY), /templates)
SRC_static := $(addprefix $(SRC_DIRECTORY), /static)

APACHE_WSGI := $(addprefix $(SRC_DIRECTORY), /apache/dev_django_wsgi.conf)
WWW_PREFIX := /var/www/reduction_service
REQUIREMENTS := $(addprefix $(SRC_DIRECTORY), /requirements/production.txt)

all:
	@echo "Run make install to install the reduction application locally"

venv: env/bin/activate
	@echo "Venv"

env/bin/activate: $(REQUIREMENTS)
	@echo "Virtual env instalation"
	cd $(WWW_PREFIX)
	test -d env || virtualenv env
	bash -c "source env/bin/activate; env/bin/pip install -r $(REQUIREMENTS)"
	touch env/bin/activate

check: venv
	@echo "Check dependencies"

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

	# Install apache config
	# cp -R $(SRC_apache) $(WWW_PREFIX)

	# Collect the static files and install them
	cd $(WWW_PREFIX)/app/src; python manage.py collectstatic --noinput

	# Create migrations and apply them
	cd $(WWW_PREFIX)/app/src; python manage.py makemigrations
	# To avoid error: ProgrammingError: relation "django_content_type" already exists
	cd $(WWW_PREFIX)/app/src; python manage.py migrate --fake-initial

	# Prepare web monitor cache: RUN THIS ONCE BY HAND
	#cd $(WWW_PREFIX)/app/src; python manage.py createcachetable webcache

	# Development environment
	# test -d /etc/apache2/other && cp $(WWW_PREFIX)/apache/dev_django_wsgi.conf /etc/apache2/other/reduction_service_wsgi.conf
	# Linux server environment
	test -d /etc/httpd/conf.d && cp $(APACHE_WSGI) /etc/httpd/conf.d/

	@echo "\n\nReady to go: run apachectl restart\n"

clean:
	rm -rf $(WWW_PREFIX)
	#rm -f /etc/apache2/other/reduction_service_wsgi.conf
	rm -f /etc/httpd/conf.d/reduction_service_wsgi.conf

.PHONY: check
.PHONY: clean
.PHONY: install
.PHONY: webapp
