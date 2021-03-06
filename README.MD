# TeleRaid
*a webhook-based notifier for Pokemon GO raids*

## What is this?
TeleRaid focuses on receiving webhook data from various services to display upcoming Raids in a Telegram Channel to notify its Users and let them vote for attendance.

## How to install?
```
git clone https://github.com/Arengo/TeleRaid.git
cd TeleRaid
pip install -r requirements.txt
```

## How to update?
```
git pull
pip install -r requirements.txt --upgrade
```
Check for changes in the ``config.example.py`` file and adjust your ``config.py`` accordingly.

## How to use?
1. Put your Telegram ``bot_id`` as well as the ``chat_id`` you want to send notifications to, into the ``config.example.py`` file by replacing the placeholders ``#Placeholder#``.
3. Specify a webhook address to listen to into ``config.example.py``, default is ``127.0.0.1:4001``.
2. Rename ``config.example.py`` to ``config.py``.
4. Setup your service to send webhooks to above's address.
5. Run the bot with
```bash
python teleraid.py
```

**Have fun :-)**
