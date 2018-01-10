import socket
import struct

class ArtNet():
    def __init__(self, ip="192.168.1.255", port=6454):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        # broadcast ip
        self.ip = ip
        # UDP ArtNet Port
        self.port = port

    def broadcastDMX(self, dmxdata, address):
        content = []
        # Name, 7byte + 0x00
        content.append("Art-Net\x00")
        # OpCode ArtDMX -> 0x5000, Low Byte first
        content.append(struct.pack('<H', 0x5000))
        # Protocol Version 14, High Byte first
        content.append(struct.pack('>H', 14))
        # Order -> nope -> 0x00
        content.append("\x00")
        # Eternity Port
        content.append(chr(1))
        # Address
        net, subnet, universe = address
        content.append(struct.pack('<H', net << 8 | subnet << 4 | universe))
        # Length of DMX Data, High Byte First
        content.append(struct.pack('>H', len(dmxdata)))
        # DMX Data
        for d in dmxdata:
            content.append(chr(d))
        # stitch together
        content = "".join(content)
        # send
        self.s.sendto(content, (self.ip, self.port))

    def close(self):
        self.s.close()

if __name__ == "__main__":
	import time
	artnet = ArtNet()
	address = [0, 0, 1]
	dmx_on   = [64] * 512
	dmx_off  = [ 0] * 512
	while True:
		artnet.broadcastDMX(dmx_on, address)
		time.sleep(0.1)
		artnet.broadcastDMX(dmx_off, address)
		time.sleep(0.1)
	artnet.close()
