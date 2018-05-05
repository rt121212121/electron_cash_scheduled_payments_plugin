import datetime

DISPLAY_AS_AMOUNT = 1
DISPLAY_AS_ADDRESS = 2
DISPLAY_AS_DATETIME = 3

class ValueFormatter:
    def __init__(self, window):
        self.window = window
        self.wallet = window.wallet
        
    def format_contact(self, address):
        if address in self.wallet.contacts.keys():
            contact_type, contact_name = self.wallet.contacts[address]
            return contact_name +" <"+ address +">"        

    def format_value(self, value, display_type=0):
        if display_type == DISPLAY_AS_AMOUNT:
            return self.window.format_amount(value, whitespaces = False) +' '+ self.window.base_unit()
        elif display_type == DISPLAY_AS_ADDRESS:
            contact_name = self.format_contact(value)
            if contact_name is None:
                contact_name = value
            return contact_name
        elif display_type == DISPLAY_AS_DATETIME:
            if value is None:
                return "-"
            return datetime.datetime.fromtimestamp(value).strftime("%Y-%m-%d %H:%M")
        return str(value)

