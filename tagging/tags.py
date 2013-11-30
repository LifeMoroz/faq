# coding=utf-8
from redis_cache import get_redis_connection

# Для справки, комманды редиса
# http://redis.io/commands

# лямбда-функция, которая возвращает ключ
# где хранятся теги для чего-то
# t - question, например
# i - идентификатор вопроса
key = lambda t, i: '{0}:{1}:tags'.format(t, i)

# лямбда функция, которая возращает ключ для
# множества, где хранятся id-шники вопросов
# у которых есть тег name
tag_key = lambda t, name: 'tag:{0}:{1}'.format(name, t)

# все теги, их не так много, храним в одном сортированном
# множестве, где счет у каждого элемента - сколько он раз
# заюзан в вопросах
key_all_tags = 'tags:all'


def get_tags(prefix, tagged_id):
    r = get_redis_connection()
    # smembers возвращает все элементы множества
    # по ключу
    return r.smembers(key(prefix, tagged_id))


def get_top(max_tags=10, offset=0):
    r = get_redis_connection()
    # zrevrage возвращает из упорядоченного множества
    # первые max_tags тегов начиная с offset
    # значения отсортированы (в данном случае по кол-ву вопросов
    # в которых они использованы)
    return r.zrevrange(key_all_tags, offset, max_tags)


def get_models(prefix, tag):
    """
    Возвращает id-шники элементов с тегом tag
    Например все вопросы, у которых есть какой-то тег
    """
    r = get_redis_connection()
    return r.smembers(tag_key(prefix, tag))


def add_tag(prefix, tagged_id, tag):
    if tag.strip() == '':
        return

    r = get_redis_connection()
    # ZINCRBY увеличивает "счет" тега, в данном случае на 1
    r.execute_command('ZINCRBY', key_all_tags, 1, tag)

    # добавляем тег к вопросу и id-шник вопроса к тегу
    r.sadd(key(prefix, tagged_id), tag)
    r.sadd(tag_key(prefix, tag), tagged_id)


def add_tags(prefix, tagged_id, tags):
    # тут просто добавляем сразу много тегов
    r = get_redis_connection()
    for t in tags:
        if t.strip() == '':
            continue
        r.execute_command('ZINCRBY', key_all_tags, 1, t)
        r.sadd(key(prefix, tagged_id), t)
        r.sadd(tag_key(prefix, t), tagged_id)


def get_tag_count(tag):
    r = get_redis_connection()
    # zscore возвращает счет тега
    return r.zscore(key_all_tags, tag)


def remove_tag(prefix, tagged_id, tag):
    r = get_redis_connection()
    r.execute_command('ZINCRBY', key_all_tags, -1, tag)
    r.srem(key(prefix, tagged_id), tag)
    r.srem(tag_key(prefix, tag), tagged_id)


def get_all_tags():
    r = get_redis_connection()
    return r.zrevrange(key_all_tags, 0, -1)


def get_starts(startswith):
    # а тут для автокомплита
    r = get_redis_connection()
    # zscan ищет по wildcard-у элемент

    data = r.execute_command('ZSCAN', key_all_tags, 0, 'match', '{0}*'.format(startswith))
    result = []
    tags = data[1]
    if len(tags) == 0:
        return None
    count = len(tags)
    for i in range(0, count, 2):
        result.append(tags[i])
    return result


