# coding=utf-8
from tornado import web, ioloop

from sockjs.tornado import SockJSRouter, SockJSConnection
import json
import os
import threading
import tornadoredis
import signal
import logging
import time

from django.core.management.base import BaseCommand
from django.conf import settings

# parts of code from tutorial
# http://blog.kristian.io/post/47460001334/sockjs-and-tornado-for-python-real-time-web-projects/
# by Kristian Ollegaard

QUESTION_CHAN_PREF = 'question'
USER_CHAN_PREF = 'user'
REALTIME_PREF = 'realtime'
UPDATES_TAG = 'updates'


class Connection(SockJSConnection):
    clients = set()
    channels = set()

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
            message = json.loads(msg)
        except ValueError:
            self.send_error("Invalid JSON")
            return
        if message['data_type'] == 'sub':
            channel = message['data']['channel']
            self.channels.add(channel)
            self.send_message({'message': 'success'}, 'sub')
        else:
            self.send_error("Invalid data type %s" % message['data_type'])

    @classmethod
    def pubsub_message(cls, msg):
        for client in cls.clients:
            if msg.channel in client.channels:
                client.send(msg.body)

class Command(BaseCommand):
    help = 'Generates testing data'
    pidfile = os.path.join(settings.BASE_DIR, 'run', 'realtime.pid')

    def sig_handler(self, sig, frame):
        """Catch signal and init callback"""
        ioloop.IOLoop.instance().add_callback(self.shutdown)

    def shutdown(self):
        """Stop server and add callback to stop i/o loop"""

        io_loop = ioloop.IOLoop.instance()
        io_loop.add_timeout(time.time() + 2, io_loop.stop)

        if os.path.isfile(self.pidfile):
            os.unlink(self.pidfile)

        exit(0)

    def _handle(self):

        logger = logging.getLogger()
        logger.handlers = []
        # удаляем внезапный треш из консоли
        logger.addHandler(logging.FileHandler(os.path.join(settings.BASE_DIR, 'logs', 'realtime.log')))

        c = tornadoredis.Client(port=settings.REDIS_PORT)
        c.connect()
        c.psubscribe("*:*:{0}".format(UPDATES_TAG), lambda msg: c.listen(Connection.pubsub_message))

        router = SockJSRouter(Connection, '/%s' % REALTIME_PREF)

        app = web.Application(router.urls, debug=False)
        app.listen(os.environ.get("PORT", settings.TORNADO_PORT))

        # получаем pid
        pid = str(os.getpid())


        # записываем свой pid в файл
        file(self.pidfile, 'w').write('%s\n' % pid)

        signal.signal(signal.SIGTERM, self.sig_handler)
        signal.signal(signal.SIGINT, self.sig_handler)
        ioloop.IOLoop.instance().start()

    def handle(self, *args, **options):
        if os.path.isfile(self.pidfile):
            self.stderr.write('%s already exists' % self.pidfile)
            exit(-1)

        # запускаем демона
        thread = threading.Thread(target=self._handle)
        thread.daemon = True
        thread.start()
