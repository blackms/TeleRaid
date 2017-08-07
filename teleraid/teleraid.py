#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
import threading
from datetime import datetime, timedelta

from telepot.exception import TelegramError
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton

# Custom files and packages
from config.config import config
from static.stickers import stickers
from .utils import get_pokemon_name, get_move_name

log = logging.getLogger(__name__)


class TeleRaid(threading.Thread):
    def __init__(self, queue, session, event, name='TeleRaid'):
        self.stop_event = event

        self.__bot_token = config['bot_token']
        self.__chat_id = config['chat_id']

        self.__timezone = config.get('timezone', 0)
        self.__notify_levels = config['notify_levels']
        self.__notify_pokemon = config['notify_pokemon']

        self.__queue = queue
        self.__session = session
        super(TeleRaid, self).__init__()
        self.name = name

    def run(self):
        log.info("TeleRaid is running...")
        while self.stop_event:
            try:
                data_json = self.__queue.get(block=True)
                for elem in data_json:
                    self.__process_request(elem)
                raids_to_notify = self.__check_raids()
                for raid in raids_to_notify:
                    self.__notify(raid)
            except Exception as e:
                log.exception("Exception during regular runtime: {}".format(repr(e)))
                pass

            self.__queue.task_done()

    def __process_request(self, data_json):
        if data_json['type'] == 'raid':
            log.info("Raid received.")
            self.__add_raid(data_json['message'])

    def __add_raid(self, raid):
        if raid['pokemon_id'] and raid['gym_id'] not in self.__session.raids:
            raid['notified_battle'] = False
            self.__session.raids[raid['gym_id']] = raid
            log.info("Raid added.")

    def __check_raids(self):
        raids_to_notify = []
        for r in self.__session.raids:
            log.debug('Raid Level: {}, I am configured to notify Raid of level: {}'.format(
                self.__session.raids[r]['level'],
                self.__notify_levels
            ))
            if self.__session.raids[r]['level'] not in self.__notify_levels:
                continue

            if self.__session.raids[r]['pokemon_id'] not in self.__notify_pokemon:
                continue

            if (datetime.utcnow() > datetime.utcfromtimestamp(
                    self.__session.raids[r]['start'])):
                if not self.__session.raids[r]['notified_battle']:
                    log.info("Notifying about raid with Pokemon-ID {}.".format(self.__session.raids[r]['pokemon_id']))
                    raids_to_notify.append(self.__session.raids[r])
                else:
                    log.info(
                        "Already notified about raid of Pokemon-ID {}.".format(self.__session.raids[r]['pokemon_id']))
        log.info("Raids checked.")
        return raids_to_notify

    def __notify(self, raid):
        try:
            # Setup the message
            raid_end = ((datetime.utcfromtimestamp(raid['end']) +
                         timedelta(hours=self.__timezone))
                        .strftime("%H:%M"))
            raid_pokemon = get_pokemon_name(raid['pokemon_id'])
            raid_move_1 = get_move_name(raid['move_1'])
            raid_move_2 = get_move_name(raid['move_2'])
            text = ("\n\n<b>Raid - Level {} - {}</b>\n{} / {}\nRaid ends at <b>{}</b>.\n".format(
                raid['level'], raid_pokemon,
                raid_move_1, raid_move_2,
                raid_end)
            )
            inline_keyboard = [[
                InlineKeyboardButton(text="\xF0\x9F\x91\x8D Yes", callback_data='y'),
                InlineKeyboardButton(text="\xF0\x9F\x91\x8E No", callback_data='n')
            ]]
            keyboard_markup = InlineKeyboardMarkup(
                inline_keyboard=inline_keyboard)

            sticker_message = self.__send_sticker(
                chat_id=self.__chat_id,
                sticker=stickers[raid['pokemon_id']]
            )

            location_message = self.__send_location(
                chat_id=self.__chat_id,
                latitude=raid['latitude'],
                longitude=raid['longitude']
            )

            message = self.__send_message(text=text,
                                          chat_id=self.__chat_id,
                                          parse_mode="HTML",
                                          reply_markup=keyboard_markup)
            self.__session.messages[message['message_id']] = {
                'gym_id': raid['gym_id'],
                'text': message['text'],
                'poll': {
                    'yes': 0,
                    'no': 0,
                    'users': {}
                },
                'ids': {
                    'sticker_id': sticker_message['message_id'],
                    'location_id': location_message['message_id'],
                    'message_id': message['message_id']
                }
            }
            log.info('notify: {}'.format(self.__session.messages))
            raid['notified_battle'] = True
        except Exception as e:
            log.exception("Exception during notification process: {}"
                          .format(repr(e)))
            pass

    def __send_message(self, text, chat_id, parse_mode=None, reply_markup=None):
        log.info('send message to: {}'.format(chat_id))
        try:
            return self.__session.telegram_client.sendMessage(chat_id=chat_id,
                                                              text=text,
                                                              parse_mode=parse_mode,
                                                              reply_markup=reply_markup)
        except Exception as e:
            log.exception("Exception while sending message: {}"
                          .format(repr(e)))

    def __send_location(self, chat_id, latitude, longitude):
        try:
            return self.__session.telegram_client.sendLocation(chat_id=chat_id, latitude=latitude, longitude=longitude)
        except Exception as e:
            log.exception("Exception while sending location: {}"
                          .format(repr(e)))

    def __send_sticker(self, chat_id, sticker):
        try:
            return self.__session.telegram_client.sendSticker(chat_id=chat_id, sticker=sticker)
        except Exception as e:
            log.exception("Exception while sending sticker: {}"
                          .format(repr(e)))

    def __edit_message_reply_markup(self, msg_identifier, reply_markup):
        try:
            return self.__session.telegram_client.editMessageReplyMarkup(
                msg_identifier=msg_identifier,
                reply_markup=reply_markup
            )
        except TelegramError:
            log.warning("TelegramError - No change in message after updating.")
        except Exception as e:
            log.exception("Exception while editing keyboard markup: {}"
                          .format(repr(e)))
