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
../../envs/bin/pip install -r requirements.txt



