class User:
    count_id = 0

    def __init__(self, name, title, amount_paid, refund_status):
        User.count_id += 1
        self.__user_id = User.count_id
        self.__name = name
        self.__title = title
        self.__amount_paid = amount_paid
        self.__refund_status = refund_status

    # Getters
    def get_user_id(self):
        return self.__user_id

    def get_name(self):
        return self.__name

    def get_title(self):
        return self.__title

    def get_amount_paid(self):
        return self.__amount_paid

    def get_refund_status(self):
        return self.__refund_status

    # Setters
    def set_user_id(self, user_id):
        self.__user_id = user_id

    def set_name(self, name):
        self.__name = name

    def set_title(self, title):
        self.__title = title

    def set_amount_paid(self, amount_paid):
        self.__amount_paid = amount_paid

    def set_refund_status(self, refund_status):
        self.__refund_status = refund_status
