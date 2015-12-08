#Prototype for a reduction web service

## Assumptions

- Local : no webserber. Django is run through the command: ```./manage runserver```.
- Development: Same code running on a webserver. Usually this runs on Ubuntu.
- Production: Production code. This Runs on RHEL7 with proper signed SSL certificates.

An enviroment variable named ```DJANGO_SETTINGS_MODULE``` must be defined.
This variable is called by either:
- [manage.py](manage.py)
- [config/wsgi.py](config/wsgi.py)

In the [manage.py](manage.py) the ```DJANGO_SETTINGS_MODULE``` is predefined with settings for local [config.settings.local](config/settings/local.py).

In the [config/wsgi.py](config/wsgi.py) the ```DJANGO_SETTINGS_MODULE```is predefined with settings for production [config.settings.production](config/settings/production.py).

Usually both [local](config/settings/local.py) and [production](config/settings/production.py) don't need to be changed.
There is an [.env](config/settings/.env) file that you should have been provided with the respective environment configurations.

An example for production is:
```
DEBUG=False
SECRET_KEY=<your secret key>
DATABASE_URL=postgres://<user>:<pass>@localhost:5432/<db name>
ADMIN_URL="r'^<admin interface folder>/'"
ALLOWED_HOSTS=localhost,127.0.0.1,<etc...>
```
This file must saved as ```config/settings/.env```.


## Instalation (Local)

### Packages, and all required dependencies, to install with synaptic / apt-get in Ubuntu.
- libhdf5-dev
- libhdf5-serial-dev
- python-h5py
- apache2
- python-ldap
- libldap2-dev
- libsasl2-dev
- postgresql
- postgresql-server-dev
- psycopg2
- libapache2-mod-wsgi
- python-pip
- nginx

### Python packages

See [requirements](config/requirements) directory. This should be installed with pip, if possible, within a virtual environment. See below.

```pip freezes``` gives:

```
Cython==0.23.4
Django==1.8.5
django-auth-ldap==1.2.6
django-debug-toolbar==1.4
django-environ==0.4.0
django-secure==1.0.1
h5py==2.5.0
numpy==1.10.1
psycopg2==2.6.1
python-ldap==2.4.21
simplejson==3.8.0
six==1.10.0
sqlparse==0.1.16
uWSGI==2.0.11.2
wheel==0.24.0
```

### Setup Postgres

Edit the following file:

```bash
# Ubuntu:
sudo vi /etc/postgresql/9.3/main/pg_hba.conf
```
Replace all *peer* or *ident* at the end by *md5*:

E.g.:
```
# "local" is for Unix domain socket connections only
 90 local   all             all                                     peer
```
by
```
# "local" is for Unix domain socket connections only
 90 local   all             all                                     md5
```

Init the database:
```
sudo postgresql-setup initdb
```

Restart postgres:
```
sudo service postgresql restart
```

Configure Postgres:  
```bash
# Enter as postgres user
sudo su - postgres


# Database and username/password is available in the ```.env``` file
# that should have been provided separately.

# Once postgres, create a db
createdb reduction_service

# Create user
createuser -s -P reduction

# Once postgres user, create a db
createdb --owner=reduction reduction_service
```

Test the database. This should work:
```
psql --username=reduction -W reduction_service
# list all databases
\list
```

###  Setup the project

Clone the repository:
```bash
git clone git@github.com:neutrons/reduction_service.git
```

Setup the the virtual environment:
```
virtualenv env
source env/bin/activate
pip install -r config/settings/local.py
```

Let's see if it works:
```
./manage.py makemigrations
./manage.py migrate
./manage.py createcachetable webcache

# test:
./manage.py runserver
# Open http://localhost:8000
```

## Instalation (Local: Ubuntu 14.04)

In adition to the section before we have to install uWSGI and NGINX.


### Disable Apache

Currently running.

Disable from starting on boot:
```
sudo update-rc.d apache2 disable
sudo service apache2 stop
```

### NGINX

Install nginx

Start nginx:
```
sudo service nginx start
```

### uWSGI

uwsgi 2.0 is in the requirements folder.

Test uWSGI:
```
cd ~/git/reduction_service
# Collect static files in the static folder:
python manage.py collectstatic
# Test with the static
./env/bin/uwsgi --http :8001 --module config.wsgi --static-map /static=static
```

## Deployment no SSL

Copy everything for now:
```
cd /var/nginx/reduction_service
sudo cp -r ~/git/reduction_service/* .
```

Enable the configuration:
```
sudo ln -s /var/nginx/reduction_service/nginx/reduction_local_nginx.conf  /etc/nginx/sites-enabled/
```

```
sudo /etc/init.d/nginx restart
```

Start the uwsgi server. It uses a socket to communicate with nginx
```
cd /var/nginx/reduction_service
sudo uwsgi --socket reduction.sock --module config.wsgi --chmod-socket=666
# or
sudo uwsgi --ini nginx/reduction_uwsgi.ini
```

## Deployment SSL

Create key and certificate if needed:
```
cd ssl/
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout reduction.key -out reduction.crt
```

Enable the configuration:
```
sudo rm default
sudo rm /var/nginx/reduction_service/nginx/reduction_local_nginx.conf
sudo ln -s /var/nginx/reduction_service/nginx/reduction_dev_nginx.conf  /etc/nginx/sites-enabled/
sudo /etc/init.d/nginx restart
sudo uwsgi --ini nginx/reduction_uwsgi.ini
```

### Instalation (Production: RHEL7)


Aditional Software
```
sudo yum group install "Development Tools"
sudo yum install mod_ssl

```

### Postgres

Start
```bash
# Init db
sudo postgresql-setup initdb

# start service
sudo service postgresql start
```

Config postgres:

```bash
# Enter as postgres user
sudo su - postgres

# Create user as in local_settings.py
createuser -s -P reduction

# Once postgres, create a db
createdb --owner=reduction reduction_service
```
Edits:

By default Postgresql uses IDENT-based authentication. change to MD5:
```
sudo vi /var/lib/pgsql/data/pg_hba.conf
```
Change:
```
# "local" is for Unix domain socket connections only
local   all             all                                     peer
```
by:
```
# "local" is for Unix domain socket connections only
local   all             all                                     md5
```

Restart the service:
```
sudo service postgresql restart
```

Test
This should work:
```
psql --username=reduction -W reduction_service

\list # list all databases

```

Restore database if a backup was done
```
psql -U reduction -d reduction_service -f /SNS/users/rhf/reduction_service_dump.sql
```

Play with the DB:

```
psql --username=reduction -W reduction_service

\dt #  list all tables in the current database

```

If the migration dit not insert seq in the instriment table. Do it:
```
select * from reduction_instrument;
insert into reduction_instrument(name) values ('seq');
```

## Misc:

Gcc was not available. Installed:

```
sudo yum group install "Development Tools"
```

## Virtual Envs

### Intall:

```
virtualenv env
source env/bin/activate
pip install -r /SNS/users/rhf/git/reduction_service/requirements.txt
```


### Testing locally:

```
cd src/
python manage.py makemigrations
python manage.py migrate --fake-initial

# test! Port 80 to call from a browser
sudo -E python manage.py runserver 80
```

### Disable Apache

```
# Disable Apache
sudo service httpd status
sudo systemctl disable httpd.service
sudo service httpd status
sudo systemctl stop httpd.service
```

### Add new software
```
# install
sudo yum install nginx
sudo pip install uwsgi
```

### Start nginx

```
sudo service nginx status
sudo service nginx start

```
Test: http://reduction.sns.gov/

### Deployment

```
rm -rf /SNS/users/rhf/git/reduction_service/env
cd /SNS/users/rhf/git/reduction_service/
cp env_prod config/settings/.env
virtualenv env
source env/bin/activate
pip install -r requirements/production.txt
```

Copy everything for now:
```
sudo mkdir -p  /var/nginx/reduction_service
cd /var/nginx/reduction_service
sudo cp -r /SNS/users/rhf/git/reduction_service/* .
```
Only in redhat:
```
# If the folders don't exist!
sudo mkdir /etc/nginx/sites-available
sudo mkdir /etc/nginx/sites-enabled
# vi /etc/nginx/nginx.conf
# add inside the http block: include /etc/nginx/sites-enabled/*;
```

Enable the configuration:
```

sudo ln -s /var/nginx/reduction_service/nginx/reduction_prod_nginx.conf  /etc/nginx/sites-enabled/
sudo service nginx restart

nohup sudo -E uwsgi --ini nginx/reduction_uwsgi.ini &
```

### Open ports:
```
sudo iptables -A INPUT -p tcp -m tcp --sport 80 -j ACCEPT
#sudo iptables -A OUTPUT -p tcp -m tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp -m tcp --sport 443 -j ACCEPT
#sudo iptables -A OUTPUT -p tcp -m tcp --dport 443 -j ACCEPT
```

### Copy  certificate and key:

From reduction-old to reduction
```
/etc/ssl/certs/reduction.sns.gov.crt
/etc/pki/tls/private/reduction.sns.gov.key
```
