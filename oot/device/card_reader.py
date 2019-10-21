from mfrc522 import SimpleMFRC522


class CardReader(SimpleMFRC522):
    def read_uid_no_block(self):
        (status, TagType) = self.READER.MFRC522_Request(self.READER.PICC_REQIDL)
        if status != self.READER.MI_OK:
            return None
        (status, uid) = self.READER.MFRC522_Anticoll()
        if status != self.READER.MI_OK:
            return None
        return "{:02x}{:02x}{:02x}{:02x}".format(uid[0], uid[1], uid[2], uid[3])

    def scan_card(self):
        uid = False
        while not uid:
            uid = self.read_uid_no_block()
        return uid
