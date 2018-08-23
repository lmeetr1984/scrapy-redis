# -*- coding: utf-8 -*-

import redis


# For standalone use.
DUPEFILTER_KEY = 'dupefilter:%(timestamp)s'

PIPELINE_KEY = '%(spider)s:items'

# redis strict 实例
REDIS_CLS = redis.StrictRedis
REDIS_ENCODING = 'utf-8'
# Sane connection defaults.

# 默认的连接配置
REDIS_PARAMS = {
    'socket_timeout': 30,
    'socket_connect_timeout': 30,
    'retry_on_timeout': True,
    'encoding': REDIS_ENCODING,
}

# 默认的调度器的队列
SCHEDULER_QUEUE_KEY = '%(spider)s:requests'
# 调度器class
SCHEDULER_QUEUE_CLASS = 'scrapy_redis.queue.PriorityQueue'

# 调度器的过滤器在redis 中的集合名字
SCHEDULER_DUPEFILTER_KEY = '%(spider)s:dupefilter'
SCHEDULER_DUPEFILTER_CLASS = 'scrapy_redis.dupefilter.RFPDupeFilter'

START_URLS_KEY = '%(name)s:start_urls'

# 使用set作为request队列
START_URLS_AS_SET = False
