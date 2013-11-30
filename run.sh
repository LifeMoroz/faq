#!/bin/bash
echo 'Starting all services'
./manage.py make
./manage.py realtime & > logs/realtime-out.log 2> logs/realtime-err.log
uwsgi --ini conf/faq-uwsgi.ini
searchd -c conf/faq-sphinx.conf
./redis-stable/src/redis-server conf/faq-redis.conf
echo 'OK'
