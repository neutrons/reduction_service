
```bash
ssh -X reduction.sns.gov

# list sudo authotised commands
sudo -l

#DB seetings are here:
/var/www/reduction_service/app/src/reduction_service/local_settings.py

# Backup DB first:
# pg_dump -U {user-name} {source_db} -f {dumpfilename.sql}
pg_dump -U reduction reduction_service -f /SNS/users/rhf/reduction_service_dump.sql

# Restore if needed with:
# psql -U {user-name} -d {desintation_db}-f {dumpfilename.sql}

# Backup the app
tar -zcvf /SNS/users/rhf/reduction_service.tgz /var/www/reduction_service
```

Connect to the db:
```
# psql [DBNAME [USERNAME]]
psql reduction_service reduction
```

Change table names:

```sql
;;; Alter tables:
ALTER TABLE eqsans_boolreductionproperty              RENAME TO reduction_boolreductionproperty             ;
ALTER TABLE eqsans_charreductionproperty              RENAME TO reduction_charreductionproperty             ;
ALTER TABLE eqsans_experiment                         RENAME TO reduction_experiment                        ;
ALTER TABLE eqsans_experiment_instruments             RENAME TO reduction_experiment_instruments            ;
ALTER TABLE eqsans_floatreductionproperty             RENAME TO reduction_floatreductionproperty            ;
ALTER TABLE eqsans_instrument                         RENAME TO reduction_instrument                        ;
ALTER TABLE eqsans_reductionconfiguration             RENAME TO reduction_reductionconfiguration            ;
ALTER TABLE eqsans_reductionconfiguration_experiments RENAME TO reduction_reductionconfiguration_experiments;
ALTER TABLE eqsans_reductionconfiguration_reductions  RENAME TO reduction_reductionconfiguration_reductions ;
ALTER TABLE eqsans_reductionprocess                   RENAME TO reduction_reductionprocess                  ;
ALTER TABLE eqsans_reductionprocess_experiments       RENAME TO reduction_reductionprocess_experiments;
ALTER TABLE eqsans_remotejob                          RENAME TO reduction_remotejob;
ALTER TABLE eqsans_remotejob_plots                    RENAME TO reduction_remotejob_plots;
ALTER TABLE eqsans_remotejob_plots2d                  RENAME TO reduction_remotejob_plots2d;
ALTER TABLE eqsans_remotejobset                       RENAME TO reduction_remotejobset;
ALTER TABLE eqsans_remotejobset_jobs                  RENAME TO reduction_remotejobset_jobs  ;
```

Clone master into home:
```
cd /SNS/users/rhf/git
git clone https://github.com/neutrons/reduction_service/
```

Change the log settings from DEBUG to INFO.
Copy local_settings:
```
cp /var/www/reduction_service/app/src/reduction_service/local_settings.py src/reduction_service/
```


Uncomment the following line from the makefile:
```
test -d /etc/httpd/conf.d && cp $(prefix)/apache/apache_django_wsgi.conf /etc/httpd/conf.d/reduction_service_wsgi.conf
```

Run make & restart apache:
```
cd /SNS/users/rhf/git/reduction_service
make install
# This doesnt work!
# sudo apachectl restart
sudo service httpd restart


```

```
cd /var/www/reduction_service
scl enable python27 bash
virtualenv env --system-site-packages --python=python2.7
source env/bin/activate
pip install -r /SNS/users/rhf/git/reduction_service/requirements.txt
```
