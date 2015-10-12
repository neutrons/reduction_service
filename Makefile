##
# Make file to deploy the project in production
#
# This shouldn't work in windows

.PHONY: check
.PHONY: clean
.PHONY: install
.PHONY: webapp
.PHONY: venv

SHELL = /bin/bash
UNAME = $(shell uname)

## Release file to determin distro and os
UBUNTU_REL_F := /etc/lsb-release
DEBIAN_REL_F := /etc/debian_version
ORACLE_REL_F := /etc/oracle-release
REDHAT_REL_F := /etc/redhat-release

# Constants:
SRC_DIRECTORY := $(shell pwd)
SRC_src := $(addprefix $(SRC_DIRECTORY), /src)
SRC_templates := $(addprefix $(SRC_DIRECTORY), /templates)
SRC_static := $(addprefix $(SRC_DIRECTORY), /static)
SRC_env := $(addprefix $(SRC_DIRECTORY), /env)

APACHE_WSGI := $(addprefix $(SRC_DIRECTORY), /apache/reduction_service_wsgi.conf)
REQUIREMENTS := $(addprefix $(SRC_DIRECTORY), /requirements/production.txt)

WWW_PREFIX := /var/www/reduction_service

## Determine OS and Distribution
ifeq ($(UNAME),Darwin)
	DISTRO := osx
	CODENAME = $(shell sw_vers -productVersion  | sed "s/\./_/g")
## Check oracle first as it also has the redhat-release file
else ifneq ("$(wildcard $(ORACLE_REL_F))", "")
	DISTRO := oracle
else ifneq ("$(wildcard $(REDHAT_REL_F))", "")
	DISTRO := redhat
## Check ubuntu first as it also has the debian_version file
else ifneq ("$(wildcard $(UBUNTU_REL_F))","")
	DISTRO := ubuntu
	CODENAME = $(shell grep 'DISTRIB_CODENAME=' $(UBUNTU_REL_F) | cut -d '=' -f 2 | tr '[:upper:]' '[:lower:]')
else ifneq ("$(wildcard $(DEBIAN_REL_F))", "")
	DISTRO := debian
	CODENAME = $(shell cat $(DEBIAN_REL_F))
endif

ifeq ("$(DISTRO)","")
	echo "Could not determine distro!"
	exit 1
endif

## Check wich apache root to use:
ifeq ($(shell [[ $(DISTRO) == "ubuntu" || $(DISTRO) == "debian" ]] && echo true),true)
	APACHE_PREFIX := /etc/apache2
else
	APACHE_PREFIX := /etc/httpd
endif


all:
	@echo "Run make install to install the reduction application locally"
	@echo "Configuration:"
	@echo "Apache: $(APACHE_PREFIX)"
	@echo "From:   $(SRC_DIRECTORY)"
	@echo "To:     $(WWW_PREFIX)"

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

	# Linux server environment
	# This probbaly has to run as root
	test -d $(APACHE_PREFIX)/conf.d && cp $(APACHE_WSGI) $(APACHE_PREFIX)/conf.d/

	@echo "\n\nReady to go:\n"
	@echo "sudo service httpd restart\n"
	@echo "Or:\n"
	@echo "sudo service apachectl restart\n"

clean:
	rm -rf $(WWW_PREFIX)/*
	rm -f $(APACHE_PREFIX)/conf.d/reduction_service_wsgi.conf


