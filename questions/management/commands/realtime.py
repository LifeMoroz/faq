from tornado import web, ioloop
from sockjs.tornado import SockJSRouter, SockJSConnection
import json
import os
import tornadoredis
import logging

from django.core.management.base import BaseCommand

# parts of code from tutorial
# http://blog.kristian.io/post/47460001334/sockjs-and-tornado-for-python-real-time-web-projects/
# by Kristian Ollegaard

QUESTION_CHAN_PREF = 'question'
USER_CHAN_PREF = 'user'
REALTIME_PREF = 'realtime'
UPDATES_TAG = 'updates'


class Connection(SockJSConnection):
    clients = set()

    def send_message(self, message, data_type):
        """
        Standard format for all messages
        """
        return self.send(json.dumps({
            'data_type': data_type,
            'data': message,
        }))

    def send_error(self, message, error_type=None):
        """
        Standard format for all errors
        """
        return self.send(json.dumps({
            'data_type': 'error' if not error_type else '%s_error' % error_type,
            'data': {
                'message': message
            }
        }))

    def on_open(self, request):
        """
        Request the client to authenticate and add them to client pool.
        """
        self.channels = set()
        self.clients.add(self)

    def on_close(self):
        """
        Remove client from pool. Unlike Socket.IO connections are not
        re-used on e.g. browser refresh.
        """
        self.clients.remove(self)
        return super(Connection, self).on_close()

    def on_message(self, msg):
        """
        Handle subcription requests
        """
        try:
            print msg
            message = json.loads(msg)
        except ValueError:
            self.send_error("Invalid JSON")
            return
        if message['data_type'] == 'sub':
            channel = message['data']['channel']
            self.channels.add(channel)
            self.send_message({'message': 'success'}, 'sub')
            logging.debug("Client updated channels with %s" % channel)
        else:
            self.send_error("Invalid data type %s" % message['data_type'])
            logging.debug("Invalid data type %s" % message['data_type'])

    @classmethod
    def pubsub_message(cls, msg):
        for client in cls.clients:
            if msg.channel in client.channels:
                client.send(msg.body)

if __name__ == '__main__':
    pool = tornadoredis.ConnectionPool()
    c = tornadoredis.Client()
    c.connect()
    c.psubscribe("*:*:{0}".format(UPDATES_TAG), lambda msg: c.listen(Connection.pubsub_message))

    Router = SockJSRouter(Connection, '/%s' % REALTIME_PREF)

    app = web.Application(Router.urls)
    app.listen(os.environ.get("PORT", 6500))
    ioloop.IOLoop.instance().start()
    
class Command(BaseCommand):
    help = 'Generates testing data'

    args = '[n]'

    def handle(self, *args, **kwargs):
        pool = tornadoredis.ConnectionPool()
        c = tornadoredis.Client()
        c.connect()
        c.psubscribe("*:*:{0}".format(UPDATES_TAG), lambda msg: c.listen(Connection.pubsub_message))
    
        Router = SockJSRouter(Connection, '/%s' % REALTIME_PREF)
    
        app = web.Application(Router.urls)
        app.listen(os.environ.get("PORT", 6500))
        ioloop.IOLoop.instance().start()
