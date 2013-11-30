#!/bin/bash
function test {
    "$@"
    status=$?
    if [ $status -ne 0 ]; then
        echo "error with $1"
        ./stop.sh
    fi
    return $status
}

echo 'Starting all services'
test ./manage.py make >> logs/start.log

echo 'Need sudo to copy nginx config'
test sudo cp conf/faq-nginx.conf /etc/nginx/sites-enabled/faq.conf
test ./redis-stable/src/redis-server conf/faq-redis.conf
test sudo service nginx reload > logs/start.log
test ./manage.py realtime > logs/realtime.log
test uwsgi --ini conf/faq-uwsgi.ini > logs/start.log
test searchd -c conf/faq-sphinx.conf > logs/start.log

echo 'OK'
