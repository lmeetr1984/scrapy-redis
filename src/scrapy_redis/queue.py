from scrapy.utils.reqser import request_to_dict, request_from_dict

from . import picklecompat


"""
这些容器类都会作为scheduler调度request的容器，
scheduler在每个主机上都会实例化一个，并且和spider一一对应，
所以分布式运行时会有一个spider的多个实例和一个scheduler的多个实例存在于不同的主机上，

但是，因为scheduler都是用相同的容器，而这些容器都连接同一个redis服务器，
又都使用spider名加queue来作为key读写数据，所以不同主机上的不同爬虫实例公用一个request调度池，

实现了分布式爬虫之间的统一调度。


"""


class Base(object):
    """Per-spider base queue class"""

    def __init__(self, server, spider, key, serializer=None):
        """Initialize per-spider redis queue.

        Parameters
        ----------
        server : StrictRedis
            Redis client instance.
        spider : Spider
            Scrapy spider instance.
        key: str
            Redis key where to put and get messages.
        serializer : object
            Serializer object with ``loads`` and ``dumps`` methods.

        """
        if serializer is None:
            # Backward compatibility.
            # TODO: deprecate pickle.
            serializer = picklecompat

        # 判断序列化的模块是否有load/dumps

        if not hasattr(serializer, 'loads'):
            raise TypeError("serializer does not implement 'loads' function: %r"
                            % serializer)
        if not hasattr(serializer, 'dumps'):
            raise TypeError("serializer '%s' does not implement 'dumps' function: %r"
                            % serializer)

        self.server = server
        self.spider = spider
        self.key = key % {'spider': spider.name}
        self.serializer = serializer

    def _encode_request(self, request):
        """Encode a request object"""

        # 把request => dict
        obj = request_to_dict(request, self.spider)
        return self.serializer.dumps(obj)

    def _decode_request(self, encoded_request):
        """Decode an request previously encoded"""
        obj = self.serializer.loads(encoded_request)
        return request_from_dict(obj, self.spider)

    def __len__(self):
        """Return the length of the queue"""
        raise NotImplementedError

    def push(self, request):
        """Push a request"""
        raise NotImplementedError

    def pop(self, timeout=0):
        """Pop a request"""
        raise NotImplementedError

    def clear(self):
        """Clear queue/stack"""
        # 清除redis的队列数据
        self.server.delete(self.key)


class FifoQueue(Base):
    """Per-spider FIFO queue"""

    """先进先出队列"""

    def __len__(self):
        """Return the length of the queue"""
        # 返回列表长度
        return self.server.llen(self.key)

    def push(self, request):
        """Push a request"""
        # 往redis list 的左侧添加数据
        self.server.lpush(self.key, self._encode_request(request))

    def pop(self, timeout=0):
        """Pop a request"""
        if timeout > 0:
            # 从一个非空的list右侧 移除第一个数据
            # 如果没有数据的话，那么等待timeout，
            data = self.server.brpop(self.key, timeout)
            if isinstance(data, tuple):
                data = data[1]
        else:
            # 删除最右侧的数据
            data = self.server.rpop(self.key)
        if data:
            # 数据存在的话，那么久还原成request
            return self._decode_request(data)


class PriorityQueue(Base):
    """Per-spider priority queue abstraction using redis' sorted set"""

    def __len__(self):
        """Return the length of the queue"""

        # 获取有序集合元素的数量
        return self.server.zcard(self.key)

    def push(self, request):
        """Push a request"""
        data = self._encode_request(request)
        score = -request.priority
        # We don't use zadd method as the order of arguments change depending on
        # whether the class is Redis or StrictRedis, and the option of using
        # kwargs only accepts strings, not bytes.

        # 使用原生的ZADD，向有序集合中增加数据
        self.server.execute_command('ZADD', self.key, score, data)

    def pop(self, timeout=0):
        """
        Pop a request
        timeout not support in this queue class
        """
        # use atomic range/remove using multi/exec

        # redis默认在执行每次请求都会创建（连接池申请连接）和断开（归还连接池）一次连接操作，
        # 并且开始事务
        pipe = self.server.pipeline()
        pipe.multi()

        # 获取有序集合中的范围内集合数据
        # zremrangebyrank：根据排行范围删除

        # 范围：第一个元素
        pipe.zrange(self.key, 0, 0).zremrangebyrank(self.key, 0, 0)
        results, count = pipe.execute()
        if results:
            return self._decode_request(results[0])


class LifoQueue(Base):
    """Per-spider LIFO queue."""
    """后进先出"""

    def __len__(self):
        """Return the length of the stack"""
        return self.server.llen(self.key)

    def push(self, request):
        """Push a request"""
        # 左侧插入数据
        self.server.lpush(self.key, self._encode_request(request))

    def pop(self, timeout=0):
        """Pop a request"""
        if timeout > 0:
            data = self.server.blpop(self.key, timeout)
            if isinstance(data, tuple):
                data = data[1]
        else:
            # 删除最左侧的第一个元素
            data = self.server.lpop(self.key)

        if data:
            # 如果数据存在的话，那么把数据还原成request
            return self._decode_request(data)


# TODO: Deprecate the use of these names.
SpiderQueue = FifoQueue
SpiderStack = LifoQueue
SpiderPriorityQueue = PriorityQueue
