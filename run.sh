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
test ../../envs/faq/bin/python manage.py make >> logs/start.log
test ../../envs/faq/bin/python manage.py collectstatic --noinput

echo 'Need sudo to copy nginx config'
# копируем обновленные настройки нжинкса
test sudo cp conf/faq-nginx.conf /etc/nginx/sites-enabled/faq.conf

# стартуем редиску
test ./redis-stable/src/redis-server conf/faq-redis.conf

# перезагружаем нжинкс
test sudo service nginx reload

# сигналы в питоне не работают нигде, кроме главного треда
# поэтому делаем вот так вот:
test ../../envs/faq/bin/python manage.py realtime &

# бекенд
test ../../envs/faq/bin/uwsgi --ini conf/faq-uwsgi.ini

echo 'OK'
