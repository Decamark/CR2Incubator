# -*- coding: utf-8 -*-

import sys
from struct import pack, unpack

def iprint(s, level):
    print(' '*level*2 + s)

class Incubator:
    def open_raw(self, path):
        raw_f = open(path, 'rb')
        self.all_bytes = raw_f.read()
        raw_f.close()

    def save_jpg(self, path):
        jpg_f = open(path, 'wb')
        jpg_f.write(self.final_jpg_bytes)
        jpg_f.close()

    def prepare(self):
        self.offset_ifd0       = unpack('<I', self.all_bytes[4:8])[0]
        self.offset_1st_ifd0   = self.offset_ifd0+2
        self.offset_ifd3       = unpack('<I', self.all_bytes[12:16])[0]
        self.offset_1st_ifd3   = self.offset_ifd3+2
        self.offset_subifd     = self.find_tag_call(self.offset_1st_ifd0, 0x8769, self.get_value)
        self.offset_1st_subifd = self.offset_subifd+2

    def find_tag_call(self, curr_ptr, tag_id_to_find, callback):
        while True:
            tag_id    = unpack('<H', self.all_bytes[curr_ptr:curr_ptr+2])[0]
            tag_type  = unpack('<H', self.all_bytes[curr_ptr+2:curr_ptr+4])[0]
            value_num = unpack('<I', self.all_bytes[curr_ptr+4:curr_ptr+8])[0]
            value     = unpack('<I', self.all_bytes[curr_ptr+8:curr_ptr+12])[0]

            if tag_id == tag_id_to_find:
                return callback(tag_id, tag_type, value_num, value)

            curr_ptr = curr_ptr+12

    @staticmethod
    def get_size(tag_id, tag_type, size, value):
        iprint('Size is: 0x{:X}'.format(size), 1)
        return size

    @staticmethod
    def get_value(tag_id, tag_type, size, value):
        iprint('Value is: 0x{:X}'.format(value), 1)
        return value

    # Extract datetime
    def get_datetime(self):
        offset_datetime   = self.find_tag_call(self.offset_1st_subifd, 0x9003, self.get_value)
        size_datetime     = self.find_tag_call(self.offset_1st_subifd, 0x9003, self.get_size)

        self.datetime = self.all_bytes[offset_datetime:offset_datetime+size_datetime]
        iprint('DateTime is: {}'.format(self.datetime.decode('utf-8')), 1)

        return self.datetime.decode('utf-8')

    # Exif APP1 marker (Taken date is embedded)
    # (Note that pre-existing marker is untouched)
    def make_exif(self):
        exif = \
            [ 0xFF, 0xE1 ] + \
            list(pack('>H', 60+len(self.datetime))) + \
            [ 0x45, 0x78, 0x69, 0x66, 0x00, 0x00 ] + \
            [ 0x49, 0x49, 0x2A, 0x00, 0x08, 0x00, 0x00, 0x00] + \
            [ 0x02, 0x00 ] + \
            [ 0x12, 0x01, 0x03, 0x00, 0x01, 0x00, 0x00, 0x00 ] + list(pack('<I', self.orientation)) + \
            [ 0x69, 0x87, 0x04, 0x00, 0x01, 0x00, 0x00, 0x00, 0x26, 0x00, 0x00, 0x00 ] + \
            [ 0x00, 0x00, 0x00, 0x00 ] + \
            [ 0x01, 0x00 ] + \
            [ 0x03, 0x90, 0x02, 0x00, 0x14, 0x00, 0x00, 0x00, 0x34, 0x00, 0x00, 0x00 ] + \
            list(self.datetime)
        return bytearray(exif)

    # Extract loosy JPEG in IFD0
    def make_loosy_jpg(self):
        offset_raw = self.find_tag_call(self.offset_1st_ifd0, 0x0111, self.get_value)
        size_raw   = self.find_tag_call(self.offset_1st_ifd0, 0x0117, self.get_value)
        jpg_bytes  = self.all_bytes[offset_raw:offset_raw+size_raw]

        self.orientation = self.find_tag_call(self.offset_1st_ifd0, 0x0112, self.get_value)

        exif = self.make_exif()

        self.final_jpg_bytes = jpg_bytes[:2] + exif + jpg_bytes[2:]

    # Extract loseless JPEG in IFD3
    # (Note that this image is too large to save without compressing. Don't recommand)
    def make_loseless_jpg(self):
        offset_raw = self.find_tag_call(offset_1st_ifd3, 0x0111, self.get_value)
        size_raw   = self.find_tag_call(offset_1st_ifd3, 0x0117, self.get_value)
        jpg_bytes  = self.all_bytes[offset_raw:offset_raw+size_raw]

        self.orientation = self.find_tag_call(self.offset_1st_ifd0, 0x0112, self.get_value)

        exif = self.make_exif()

        self.final_jpg_bytes = jpg_bytes[:2] + exif + jpg_bytes[2:]
