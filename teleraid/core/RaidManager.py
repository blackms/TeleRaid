from threading import Thread


class RaidManager(Thread):
    def __init__(self, session, logger, name='RaidManager'):
        self.session = session
        self.logger = logger
        super(RaidManager, self).__init__()
        # Override Thread name after pass control to father class.
        self.name = name

    def run(self):
        pass

