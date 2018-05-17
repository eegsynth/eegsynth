# This example will collect data for 5 sec.
macAddress = "00:00:00:00:00:00"
# macAddress = "/dev/tty.BITalino-XX-XX-DevB" # on Mac OS replace XX-XX by the 4 final digits of the MAC address
running_time = 5

batteryThreshold = 30
acqChannels = [0, 1, 2, 3, 4, 5]
samplingRate = 1000
nSamples = 10
digitalOutput = [1,1]

# Connect to BITalino
device = BITalino(macAddress)

# Set battery threshold
device.battery(batteryThreshold)

# Read BITalino version
print(device.version())

# Start Acquisition
device.start(samplingRate, acqChannels)

start = time.time()
end = time.time()
while (end - start) < running_time:
        # Read samples
        print(device.read(nSamples))
        end = time.time()

# Turn BITalino led on
device.trigger(digitalOutput)

# Stop acquisition
device.stop()

# Close connection
device.close()
