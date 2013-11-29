#!/bin/bash
echo 'Deploying faq'
sudo apt-get update
sudo apt-get install python-pip python-dev mysql-server apache2 libmysqlclient-dev nginx -y
easy_install -U distribute
pip install virtualenv
virtualenv env
env/bin/pip install -r requirements.txt
env/bin/python deploy.py


