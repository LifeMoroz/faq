#!/bin/bash
echo 'Stopping all related services'
for f in run/*.pid; do kill `cat "$f"`; done
sudo rm /etc/nginx/sites-enabled/faq.conf
sudo service nginx reload
echo 'Ok'

