#!/bin/bash
echo 'Deploying faq'
sudo apt-get update
sudo apt-get install python-pip python-dev redis-server mysql-server apache2 memcached libmysqlclient-dev nginx -y
easy_install -U distribute
pip install virtualenv
virtualenv env
env/bin/python pip install -r requirements.txt


