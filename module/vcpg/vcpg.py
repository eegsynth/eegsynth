import ConfigParser
import redis

config = ConfigParser.ConfigParser()
config.read('vcpg.ini')

for section in config.sections():
    print section
    for option in config.options(section):
        print " ", option, "=", config.get(section, option)


r = redis.StrictRedis(host=config.get('input','hostname'), port=int(config.get('input','port')), db=0)
r.set('foo', 'bar')
r.get('foo')
