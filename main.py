import argparse
import logging
import os
import uuid
from datetime import datetime
from sqlite3 import DatabaseError

from slack_bolt import App

from blockresults import BlockResults
from database import Database
from image import Image
from logsetup import LogSetup
from tenor_search import Tenor

LOG_LOC = "log_slack_tenor"

# Argparse
parser = argparse.ArgumentParser(description="Post messages to slack if a cryptocurrency has changed price significantly")
parser.add_argument("slack bot token",
                    help="Slack Bot Token")
parser.add_argument("slack signing secret",
                    help="Slack Signing Secret")
parser.add_argument("tenor api key",
                    help="Tenor API Key")
parser.add_argument("--port", "-p", default=1300, type=int,
                    help="Port for slash commands + actions")
parser.add_argument("--log-file", "-lf", action="store_true",
                    help=f"Output logs into files in /{LOG_LOC}")
parser.add_argument("--disable-stdout", "-dso", action="store_true",
                    help="Disable log messages lower than ERROR from appearing in stdout")
parser.add_argument("--disable-stderr", "-dse", action="store_true",
                    help="Disable error messages from appearing in stdout (requires --disable-stdout to also be set)")
args = parser.parse_args()


# Initializes your app with your bot token and signing secret
Tenor.TENOR_API_KEY = getattr(args, "tenor api key")
LogSetup.setup(logging.INFO, not args.disable_stdout, not args.disable_stderr, args.log_file, LOG_LOC)

app = App(
    token=getattr(args, "slack bot token"),
    signing_secret=getattr(args, "slack signing secret")
)

@app.error
def error_handler(error, body, logger, respond):
    logger.exception(f"Error: {error}")
    logger.info(f"Request body: {body}")

    if respond is not None:
        respond("Encountered an error processing request. Please contact AgentKay for help", replace_original=False, response_type="ephemeral")

@app.command(command="/tenor")
def tenor_search(ack, respond, command):
    conversation_id = command['channel_id']
    conversation = command['channel_name']
    user_id = command['user_id']
    username = command['user_name']
    query_str = command['text']

    block_uid = str(uuid.uuid4())
    logging.info(f"Received new request {block_uid} from user '{username}' ({user_id}) in channel '{conversation}' ({conversation_id}). Query: {query_str}")
    ack()

    with Database() as db:
        cursor = db.execute("""INSERT INTO slack_request (timestamp, user_id, conversation_id, block_uid, search_string, status)
            VALUES (?, ?, ?, ?, ?, ?)""", (
            datetime.now().isoformat(),
            user_id,
            conversation_id,
            block_uid,
            query_str,
            'SELECTING'
        ))
        if cursor.rowcount != 1:
            raise DatabaseError(f"Error creating record. Rowcount: {cursor.rowcount}")

    image = Tenor(block_uid).next_image()
    results = BlockResults(block_uid, image, user_id, query_str)
    respond(blocks=results.get_ephemeral_message(), response_type="ephemeral")

@app.action("action_send")
def send_message(ack, respond, action):
    block_uid = action.get('block_id')
    logging.info(f"Received send request for {block_uid}")
    ack()

    tenor = Tenor(block_uid)
    request = tenor.fetch_request()

    image = tenor.get_send_image_and_delete_others()
    results = BlockResults(block_uid, image, request['user_id'], request['search_string'])
    respond(blocks=results.get_command_post_message(), response_type="in_channel", delete_original=True)

    with Database() as db:
        cursor = db.execute("""
            UPDATE slack_request
            SET status = 'POSTED'
            WHERE block_uid = ?""",
            (block_uid, )
        )
        if cursor.rowcount == 1:
            logging.info(f"Set message {block_uid} as posted")
        else:
            raise DatabaseError(f"Error updating status. Rowcount: {cursor.rowcount}")
    tenor.register_image_as_shared(image)

@app.action("action_next")
def next_message(ack, respond, action):
    block_uid = action.get('block_id')
    logging.info(f"Received next request for {block_uid}")
    ack()

    tenor = Tenor(block_uid)
    request = tenor.fetch_request()

    image = tenor.next_image()
    results = BlockResults(block_uid, image, request['user_id'], request['search_string'])
    respond(blocks=results.get_ephemeral_message(), response_type="ephemeral")

@app.action("action_cancel")
def delete_message(ack, respond, action):
    block_uid = action.get('block_id')
    logging.info(f"Received cancel request for {block_uid}")
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
            logging.info(f"Deleted message {block_uid}")
        else:
            raise DatabaseError(f"Error updating status. Rowcount: {cursor.rowcount}")

# Start your app
if __name__ == "__main__":
    app.start(port=args.port, path="/tenor")
