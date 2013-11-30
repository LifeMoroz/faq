#!/bin/bash
echo 'Stopping all related services'
if [ -f /etc/nginx/sites-enabled/faq.conf ]; then
    sudo rm /etc/nginx/sites-enabled/faq.conf
    sudo service nginx reload
else
    echo 'Nginx config file not found'
fi
for f in run/*.pid; do kill `cat "$f"`; done
rm run/*.pid
echo 'Stop finished'

