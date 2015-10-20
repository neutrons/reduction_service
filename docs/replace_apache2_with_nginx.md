# RHEL 7


## Disable Apache

```
# install
sudo yum install nginx
sudo yum install uwsgi
#
# Disable Apache
sudo service httpd status
sudo systemctl disable httpd.service
sudo service httpd status
sudo systemctl stop httpd.service
```



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

see a list of all available SELinux booleans. Must be ON!
```
getsebool -a | grep httpd
# Set to on permanentely  if needed:
setsebool httpd_can_network_connect on -P
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


## Deployment

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
```