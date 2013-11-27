import redis

r = redis.StrictRedis(host='127.0.0.1')

key = lambda t, i: '{0}:{1}:tags'.format(t, i)

def get_tags(prefix, tagged_id):
	return r.smembers(key(prefix, tagged_id))

def add_tag(prefix, tagged_id, tag):
	r.sadd(key(prefix, tagged_id), tag)

def remove_tag(prefix, tagged_id, tag):
	r.srem(key(prefix, tagged_id), tag)

if __name__ == '__main__':
    add_tag(100, 'foo')
    add_tag(100, 'bar')
