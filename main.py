import os
import uuid
from datetime import datetime

from slack_bolt import App

from database import Database
from image import Image
from tenor_search import Tenor

SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET")
PORT = 3456

# Initializes your app with your bot token and signing secret
app = App(
    token=SLACK_BOT_TOKEN,
    signing_secret=SLACK_SIGNING_SECRET
)

def block_results(block_uid: str, image: Image):
    return [
        {
            "title": {
                "type": "plain_text",
                "text": image.get_description()
            },
            "type": "image",
            "image_url": image.get_url(),
            "alt_text": image.get_description()
        },
        {
            "type": "actions",
            "block_id": block_uid,
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Send",
                        "emoji": True
                    },
                    "style": "primary",
                    "value": "Send",
                    "action_id": "action_send"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Next",
                        "emoji": True
                    },
                    "value": "Next",
                    "action_id": "action_next"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Cancel",
                        "emoji": True
                    },
                    "value": "Cancel",
                    "action_id": "action_cancel"
                }
            ]
        }
    ]

@app.command(command="/tenor")
def tenor_search(ack, respond, command):
    conversation_id = command['channel_id']
    conversation = command['channel_name']
    user_id = command['user_id']
    username = command['user_name']
    query_string = command['text']

    block_uid = str(uuid.uuid4())
    print(f"Received new request {block_uid} from user '{username} ({user_id}) in channel '{conversation}' ({conversation_id}). Query: {query_string}")
    ack()

    with Database() as db:
        cursor = db.execute("""INSERT INTO slack_request (timestamp, user_id, conversation_id, block_uid, search_string, status)
            VALUES (?, ?, ?, ?, ?, ?)""", (
            datetime.now().isoformat(),
            user_id,
            conversation_id,
            block_uid,
            query_string,
            'SELECTING'
        ))
        if cursor.rowcount != 1:
            raise f"Error creating record. Rowcount: {cursor.rowcount}"

    image = Tenor(block_uid).next_image()
    respond(blocks=block_results(block_uid, image), response_type="ephemeral")

@app.action("action_send")
def send_message(ack, respond, action):
    block_uid = action.get('block_id')
    print(f"Received send request for {block_uid}")
    ack()

    image = Tenor(block_uid).get_send_image_and_delete_others()
    respond(blocks=block_results(block_uid, image), response_type="in_channel", delete_original=True)

@app.action("action_next")
def next_message(ack, respond, action):
    block_uid = action.get('block_id')
    print(f"Received next request for {block_uid}")
    ack()

    image = Tenor(block_uid).next_image()
    respond(blocks=block_results(block_uid, image), response_type="ephemeral")

@app.action("action_cancel")
def delete_message(ack, respond, action):
    block_uid = action.get('block_id')
    print(f"Received cancel request for {block_uid}")
    ack()
    respond(delete_original=True)

    with Database() as db:
        cursor = db.execute("""
            UPDATE slack_request
            SET status = 'CANCELLED'
            WHERE block_uid = ?""",
            (block_uid, )
        )
        if cursor.rowcount == 1:
            print(f"Deleted message {block_uid}")
        else:
            print(f"Error updating status. Rowcount: {cursor.rowcount}")

# Start your app
if __name__ == "__main__":
    app.start(port=PORT, path="/tenor")
