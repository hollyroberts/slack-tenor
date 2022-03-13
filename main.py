import os
import requests
import json
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

TENOR_API_KEY = os.environ.get("TENOR_API_KEY")
TENOR_SEARCH_URL = "https://g.tenor.com/v1/search"
TENOR_LOCALE = "en_GB"

resp = requests.get(TENOR_SEARCH_URL, params={
    "key": TENOR_API_KEY,
    "q": "Hello",
    "locale": TENOR_LOCALE,
    "limit": 5,
    "media_filter": "basic"
})
print(resp.status_code)
print(json.dumps(json.loads(resp.content), indent=4))

# # Initializes your app with your bot token and socket mode handler
# app = App(token=os.environ.get("SLACK_BOT_TOKEN"))
#
# # Start your app
# if __name__ == "__main__":
#     SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
