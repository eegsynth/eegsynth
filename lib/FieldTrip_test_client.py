import FieldTrip
import numpy as np

client = FieldTrip.Client()

port = 1972
while not client.isConnected and port<2000:
    try:
        client.connect('localhost', port=port)
        print('Connected on', ('localhost', port))
    except:
        port += 1

H = client.getHeader()
print(H)

# read one second of data
begsample = 0
endsample = int(H.fSample-1)

D = client.getData(index=(begsample, endsample))
print(D)
print(len(D))
