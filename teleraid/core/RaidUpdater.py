import threading

from datetime import datetime


class RaidUpdater(threading.Thread):
    def __init__(self, session, logger, event, name):
        self.session = session
        self.logger = logger
        self.stop_event = event

        super(RaidUpdater, self).__init__()
        self.name = name

    def update_raids(self):
        delete_raids = []
        delete_messages = []
        self.logger.debug('Entering update_raids method.')
        for r in self.session.raids:
            if datetime.utcnow() > datetime.utcfromtimestamp(self.session[r]['end']):
                delete_raids.append(r)
                for m in self.session.messages:
                    if r == self.session.messages[m].get('gym_id', ''):
                        try:
                            chat_id = self.session.chat_id
                            sticker_id = self.session.messages[m]['ids']['sticker_id']
                            location_id = self.session.messages[m]['ids']['location_id']
                            message_id = self.session.messages[m]['ids']['message_id']
                            self.__delete_message(msg_identifier=(chat_id, sticker_id))
                            self.__delete_message(msg_identifier=(chat_id, location_id))
                            self.__delete_message(msg_identifier=(chat_id, message_id))
                        except Exception as e:
                            self.logger.exception("Exception while updating raids: {}".format(repr(e)))
                            pass
                        delete_messages.append(m)
                        self.logger.info('Deleted outdated message.')
        for r in delete_raids:
            del self.session.raids[r]
        for m in delete_messages:
            del self.session.messages[m]
        self.logger.debug('Raid updated.')

    def run(self):
        while self.stop_event:
            self.update_raids()
            self.stop_event.wait(10)

    def __delete_message(self, msg_identifier):
        try:
            return self.session.telegram_client.deleteMessage(msg_identifier=msg_identifier)
        except Exception as e:
            self.logger.exception("Exception while deleting message: {}".format(repr(e)))
