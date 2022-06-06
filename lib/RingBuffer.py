class RingBuffer:
    """
    Class that implements a ring or cyclic buffer that automatically wraps around.
    It works with bytes and has the methods append() and read().
    """

    def __init__(self, length):
        self.buffer = bytearray(length)
        self.length = length
        self.count = 0

    def append(self, data):
        """
        append(bytes) - add bytes to the end of the buffer.
        """
        if len(data)>self.length:
            # remove the part of the data that does not fit anyway
            self.count += int(len(data)/self.length)*self.length
            data = data[-self.length:]

        begbyte = self.count % self.length
        endbyte = (self.count + len(data) - 1) % self.length + 1

        if endbyte<begbyte:
            # insert the first section towards the end
            numbytes = self.length - begbyte + 1
            self.buffer[begbyte:self.length] = data[0:numbytes]
            # insert the second section at the start
            self.buffer[0:endbyte] = data[numbytes:]
        elif endbyte>begbyte:
            # simply insert the data
            self.buffer[begbyte:endbyte] = data
        else:
            # there is nothing to insert
            pass
        self.count += len(data)

    def read(self, begbyte, endbyte):
        """
        read(begbyte, endbyte) - read bytes from a specific location in the buffer.
        """
        if self.count>self.length:
            begavailable = self.count - self.length
        else:
            begavailable = 0
        endavailable = self.count
        
        if begbyte<begavailable:
            raise RuntimeError('Cannot read before the start of the available data.')
        elif endbyte>endavailable or begbyte>endavailable-1:
            raise RuntimeError('Cannot read past the end of the available data.')
        elif endbyte<begbyte:
            raise RuntimeError('Invalid selection.')
        begbyte = begbyte % self.length
        endbyte = (endbyte - 1) % self.length + 1
    
        if endbyte<=begbyte:
            data = self.buffer[begbyte:] + self.buffer[0:endbyte]
        else:
            data = self.buffer[begbyte:endbyte]
        return data
