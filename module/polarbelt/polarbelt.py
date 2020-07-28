# https://www.oreilly.com/library/view/getting-started-with/9781491900550/ch04.html
# https://stackoverflow.com/questions/52882552/getting-heart-rate-variability-from-polar-h10-uwp
# https://github.com/watsonix/node-ble-hr/blob/master/index.js
# https://github.com/Lawreros/PolarStrapBLE/blob/master/Scenario2_Client.xaml.cs
# https://www.raywenderlich.com/231-core-bluetooth-tutorial-for-ios-heart-rate-monitor
# https://github.com/danielfppps/hbpimon/blob/master/hb.py
# https://stackoverflow.com/questions/58778739/polar-h10-to-rpi-zero-w-hr-notifications-stop-after-ca-100s-without-error-mess
# https://stackoverflow.com/questions/56330018/how-to-read-and-convert-bluetooth-characteristic-from-byte-data-to-proper-values
# https://github.com/oesmith/gatt-xml/blob/master/org.bluetooth.characteristic.heart_rate_measurement.xml
# https://github.com/polarofficial/create-mobile-app-for-polar-sensors

import asyncio
from bleak import BleakClient


HR_UUID = "00002a37-0000-1000-8000-00805f9b34fb"
configfile = {"MAC": "F7:9E:36:E5:85:42"}    # mock for now


class PolarClient:

    def __init__(self, configfile):
        self.loop = asyncio.get_event_loop()
        self.ble_client = BleakClient(configfile["MAC"], loop=self.loop)

    async def connect(self):
        await self.ble_client.connect()
        await self.ble_client.start_notify(HR_UUID, self.data_handler)

    def start(self):
        asyncio.ensure_future(self.connect())
        self.loop.run_forever()

    async def stop(self):
        print("disconnecting")
        await self.ble_client.stop_notify(HR_UUID, self.data_handler)
        await self.ble_client.disconnect()

    def data_handler(self, sender, data):
        # print(list(data))    # bytes to int
        # data has up to 6 bytes:
        # byte 1: flags
        #   00 = only HR
        #   16 = HR and RR(s)
        # byte 2: HR
        # byte 3 and 4: RRI1
        # byte 5 and 6: RRi2 (if present)

        # Polar H10 Heart Rate Characteristics (UUID: 00002a37-0000-1000-8000-00805f9b34fb)
        # + Energy expenditure is not transmitted
        # + HR only transmitted as uint8, no need to check if HR is transmitted as uint8 or uint16
        # Acceleration and ECG only available via Polar SDK
        bytes = list(data)
        if bytes[0] == 00:
            print(f"HR={data[1]}")
        if bytes[0] == 16:
            ibis = []
            for i in range(2, len(bytes), 2):
                ibis.append(data[i] + 256 * data[i + 1])
            print(f"HR={data[1]}, IBI={ibis}")


if __name__ == "__main__":
    polar = PolarClient(configfile).start()
    if (SystemExit, KeyboardInterrupt, RuntimeError):
        polar.stop()
