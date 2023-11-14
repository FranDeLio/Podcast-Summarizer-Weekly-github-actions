from datetime import datetime

PODCASTS_DICT = {
    "PhilosophizeThis": "https://philosophizethis.libsyn.com/rss",
    "EconTalk": "https://feeds.simplecast.com/wgl4xEgL"
    #"LexFridman": "https://lexfridman.com/feed/podcast/"",
}

START_DATE = datetime.strptime("01-10-2023", "%d-%m-%Y").date()

MAX_TOKEN_LENGTH = 15_500
MAX_STRING_LENGTH = 70_000

GPT_MODEL = "gpt-3.5-turbo-1106"
TEMPERATURE = 0
