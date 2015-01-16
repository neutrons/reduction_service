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
sudo cp /var/www/reduction_service/apache/apache_django_wsgi.conf  /etc/apache2/sites-enabled/reduction_service_wsgi.conf
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

