from image import Image

class BlockResults:
    def __init__(self, block_uid: str, image: Image, user_id: str, query_str: str):
        self.user_id = user_id
        self.image = image
        self.block_uid = block_uid
        self.query_str = query_str

    def get_ephemeral_message(self):
        return [
            self.__get_image(),
            self.__get_action_buttons()
        ]

    def get_command_post_message(self):
        return [
            self.__get_user_posted_section(),
            self.__get_image()
        ]

    def __get_user_posted_section(self):
        return {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"<@{self.user_id}> /tenor {self.query_str}"
            },
        }

    def __get_image(self):
        description = self.image.get_description()
        description = description.removesuffix(" GIF")

        return {
            "type": "image",
            "image_url": self.image.get_url(),
            "alt_text": description
        }

    def __get_action_buttons(self):
        return {
            "type": "actions",
            "block_id": self.block_uid,
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
