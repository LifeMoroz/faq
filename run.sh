#!/bin/bash
function test {
    "$@"
    status=$?
    if [ $status -ne 0 ]; then
        echo "error with $1"
        ./stop.sh
        echo 'Startup failed'
        exit 0
    fi
    return $status
}

echo 'Starting all services'
test ./manage.py make >> logs/start.log

echo 'Need sudo to copy nginx config'
test sudo cp conf/faq-nginx.conf /etc/nginx/sites-enabled/faq.conf
test ./redis-stable/src/redis-server conf/faq-redis.conf
test sudo service nginx reload
test ./manage.py realtime
test uwsgi --ini conf/faq-uwsgi.ini
test searchd -c conf/faq-sphinx.conf

echo 'OK'
