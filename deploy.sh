#!/bin/bash
echo 'Deploying faq'
# sudo apt-get update
sudo debconf-set-selections <<< 'mysql-server mysql-server/root_password password local'
sudo debconf-set-selections <<< 'mysql-server mysql-server/root_password_again password local'
sudo apt-get install python-pip python-dev mysql-server libmysqlclient-dev nginx -y
easy_install -U distribute

echo 'Downloading and installing redis'
wget http://download.redis.io/redis-stable.tar.gz
tar xvzf redis-stable.tar.gz
cd redis-stable 
make
cd -

sudo pip install virtualenv

if [ ! -d "../../envs" ]; then
  mkdir ../../envs/
fi
virtualenv ../../envs/faq

# установка зависимостей из файла
../../envs/faq/bin/pip install -r requirements.txt

# создание БД
../../envs/faq/bin/python manage.py createdb

# создание таблиц
../../envs/faq/bin/python manage.py syncdb --noinput

echo 'Скачивание дампов redis и MySQL'
wget http://cdn.cygame.ru/faq_dump/dump.rdb.gz
wget http://cdn.cygame.ru/faq_dump/dump.sql.gz
gunzip dump.sql.gz
gunzip dump.rdb.gz

echo 'Загрузка дампа MySQL...'m
mysql -u root -plocal faq_db < dump.sql

echo 'Копирование дампа redis'
cp dump.rdb redis-db/dump.rdb

echo 'user: admin, password: admin'
echo 'db user: root, password: local'
echo 'Запуск через ./run.sh, остановка через ./stop.sh'



