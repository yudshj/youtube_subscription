# <podcast:transcript>
# dir: downloads/vtt/*

import datetime
import http.cookiejar
import requests
import http
import bs4
import os
from yt_dlp import YoutubeDL
from utils import PROXY, OUTPUT_DIR, SUBSCRIBTIONS_LIST, COOKIEFILE, logger, ydl_opts, BASE_URL


def main():
    requester = requests.Session()
    requester.cookies.update(http.cookiejar.MozillaCookieJar(COOKIEFILE))
    requester.proxies.update({"http": PROXY, "https": PROXY})

    for name, feed_url in SUBSCRIBTIONS_LIST:
        download_videos(name, feed_url, requester, ydl_opts)

def save_feed(soup: bs4.BeautifulSoup, xml_path: str):
    current_date = datetime.datetime.now(datetime.timezone.utc)

    formatted_date = current_date.strftime('%a, %d %b %Y %H:%M:%S GMT')

    a = soup.find_all('lastBuildDate')

    if a:
        a[0].string = formatted_date

    with open(xml_path, 'w', encoding='utf-8') as f:
        f.write(str(soup))

def download_videos(name: str, feed_url: str, requester: requests.Session, ydl_opts: dict):
    # 构建本地XML文件路径
    xml_path = os.path.join(OUTPUT_DIR, '@' + name + '.xml')
    # 读取本地XML文件
    with open(xml_path, 'r', encoding='utf-8') as f:
        soup = bs4.BeautifulSoup(f, "xml")

    # 遍历所有item并下载视频
    items = soup.find_all("item")
    # 遍历所有RSS feed中的item（视频条目）
    for iii, item in enumerate(items):
        print('-' * 20, iii, '/', len(items), '-' * 20)

        if item.find('podcast:transcript'):
            continue
        
        # 获取视频的链接
        link = item.find("link").text
        # 记录即将下载的视频链接
        logger.info("Downloading video %s", link)
        
        # 使用yt_dlp的YoutubeDL实例来下载视频信息，并尝试下载
        with YoutubeDL(ydl_opts) as ydl:
            # info_dict = ydl.extract_info(link, download=False)
            try:
                info = ydl.extract_info(link, download=False)
                langs = ['zh-Hans', 'zh', 'en']
                ext = 'vtt'
                sub_url = None
                for lang in langs:
                    if lang not in info['subtitles']: # type: ignore
                        continue
                    for i in info['subtitles'][lang]: # type: ignore
                        if i['ext'] == ext:
                            sub_url = i['url']
                            break
                assert sub_url is not None
                # download vtt to downloads/vtt/NAME/ID.vtt
                sub_path = os.path.join(OUTPUT_DIR, 'vtt', name)
                if not os.path.exists(sub_path):
                    os.makedirs(sub_path)
                sub_filename = info['id'] + '.' + ext # type: ignore
                sub_path = os.path.join(sub_path, sub_filename)
                with open(sub_path, 'wb', encoding='utf-8') as f:
                    f.write(requester.get(sub_url).content)
                xml_sub_url = BASE_URL + '/vtt/' + name + '/' + sub_filename
                _tag = soup.new_tag('podcast:transcript', url=xml_sub_url, type='text/vtt', rel="captions")
                item.append(_tag)
                save_feed(soup, xml_path)
            except KeyboardInterrupt as e:
                raise e
            except:
                continue

if __name__ == "__main__":
    main()
