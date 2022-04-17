from pathlib import Path
import telebot
from telebot.types import InputMediaPhoto, InputMediaVideo
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
import yt_dlp


# tgbot
tgtoken = ""  # вписать token tg бота
tggroupid =  # вписать id группы(кавычки не пропущены, они не нужны)
tgbot = telebot.TeleBot(tgtoken, parse_mode='HTML')


# vkbot
vktoken = ""  # вписать token vk бота
vkgroupid = ""  # вписать id группы
vksession = vk_api.VkApi(token=vktoken)
longpoll = VkBotLongPoll(vksession, vkgroupid)


# получить ссылку на репостнутый пост
def get_repost(post):
    repost = post.copy_history
    if repost:
        return f'Ответ на: https://vk.com/wall{repost[0]["from_id"]}_{repost[0]["id"]}'
    return ''


# получить все прикрепленные ссылки
def get_links(attachments):
    links = ''
    for attachment in attachments:
        if attachment['type'] == 'link':
            link = attachment['link']
            links += f'{link["url"]}\n'
    return links


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
    filelist = (Path.cwd() / 'videos').glob('*.*')
    for file in filelist:
        file.unlink()


# получает все видео
def get_videos(attachments):
    clr_videos()
    for attachment in attachments:
        if attachment['type'] == 'video':
            video = attachment['video']
            video_id = f'{video["owner_id"]}_{video["id"]}'
            video_path = Path.cwd() / 'videos'
            # настройки для загрузчика видео
            ydl_opts = {'outtmpl': f'{str(video_path)}/{video_id}.%(ext)s'}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # загрузчик видео
                ydl.download([f'https://vk.com/video{video_id}'])
    videos = [InputMediaVideo(path.read_bytes()) for path in (Path.cwd() / 'videos').glob('*.*')]
    return videos


def listen():
    try:
        for event in longpoll.listen():  # ждем события в группе вк
            if event.type == VkBotEventType.WALL_POST_NEW:
                post = event.obj
                attachments = post.attachments
                repost = get_repost(post)
                message = f'{repost}\n\n{post.text}'

                if attachments:  # отправить сообщение с вложениями
                    # вложения по типам
                    photos = get_photos(attachments)
                    videos = get_videos(attachments)
                    links = get_links(attachments)

                    photo_video = photos + videos  # фото и видео
                    message = f'{message}\n\n{links}'
                    if len(photo_video) > 1:
                        photo_video[0].caption = message  # добавляет текст к первому фото/видео
                        tgbot.send_media_group(tggroupid, photo_video)
                    elif photos:  # если единственное вложение - фото(для этого случая нужен отдельный метод)
                        tgbot.send_photo(tggroupid, photos[0].media, caption=message)
                    elif videos:  # если единственное вложение - видео(для этого случая нужен отдельный метод)
                        tgbot.send_video(tggroupid, videos[0].media, caption=message)
                    elif links:  # если единственное вложение - прикрепленная ссылка(например, статья)
                        tgbot.send_message(tggroupid, message)
                elif post.text or repost:  # отправить простое сообщение
                    tgbot.send_message(tggroupid, message)
    except Exception:
        listen()


listen()
