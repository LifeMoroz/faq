#!/bin/bash
echo 'Starting all services'
./manage.py make

echo 'Need sudo to copy nginx config'
sudo cp conf/faq-nginx.conf /etc/nginx/sites-enabled/faq.conf
sudo service nginx reload
echo 'Ok'

./manage.py realtime & > logs/realtime-out.log 2> logs/realtime-err.log
uwsgi --ini conf/faq-uwsgi.ini
searchd -c conf/faq-sphinx.conf
./redis-stable/src/redis-server conf/faq-redis.conf
echo 'OK'
