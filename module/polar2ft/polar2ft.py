
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
MAC = "F7:9E:36:E5:85:42"


def data_handler(sender, data):
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
        print(f"HR={data[1]}, IBI={data[2] + 256*data[3]}")

async def run(address, loop, debug=False):

    async with BleakClient(address, loop=loop) as client:    # timeout?
        await client.is_connected()

        while True:
            await client.start_notify(HR_UUID, data_handler)

        # for service in client.services:
        #     log.info("[Service] {0}: {1}".format(service.uuid, service.description))
        #     for char in service.characteristics:
        #         if "read" in char.properties:
        #             try:
        #                 value = bytes(await client.read_gatt_char(char.uuid))
        #             except Exception as e:
        #                 value = str(e).encode()
        #         else:
        #             value = None
        #         log.info(
        #             "\t[Characteristic] {0}: ({1}) | Name: {2}, Value: {3} ".format(
        #                 char.uuid, ",".join(char.properties), char.description, value
        #             )
        #         )
        #         for descriptor in char.descriptors:
        #             value = await client.read_gatt_descriptor(descriptor.handle)
        #             log.info(
        #                 "\t\t[Descriptor] {0}: (Handle: {1}) | Value: {2} ".format(
        #                     descriptor.uuid, descriptor.handle, bytes(value)
        #                 )
        #             )


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run(MAC, loop, True))
