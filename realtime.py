import redis
import tornado.web

class WaiterHandler(tornado.web.RequestHandler):

    @tornado.web.asynchronous
    def get(self):
        client = redis.StrictRedis(port=6379)
        pubsub = client.pubsub()
        pubsub.subscribe('test_channel')

        for item in pubsub.listen():
            if item['type'] == 'message':
                print item['channel']
                self.write(item['data'])
                self.finish()

        self.write(item['data'])
        self.finish()


class GetHandler(tornado.web.RequestHandler):

    def get(self):
        self.write("Hello world")


application = tornado.web.Application([
    (r"/", GetHandler),
    (r"/wait", WaiterHandler),
])

if __name__ == '__main__':
    application.listen(8888)
    print 'running'
    tornado.ioloop.IOLoop.instance().start()
