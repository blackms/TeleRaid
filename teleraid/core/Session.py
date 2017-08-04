class Session(object):
    messages = dict()
    raids = dict()
    chat_id = str()
    telegram_client = None

    def __init__(self, name, telegram_client):
        self.name = name
        self.telegram_client = telegram_client
