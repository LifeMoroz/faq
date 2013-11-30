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
virtualenv env
env/bin/pip install -r requirements.txt
# env/bin/python deploy.py


