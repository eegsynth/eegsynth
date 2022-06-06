import FieldTrip
import time

server = FieldTrip.Server()
server.connect(port=1972)
try:
    while True:
        server.loop()
except KeyboardInterrupt:
    print('stopping')
finally:
    server.disconnect()
