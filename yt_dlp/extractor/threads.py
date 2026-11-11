import re

from .instagram import InstagramBaseIE
from ..cookies import YoutubeDLCookieJar
from ..networking import Request
from ..utils import ExtractorError, clean_html, int_or_none, parse_duration, traverse_obj


class ThreadsIE(InstagramBaseIE):
    IE_NAME = 'threads'
    _VALID_URL = r'https?://(?:www\.)?threads\.(?:com|net)/(?:@[\w.-]+/)?post/(?P<id>[\w-]+)'
    _TESTS = [{
        'url': 'https://www.threads.com/@takefumi.hayashi/post/Dflaf6hGX8u',
        'info_dict': {
            'id': 'Dflaf6hGX8u',
            'ext': 'mp4',
            'title': 'Video by takefumi.hayashi',
            'channel': 'takefumi.hayashi',
            'description': str,
            'timestamp': int,
            'upload_date': str,
            'uploader': str,
            'uploader_id': str,
            'duration': float,
            'thumbnail': r're:https?://.+',
            'like_count': int,
            'comment_count': int,
        },
        'params': {'skip_download': True},
    }, {
        'url': 'https://www.threads.net/@takefumi.hayashi/post/Dflaf6hGX8u?xmt=AQG0bfjKx2AkGbeZ3NCyRVDF',
        'only_matching': True,
    }, {
        'url': 'https://www.threads.com/post/Dflaf6hGX8u',
        'only_matching': True,
    }]

    @staticmethod
    def _find_media(obj, post_id):
        # The post is somewhere in the page's server-rendered JSON; replies are also there
        if isinstance(obj, dict):
            if obj.get('code') == post_id and any(
                    k in obj for k in ('video_versions', 'carousel_media', 'image_versions2')):
                return obj
            values = obj.values()
        elif isinstance(obj, list):
            values = obj
        else:
            return None
        for value in values:
            if (found := ThreadsIE._find_media(value, post_id)) is not None:
                return found
        return None

    def _real_extract(self, url):
        post_id = self._match_id(url)
        webpage = self._download_webpage(url, post_id)

        media = None
        for data in re.findall(r'<script type="application/json"[^>]*data-sjs>(.*?)</script>', webpage, re.S):
            if post_id not in data:
                continue
            media = self._find_media(self._parse_json(data, post_id, fatal=False), post_id)
            if media:
                break

        if not media:
            if not self._get_cookies('https://www.threads.com/').get('sessionid'):
                # Logged-out visitors get an empty page shell without the post
                self.raise_login_required('Threads needs you to be logged in', method='cookies')
            raise ExtractorError('Unable to find the post data in the page')

        info = self._extract_product(media, video_id=post_id, get_comments=False)
        if info.get('_type') != 'playlist' and not info.get('formats'):
            raise ExtractorError('This post has no video', expected=True)
        if not info.get('duration'):
            # Threads has no video_duration; the DASH manifest has the length
            info['duration'] = parse_duration(self._search_regex(
                r'mediaPresentationDuration="([^"]+)"', media.get('video_dash_manifest') or '',
                'duration', default=None))
        if info.get('comment_count') is None:
            info['comment_count'] = traverse_obj(
                media, ('text_post_app_info', 'direct_reply_count', {int_or_none}))
        info['description'] = clean_html(info.get('description'))
        info['http_headers'] = {'Referer': 'https://www.threads.com/'}
        if info.get('_type') == 'playlist':
            for entry in info['entries']:
                entry['http_headers'] = info['http_headers']
        return {
            **info,
            'webpage_url': url,
        }


class ThreadsShareIE(InstagramBaseIE):
    IE_NAME = 'threads:share'
    _VALID_URL = r'https?://(?:www\.)?threads\.(?:com|net)/share/(?P<id>[\w-]+)'
    _TESTS = [{
        'url': 'https://www.threads.com/share/BARS-fBuYX',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        share_id = self._match_id(url)
        # Resolve the share link without cookies: with a logged-in session, it may redirect
        # to the app's "barcelona://" URL, which cannot be fetched
        try:
            urlh = self._request_webpage(
                Request(url, extensions={'cookiejar': YoutubeDLCookieJar()}),
                share_id, 'Resolving share link')
        except ExtractorError as e:
            raise ExtractorError(
                f'Unable to resolve the share link; open it in a browser and use the post URL instead ({e.orig_msg})',
                expected=True)
        if not ThreadsIE.suitable(urlh.url):
            raise ExtractorError(f'The share link did not lead to a post: {urlh.url}', expected=True)
        return self.url_result(urlh.url, ThreadsIE)

