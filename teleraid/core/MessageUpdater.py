import logging
import threading

from teleraid.utils import telepot_shiny

from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton

from telepot.exception import TelegramError


class MessageUpdater(threading.Thread):
    def __init__(self, session, logger, event, name):
        self.session = session
        self.logger = logger
        self.stop_event = event

        super(MessageUpdater, self).__init__()
        self.name = name

    def run(self):
        while self.stop_event:
            self.__update_messages()
            self.stop_event.wait(2)

    def __update_messages(self):
        self.logger.debug('Entering __update_messages method')
        offset = None
        retry_time = 1
        try:
            updates = self.session.telegram_client.getUpdates(offset=offset)
            updated_messages = []
            for u in updates:
                callback_query = u.get('callback_query', {})
                data = callback_query.get('data', None)
                message = callback_query.get('message', {})
                message_id = message.get('message_id', 0)
                if message_id:
                    updated_messages.append(message_id)
                    if message_id not in self.session.messages:
                        self.session.messages[message_id] = {
                            'gym_id': '',
                            'text': message['text'],
                            'entities': message['entities'],
                            'poll': {
                                'yes': 0,
                                'no': 0,
                                'users': {}
                            }
                        }

                    self.session.messages[message_id]['poll']['users'].update({
                        callback_query['from']['id']: {
                            'id': callback_query['from']['id'],
                            'data': data,
                            'username': callback_query['from']['first_name']
                        }
                    })

                update_id = u.get('update_id', None)
                if update_id and update_id >= offset:
                    offset = update_id + 1

            for message_id in updated_messages:
                poll = self.session.messages[message_id]['poll']
                poll['yes'] = 0
                poll['no'] = 0

                for user in poll['users']:
                    if poll['users'][user]['data'] == 'y':
                        poll['yes'] += 1
                    elif poll['users'][user]['data'] == 'n':
                        poll['no'] += 1

                if poll['yes'] or poll['no']:
                    text = self.session.messages[message_id]['text']
                    if 'entities' in self.session.messages[message_id]:
                        text = telepot_shiny(self.session.messages[message_id])

                    yes_string = ('<b>Yes</b>\n' + '\n'.join(
                        [poll['users'][user]['username']
                         for user in poll['users']
                         if poll['users'][user]['data'] == 'y']))
                    no_string = ('<b>No</b>\n' + '\n'.join(
                        [poll['users'][user]['username']
                         for user in poll['users']
                         if poll['users'][user]['data'] == 'n']))
                    text = (text.split('\n\n<b>Yes</b>')[0] + ('''\n{}\n{}\n'''.format(yes_string, no_string)))
                    inline_keyboard = [[
                        InlineKeyboardButton(
                            text=("\xF0\x9F\x91\x8D Yes ({})".format(poll['yes'])),
                            callback_data='y'),
                        InlineKeyboardButton(
                            text=("\xF0\x9F\x91\x8E No ({})".format(poll['no'])),
                            callback_data='n')
                    ]]
                    keyboard_markup = InlineKeyboardMarkup(
                        inline_keyboard=inline_keyboard)
                    self.__edit_message(
                        msg_identifier=(self.session.chat_id, message_id),
                        text=text,
                        parse_mode='HTML',
                        reply_markup=keyboard_markup
                    )
            retry_time = 1
        except Exception as e:
            self.logger.exception("Exception while updating messages: {}".format(repr(e)))
            retry_time *= 2

    def __edit_message(self, msg_identifier, text, parse_mode=None, reply_markup=None):
        try:
            return self.session.telegram_client.editMessageText(
                msg_identifier=msg_identifier,
                text=text,
                parse_mode=parse_mode,
                reply_markup=reply_markup
            )
        except TelegramError as e:
            self.logger.warning("TelegramError - No change in message after updating.")
        except Exception as e:
            self.logger.exception("Exception while editing message: {}".format(repr(e)))
