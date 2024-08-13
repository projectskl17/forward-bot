from os import environ
import re

id_pattern = re.compile(r'^.\d+$')
def is_enabled(value, default):
    if value.lower() in ["true", "yes", "1", "enable", "y"]:
        return True
    elif value.lower() in ["false", "no", "0", "disable", "n"]:
        return False
    else:
        return default

SESSION = environ.get("SESSION", "forward bot")
# API_ID = int(environ["API_ID"])
API_ID = ... # api id
# API_HASH = environ["API_HASH"]
API_HASH ='api hash here'
#BOT_TOKEN = environ["BOT_TOKEN"]
BOT_TOKEN = 'bot token here'
# LOG_CHANNEL = int(environ.get("LOG_CHANNEL", 0))
LOG_CHANNEL = ... # userid for logs and start message
PORT = int(environ.get("PORT", "8080"))
ADMINS = [int(admin) if id_pattern.search(admin) else admin for admin in environ.get('ADMINS', '1630507023 6891576089').split()]
UPSTREAM_REPO = environ.get("UPSTREAM_REPO", "https://github.com/Joelkb/File-Forward-Bot")
# DB_URI = environ.get('DB_URI', "")
DB_URI = "mongodb url here"
DB_NAME = environ.get('DB_NAME', "forwardbot")