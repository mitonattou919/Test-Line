# coding: utf-8

import json
import base64
import hashlib
import hmac
import requests
import random
import six

from io import BytesIO

from linebot import LineBotApi
from linebot import WebhookHandler
from linebot.models import TextSendMessage
from linebot.exceptions import LineBotApiError
from linebot.exceptions åimport InvalidSignatureError


with open('config.json', 'r') as f:
    data = f.read()
config = json.loads(data)

#         1         2         3         4         5         6         7
# 234567890123456789012345678901234567890123456789012345678901234567890123456789


# {START detect text from image]
def detect_text(image_request):

    from google.cloud import vision

    client = vision.ImageAnnotatorClient()
    image = vision.types.Image(content=image_request)
    response = client.document_text_detection(image=image)
    return response.full_text_annotation.text
# [END detect text from image]


# [START translate text]
def translate_text(target, text):

    from google.cloud import translate_v2 as translate
    translate_client = translate.Client()

    print(target)
    print(text)

    if isinstance(text, six.binary_type):
        text = text.decode('utf-8')

    result = translate_client.translate(
        text, target_language=target)

    print(result['translatedText'])

    return result['translatedText']
# [END translate text]


# [START verify Authorization Header]
def verify_auth(request):

    channel_secret = config.get('CHANNEL_SECRET')
    handler = WebhookHandler(channel_secret)

    body = request.get_data(as_text=True)
    signature = request.headers['X-Line-Signature']

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print('Invalid signature.')
        return 'Invalid signature.', 400

    return 'OK'

# [END verify Authorization Header]


# [START parse message and build payload]
def reply_message(request):

    request_json = request.get_json(silent=True)

    if request_json:

        reply_token = request_json['events'][0]['replyToken']
        message_type = request_json['events'][0]['message']['type']
        user_id = request_json['events'][0]['source']['userId']

        line_bot_api = LineBotApi(config.get('ACCESS_TOKEN'))

        target_lang = 'en'

        if message_type == 'text':
            user_message = request_json['events'][0]['message']['text']
            reply_text = translate_text(target_lang, user_message)

        elif message_type == 'image':
            message_id = message_type = request_json['events'][0]['message']['id']
            print(message_id)
            reply_text = message_id

            try:
                message_content = line_bot_api.get_message_content(message_id)
            except LineBotApiError as e:
                raise ValuError(e)

            detected_text = detect_text(message_content.content)
            reply_text = translate_text(target_lang, detected_text)

        try:
            line_bot_api.reply_message(reply_token, TextSendMessage(text=reply_text))
        except LineBotApiError as e:
            raise ValueError(e)

    else:
        raise ValueError('Invalid request.')

# [END parse message and build payload]


# [START main]
def test_line(request):

    if request.method != 'POST':
        return 'bad method.', 405

    verify_auth(request)

    reply_message(request)

    return 'OK', 200

# [END main]


