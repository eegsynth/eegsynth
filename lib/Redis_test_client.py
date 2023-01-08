import threading
import time

broker='zeromq'

if broker=='redis':
    import redis
    r = redis.StrictRedis(host='localhost', db=0, charset='utf-8', decode_responses=True)
    r.client_list()
elif broker=='dummy':
    import DummyRedis
    r = DummyRedis.client()
elif broker=='fake':
    import FakeRedis
    r = FakeRedis.client()
elif broker=='zeromq':
    import ZmqRedis
    r = ZmqRedis.client()

r.set('a', 1)
r.set('b', 2)
# r.set('c', 3)

print(r.get('a'))  # 1
print(r.get('b'))  # 2
print(r.get('c'))  # None

print(r.exists('a'))  # True
print(r.exists('b'))  # True
print(r.exists('c'))  # False

class WriteThread(threading.Thread):
    def __init__(self, r):
        threading.Thread.__init__(self)
        self.r = r
        self.count = 0
    def run(self):
        while True:
            time.sleep(1)
            self.count = self.count + 1
            self.r.publish('a', self.count)

background = WriteThread(r)
background.start()

pubsub = r.pubsub()
pubsub.subscribe('a')
pubsub.subscribe('b')
pubsub.subscribe('c')
print('-------------')

while True:
    for item in pubsub.listen():
        print(item)
