#Prototype for a reduction web service

# Instalation (Ubuntu)

## Requisites:

### Packages, and all required dependencies, to install with synaptic / apt-get
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

### Packages to install with Python PIP:

```bash
sudo pip install Django==1.7.3
sudo pip install django-auth-ldap --upgrade
sudo pip install psycopg2
sudo pip install django-debug-toolbar
```

## Check the Django instalation:

```bash
$ python -c 'import django;print(django.get_version())'
1.7.3
```
## Clone the repository:
```bash
git clone git@github.com:neutrons/reduction_service.git
```

## Setup Postgres

### Edit the following file:
```
sudo vi /etc/postgresql/9.3/main/pg_hba.conf
```

Replace *peer* at the end by *md5*:

```
# "local" is for Unix domain socket connections only
 90 local   all             all                                     peer

```
by
```
# "local" is for Unix domain socket connections only
 90 local   all             all                                     md5

```
Restart postgres:
```
sudo service postgresql restart
```

## Create a user in the the Postgres database:

Database and username/password is available in the ```reduction_service/src/reduction_service/local_settings.py``` that should have been provided sepparatly.

```
# Enter as postgres user
sudo su - postgres

# Once postgres, create a db
createdb reduction_service

# Create user as in local_settings.py
createuser -s -P workflow

# This should work:
psql --username=workflow -W reduction_service

```

## Let's see if the server web works:

If you running locally on your machine, create the folder and change ownership:
```
sudo mkdir /var/www/reduction_service
sudo chown $USER /var/www/reduction_service
make webapp
```

Run this by hand only once!:
```
cd /var/www/reduction_service/app/src
python manage.py createcachetable webcache
```

If the last line of the make file fails, just run it as sudo, e.g.:
```
sudo cp /var/www/reduction_service/apache/apache_django_wsgi.conf  /etc/apache2/sites-available/reduction_service_wsgi.conf
sudo a2ensite reduction_service_wsgi
sudo service apache2 reload
# or:
sudo service apache2 restart
```

Restart apache:
```
sudo service apache2 restart
```

Open the following URL in a browser:
```
http://localhost/reduction_service/
```

# For developers

## Cache

If something goes realy wrong (e.g. moving things around), cache might need to be clean. Type:

```bash
$ python manage.py shell
```

```python
from django.core.cache import cache
cache.clear()
```

# Production (REH7)

## Aditional Software
```
sudo yum group install "Development Tools"
sudo yum install mod_ssl

```

## Postgres

### Start
```bash
# Init db
sudo postgresql-setup initdb

# start service
sudo service postgresql start
```

### Config postgres:

```bash
# Enter as postgres user
sudo su - postgres

# Create user as in local_settings.py
createuser -s -P reduction

# Once postgres, create a db
createdb --owner=reduction reduction_service
```
### Edits:

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

### Restart the service:
```
sudo service postgresql restart
```

### Test
This should work:
```
psql --username=reduction -W reduction_service

\list # list all databases

```

### Restore
```
psql -U reduction -d reduction_service -f /SNS/users/rhf/reduction_service_dump.sql
```

### play with the DB:

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


## Testing locally:

```
cd src/
python manage.py makemigrations
python manage.py migrate --fake-initial

# test! Port 80 to call from a browser
sudo -E python manage.py runserver 80
```


## Apache

### Test
```
sudo service httpd configtest
sudo service httpd status
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

# Production restart

```
# Restart Postgresql
sudo service postgresql restart

# Otherwise play with uwsgi and nginx
cd /var/nginx/reduction_service
sudo service nginx stop
sudo killall -s INT /usr/bin/uwsgi
nohup sudo -E uwsgi --ini nginx/reduction_uwsgi.ini &
# Check the output file!!!!
sudo service nginx start
```
