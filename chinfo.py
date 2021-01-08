import sys
import json
import time
import requests
import numpy as np
from bs4 import BeautifulSoup as bs
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager

from utils import *


YOUTUBE_QUERY_URL = 'https://www.youtube.com/results?search_query={channel}'
YOUTUBE_CHANNEL_URL = 'https://www.youtube.com/channel/{channel_id}/videos'
YOUTUBE_AJAX_URL = 'https://www.youtube.com/browse_ajax'

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'

if sys.platform == 'darwin':
    DRIVER = './driver/chromedriver'
elif sys.platform == 'linux':
    DRIVER = ChromeDriverManager()
elif sys.platform == 'win32':
    DRIVER = './driver/chromedriver.exe'


def get_channel_id(name):
    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(
        DRIVER, chrome_options=options)
    try:
        driver.get(YOUTUBE_QUERY_URL.format(channel=name))
        time.sleep(5)
        source = driver.page_source
        soup = bs(source, 'lxml')
        result = soup.find(
            'a', class_='channel-link yt-simple-endpoint style-scope ytd-channel-renderer')
        id = result.get('href').split('/')[2]
    except AttributeError:
        id = np.nan
    return id


def get_channel_videos(channel_id):
    session = requests.Session()
    session.headers['User-Agent'] = USER_AGENT

    response = session.get(YOUTUBE_CHANNEL_URL.format(channel_id=channel_id))
    html = response.text
    session_token = find_value(html, 'XSRF_TOKEN', 3)
    session_token = bytes(session_token, 'ascii').decode('unicode-escape')

    data = json.loads(find_value(html, 'var ytInitialData = ', 0, '};') + '}')
    for renderer in search_dict(data, 'itemSectionRenderer'):
        ncd = next(search_dict(renderer, 'nextContinuationData'), None)
        if not ncd:
            break
    continuations = [(ncd['continuation'], ncd['clickTrackingParams'])]

    while continuations:
        continuation, itct = continuations.pop()
        response = ajax_request(session, YOUTUBE_AJAX_URL,
                                params={'ctoken': continuation,
                                        'continuation': continuation,
                                        'itct': itct},
                                data={'session_token': session_token},
                                headers={'X-YouTube-Client-Name': '1',
                                         'X-YouTube-Client-Version': '2.20201202.06.01'})
        time.sleep(1)
        if not response:
            break
        if list(search_dict(response, 'externalErrorMessage')):
            raise RuntimeError('Error returned from server: ' +
                               next(search_dict(response, 'externalErrorMessage')))

        # Ordering matters. The newest continuations should go first.
        continuations = [(ncd['continuation'], ncd['clickTrackingParams'])
                         for ncd in search_dict(response, 'nextContinuationData')] + continuations

        for video in search_dict(response, 'gridVideoRenderer'):
            yield {'id': video['videoId'],
                   'time': video['publishedTimeText']['simpleText'],
                   'title': video['title']['runs'][0]['text'],
                   'view': video['viewCountText']['simpleText']}
        time.sleep(1)


# def get_channel_tracker(channel_id):
#     session = requests.Session()
#     session.headers['User-Agent'] = USER_AGENT

#     response = session.get(YOUTUBE_CHANNEL_URL.format(channel_id=channel_id))
#     html = response.text
#     session_token = find_value(html, 'XSRF_TOKEN', 3)
#     session_token = bytes(session_token, 'ascii').decode('unicode-escape')

#     data = json.loads(find_value(html, 'var ytInitialData = ', 0, '};') + '}')
#     for renderer in search_dict(data, 'itemSectionRenderer'):
#         ncd = next(search_dict(renderer, 'nextContinuationData'), None)
#         if not ncd:
#             break
#     continuations = [(ncd['continuation'], ncd['clickTrackingParams'])]
#     return continuations

# def get_channel_videos(track):
#     continuations = track

#     while continuations:
#         continuation, itct = continuations.pop()
#         response = ajax_request(session, YOUTUBE_AJAX_URL,
#                                 params={'ctoken': continuation,
#                                         'continuation': continuation,
#                                         'itct': itct},
#                                 data={'session_token': session_token},
#                                 headers={'X-YouTube-Client-Name': '1',
#                                          'X-YouTube-Client-Version': '2.20201202.06.01'})
#         time.sleep(1)
#         if not response:
#             break
#         if list(search_dict(response, 'externalErrorMessage')):
#             raise RuntimeError('Error returned from server: ' +
#                                next(search_dict(response, 'externalErrorMessage')))

#         # Ordering matters. The newest continuations should go first.
#         continuations = [(ncd['continuation'], ncd['clickTrackingParams'])
#                          for ncd in search_dict(response, 'nextContinuationData')] + continuations

#         for video in search_dict(response, 'gridVideoRenderer'):
#             yield {'id': video['videoId'],
#                    'time': video['publishedTimeText']['simpleText'],
#                    'title': video['title']['runs'][0]['text'],
#                    'view': video['viewCountText']['simpleText']}
#         time.sleep(1)


# def get_channel_videos_(channel_id):
#     options = webdriver.ChromeOptions()
#     options.add_argument('headless')
#     options.add_argument('--no-sandbox')
#     driver = webdriver.Chrome(DRIVER, chrome_options=options)

#     driver.get(YOUTUBE_CHANNEL_URL.format(channel_id=channel_id))
#     time.sleep(5)
#     source = driver.page_source
#     soup = bs(source, 'html')
#     link_ = []
#     for result in soup.find_all('a', class_='yt-simple-endpoint inline-block style-scope ytd-thumbnail'):
#         link = result.get('href')
#         link_.append(link)

#     link_.remove(None)
#     id = []
#     for l in link_:
#         l = l.split('=')[1]
#         id.append(l)
#     del link_
#     return id
