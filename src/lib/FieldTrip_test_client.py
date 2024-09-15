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

print('-'*78)

# write some data
client.putHeader(2, 1000, FieldTrip.DATATYPE_FLOAT32)
for block in range(10):
    client.putData(np.random.rand(1000, 2).astype(np.float32))
    print('wrote 1000 samples, 2 channels')
print('-'*78)

H = client.getHeader()
print(H)
print('-'*78)

# read one second of data
begsample = 0
endsample = int(H.fSample-1)

D = client.getData(index=(begsample, endsample))
print(D.shape)
print(D)
print('-'*78)
