prefix := /var/www/reduction_service

HAS_MIGRATIONS:=$(shell python -c "import django;t=1 if django.VERSION[1]>=8 else 0; print t")

ifeq ($(OS),Windows_NT)
UNAME_S=Windows
else
UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Linux)
ISLINUX = 1
endif
ifeq ($(UNAME_S),Darwin)
ISOSX = 1
endif
endif

all:
	@echo "Run make install to install the reduction application locally"
	
clean: 
	rm -rf $(prefix)
	rm -f /etc/apache2/other/reduction_service_wsgi.conf
	
check:
	# Check dependencies
	# NEEDS django_auth_ldap
	@python -c "import django" || echo "\nERROR: Django is not installed: www.djangoproject.com\n"
	@python -c "import h5py" || echo "\nERROR: h5py is not installed: www.h5py.org\n"
	
install: webapp
       
webapp: check
	# Make sure the install directories exist
	test -d $(prefix) || mkdir -m 0755 -p $(prefix)
	test -d $(prefix)/app || mkdir -m 0755 $(prefix)/app
	test -d $(prefix)/static || mkdir -m 0755 $(prefix)/static
	
	# Install application code
	cp -R src $(prefix)/app
	cp -R templates $(prefix)/app
	cp -R static $(prefix)/app
	
	# Install apache config
	cp -R apache $(prefix)

	# Collect the static files and install them
	cd $(prefix)/app/src; python manage.py collectstatic --noinput

	# Create the database tables. The database itself must have been created on the server already
ifeq ($(HAS_MIGRATIONS),1)
	@echo "Detected Django >= 1.7: Using migrations"
	# The following call only needs to be done once to create the migrations if the tables already exist
	#cd $(prefix)/app/src; python manage.py makemigrations eqsans plotting catalog remote users
	
	# Create migrations and apply them
	cd $(prefix)/app/src; python manage.py makemigrations
	cd $(prefix)/app/src; python manage.py migrate
else
	cd $(prefix)/app/src; python manage.py syncdb
endif
	# Prepare web monitor cache: RUN THIS ONCE BY HAND
	#cd $(prefix)/app/src; python manage.py createcachetable webcache
	
	@echo "\n\nReady to go: run apachectl restart\n"
	
	# Development environment
	test -d /etc/apache2/other && cp $(prefix)/apache/dev_django_wsgi.conf /etc/apache2/other/reduction_service_wsgi.conf
	# Linux server environment
	#test -d /etc/httpd/conf.d && cp $(prefix)/apache/apache_django_wsgi.conf /etc/httpd/conf.d/reduction_service_wsgi.conf
	
.PHONY: check
.PHONY: clean
.PHONY: install
.PHONY: webapp
