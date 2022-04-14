import telebot
from telebot.types import InputMediaPhoto, InputMedia
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType


# tgbot
tgtoken = ""  # вписать token tg бота
tggroupid =  # вписать id группы
tgbot = telebot.TeleBot(tgtoken, parse_mode='HTML')


# vkbot
vktoken = ""  # вписать token vk бота
vkgroupid = ""  # вписать id группы
vksession = vk_api.VkApi(token=vktoken)
longpoll = VkBotLongPoll(vksession, vkgroupid)


def tgsend_message(message):
    tgbot.send_message(tggroupid, text=message)


def tgsend_photo(photo, caption):
    tgbot.send_photo(tggroupid, photo=photo, caption=caption)


def tgsend_mediagroup(media):
    tgbot.send_media_group(tggroupid, media)


def get_photos(attachments):
    photos = []
    for attachment in attachments:
        if attachment['type'] == 'photo':
            photo = attachment['photo']
            for size in photo['sizes']:
                if size['type'] == 'y':
                    photos.append(InputMediaPhoto(size['url']))
    return photos


def listen():
    try:
        for event in longpoll.listen():
            if event.type == VkBotEventType.WALL_POST_NEW:
                post = event.obj
                attachments = post.attachments
                if attachments:
                    # вложения по типам
                    photos = get_photos(attachments)

                    media = photos  # все вложения
                    if len(attachments) > 1:
                        media[-1].caption = post.text  # добавляет текст к последнему вложению
                        tgsend_mediagroup(media)
                    elif len(photos) == 1:
                        tgsend_photo(photos[0].media, {post.text})
                elif post.text:
                    tgsend_message(f'{post.text}')
    except Exception:
        listen()


listen()
