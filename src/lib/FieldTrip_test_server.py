import FieldTrip

server = FieldTrip.Server()

port = 1972
while not server.isConnected and port<2000:
    try:
        server.connect(port=port)
    except:
        port += 1

try:
    while True:
        server.loop()
except KeyboardInterrupt:
    print('stopping')
finally:
    server.disconnect()
