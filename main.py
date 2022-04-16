from pathlib import Path
import telebot
from telebot.types import InputMediaPhoto, InputMediaVideo
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
import youtube_dl


# tgbot
tgtoken = ""  # вписать token tg бота
tggroupid =  # вписать id группы(кавычки не пропущены, они не нужны)
tgbot = telebot.TeleBot(tgtoken, parse_mode='HTML')


# vkbot
vktoken = ""  # вписать token vk бота
vkgroupid = ""  # вписать id группы
vksession = vk_api.VkApi(token=vktoken)
longpoll = VkBotLongPoll(vksession, vkgroupid)


def tgsend_mediagroup(media):
    tgbot.send_media_group(tggroupid, media)


def tgsend_photo(photo, caption):
    tgbot.send_photo(tggroupid, photo=photo, caption=caption)


def tgsend_video(video, caption):
    tgbot.send_video(tggroupid, video=video, caption=caption)


def tgsend_message(message):
    tgbot.send_message(tggroupid, text=message)


# получает все фотографии
def get_photos(attachments):
    photos = []
    for attachment in attachments:
        if attachment['type'] == 'photo':
            photo = attachment['photo']
            for size in reversed(photo['sizes']):  # ищем максимальный размер фото
                if size['type'] in ('s', 'm', 'x', 'y', 'z', 'w'):
                    photos.append(InputMediaPhoto(size['url']))
                    break
    return photos


# очищает список загруженных видео для экономии места
def clr_videos():
    filelist = (Path.cwd() / 'videos').glob('*.mp4')
    for file in filelist:
        file.unlink()


# получает все видео
def get_videos(attachments):
    clr_videos()
    videos = []
    for attachment in attachments:
        if attachment['type'] == 'video':
            video = attachment['video']
            video_id = f'{video["owner_id"]}_{video["id"]}'
            video_path = Path.cwd() / 'videos' / f'{video_id}.mp4'
            ydl_opts = {'outtmpl': str(video_path)}  # настройки для загрузчика видео с вк
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:  # загрузчик видео с вк
                ydl.download([f'https://vk.com/video{video_id}'])
            videos.append(InputMediaVideo(video_path.read_bytes()))
    return videos


def listen():
    try:
        for event in longpoll.listen(): # ждем события в группе вк
            if event.type == VkBotEventType.WALL_POST_NEW:
                post = event.obj
                attachments = post.attachments
                repost = post.copy_history

                if repost:  # проверка на наличие репоста
                    repost_link = f'https://vk.com/wall{repost[0]["from_id"]}_{repost[0]["id"]}'
                else:
                    repost_link = ''

                if attachments:  # отправить сообщение с вложениями
                    # вложения по типам
                    photos = get_photos(attachments)
                    videos = get_videos(attachments)

                    media = photos + videos  # все вложения
                    if len(attachments) > 1:
                        media[-1].caption = post.text  # добавляет текст к последнему вложению
                        tgsend_mediagroup(media)
                    elif photos:  # если единственное вложение - фото(для этого случая нужен отдельный метод)
                        tgsend_photo(photos[0].media, post.text + f'\n{repost_link}')
                    elif videos:  # # если единственное вложение - видео(для этого случая нужен отдельный метод)
                        tgsend_video(videos[0].media, post.text + f'\n{repost_link}')
                elif post.text or repost_link:  # отправить простое сообщение
                    tgsend_message(f'{post.text}\n{repost_link}')
    except Exception:  # перезапуск при превышении времени ожидания события
        listen()


listen()
