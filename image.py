import logging

class Image:
    MAX_IMAGE_SIZE = 2 * (1024**2)

    def __init__(self, image_json):
        self.__json = image_json

    def get_description(self):
        return self.__json['content_description']

    def get_id(self):
        return self.__json['id']

    def get_url(self):
        media = self.__json['media'][0]
        items = {k: v for (k, v) in media.items() if v['size'] < Image.MAX_IMAGE_SIZE and k.endswith('gif')}
        item = sorted(items.items(), key=lambda it: -it[1]['size'])[0]

        logging.info(f"Selected type: {item[0]} of size {item[1]['size']:,} bytes")
        return item[1]['url']
