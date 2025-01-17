class Card:
    count_id = 0

    def __init__(self, first_name, last_name, card_number, expiry_date, cvc_number):
        Card.count_id += 1
        self.__first_name = first_name
        self.__last_name = last_name
        self.__card_id = Card.count_id
        self.__card_number = card_number
        self.__expiry_date = expiry_date
        self.__cvc_number = cvc_number

    def get_first_name(self):
        return self.__first_name

    def get_last_name(self):
        return self.__last_name

    def get_card_id(self):
        return self.__card_id

    def get_card_number(self):
        return self.__card_number

    def get_expiry_date(self):
        return self.__expiry_date

    def get_cvc_number(self):
        return self.__cvc_number

    def set_card_id(self, card_id):
        self.__card_id = card_id

    def set_first_name(self, first_name):
        self.__first_name = first_name

    def set_last_name(self, last_name):
        self.__last_name = last_name

    def set_card_number(self, card_number):
        self.__card_number = card_number

    def set_expiry_date(self, expiry_date):
        self.__expiry_date = expiry_date

    def set_cvc_number(self, cvc_number):
        self.__cvc_number = cvc_number
