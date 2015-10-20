# Ubuntu 14.04

## Disable Apache

Currently running.

Disable from starting on boot:
```
sudo update-rc.d apache2 disable
sudo service apache2 stop
```

## NGINX

Install nginx

Start nginx:
```
sudo service nginx start
```

## uWSGI

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

# RHEL 7


## Disable Apache

```
# Disable Apache
sudo service httpd status
sudo systemctl disable httpd.service
sudo service httpd status
sudo systemctl stop httpd.service
```

## Add new software
```
# install
sudo yum install nginx
sudo pip install uwsgi
```

## Start nginx

```
sudo service nginx status
sudo service nginx start

```
Test: http://reduction.sns.gov/

## Deployment

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
