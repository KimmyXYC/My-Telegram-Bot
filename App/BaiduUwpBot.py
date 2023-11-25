# -*- coding: utf-8 -*-
# @Time: 2023/11/25 18:46 
# @FileName: BaiduUwpBot.py
# @Software: PyCharm
# @GitHub: KimmyXYC
import asyncio
import concurrent.futures
import contextlib
import datetime
import hashlib
from loguru import logger
import math
import os
import re
import httpx
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from dataclasses import dataclass
from typing import List, Tuple


class SrcData:
    def __init__(self, src_data):
        self.isactive = src_data.get('isactive', 0)
        self.fullsrc = src_data.get('fullsrc', '')
        self.dirname = src_data.get('dirname', '')


class DirData:
    def __init__(self, dirdata):
        self.src: List[SrcData] = [SrcData(src) for src in dirdata.get('src', [])]
        self.timestamp = dirdata.get('timestamp', '')
        self.sign = dirdata.get('sign', '')
        self.randsk = dirdata.get('randsk', '')
        self.shareid = dirdata.get('shareid', '')
        self.surl = dirdata.get('surl', '')
        self.pwd = dirdata.get('pwd', '')
        self.uk = dirdata.get('uk', '')


class FileData:
    def __init__(self, filedata):
        self.isdir = filedata.get('isdir', 0)
        self.name = filedata.get('name', '')
        self.fs_id = filedata.get('fs_id', '')
        self.path = filedata.get('path', '')
        self.size = filedata.get('size', 0)
        self.uploadtime = filedata.get('uploadtime', 0)
        self.dlink = filedata.get('dlink', '')


class ParseList:
    def __init__(self, response_data):
        self.error = response_data.get('error', None)
        self.isroot = response_data.get('isroot', False)
        self.dirdata: DirData = DirData(response_data.get('dirdata', {}))
        self.filenum = response_data.get('filenum', 0)
        self.filedata: List[FileData] = [FileData(file) for file in response_data.get('filedata', [])]
        self.error_msg = response_data['msg'] if self.error else ''

    @staticmethod
    def parse_dirdata(dirdata):
        return {
            'src': dirdata.get('src', []),
            'timestamp': dirdata.get('timestamp', ''),
            'sign': dirdata.get('sign', ''),
            'randsk': dirdata.get('randsk', ''),
            'shareid': dirdata.get('shareid', ''),
            'surl': dirdata.get('surl', ''),
            'pwd': dirdata.get('pwd', ''),
            'uk': dirdata.get('uk', '')
        }

    @staticmethod
    def parse_filedata(filedata_list):
        return [
            {
                'isdir': filedata.get('isdir', 0),
                'name': filedata.get('name', ''),
                'fs_id': filedata.get('fs_id', ''),
                'path': filedata.get('path', ''),
                'size': filedata.get('size', 0),
                'uploadtime': filedata.get('uploadtime', 0),
                'dlink': filedata.get('dlink', ''),
            }
            for filedata in filedata_list
        ]


class BaiduUwp:
    def __init__(self, config):
        self.chat_data = {}
        self.formats = {
            ".txt": "📄", ".docx": "📝", ".pdf": "📑", ".xlsx": "📊", ".pptx": "📑", ".jpg": "🖼️", ".png": "🖼️",
            ".mp3": "🎵", ".mp4": "🎥", ".flv": "🎥", ".avi": "🎥", ".wmv": "🎥", ".mov": "🎥", ".webm": "🎥",
            ".mkv": "🎥", ".zip": "📦", ".rar": "📦", ".7z": "📦", ".tar": "📦", ".gz": "📦", ".bz2": "📦", ".xz": "📦",
            ".tar.gz": "📦", ".tar.bz2": "📦", ".tar.xz": "📦", ".zipx": "📦", ".cab": "📦", ".iso": "📦", ".jar": "📦"
        }
        self.config = config

    async def start(self, bot, message):
        if message.reply_to_message is not None:
            parameter = message.reply_to_message.text
        else:
            parameter = ' '.join(message.text.split()[1:])
        baidu = Baidu(self.config)

        if not parameter:
            system = await baidu.system_text()
            text = f"""
{system}
请加上分享链接，链接格式随意，例：
`/bd 链接: https://pan.baidu.com/s/1uY-UL9KN9cwKiTX5TzIEuw?pwd=jwdp 提取码: jwdp 复制这段内容后打开百度网盘手机App，操作更方便哦`
            """
            return await bot.reply_to(message, text, parse_mode='Markdown', disable_web_page_preview=True)
        msg = await bot.reply_to(message, '解析中...')
        mid = f'{message.from_user.id}_{msg.id}'

        def extract_link_and_password(_text: str) -> Tuple[str, str]:
            formatted_links = re.search(r'(?:/s/|surl=)([\w-]+)', _text)[1]
            formatted_links = formatted_links if formatted_links.startswith('1') else f'1{formatted_links}'
            password_pattern = r"(?<=\bpwd=)[a-zA-Z0-9]+|[^/](\b[a-zA-Z0-9]{4}\b(?!\.))(?<!link)(?<!https)(?<!surl)"
            passwords = re.search(password_pattern, _text.replace(formatted_links, ''))
            password = passwords[1] if passwords else None
            return formatted_links, password

        try:
            surl, pwd = extract_link_and_password(parameter)
            root_list = await baidu.parse_list(surl, pwd)
            if root_list.error:
                return await bot.edit_message_text(root_list.error_msg, msg.chat.id, msg.message_id)
            self.chat_data[f'bd_rlist_{mid}'] = root_list
            self.chat_data[f'bd_rlist_{mid}_root'] = root_list

            text, button = self.build_menu(root_list)
            await bot.edit_message_text(text, msg.chat.id, msg.message_id, reply_markup=InlineKeyboardMarkup(button))
        except Exception as e:
            await bot.edit_message_text(f'错误：{e}', msg.chat.id, msg.message_id)

    async def baidu_list(self, bot, query):
        mid = f'{query.from_user.id}_{query.message.id}'
        rlist: ParseList = self.chat_data.get(f'bd_rlist_{mid}')
        if not rlist:
            return await bot.answer_callback_query(query.id, text="这不是你的解析结果哦", show_alert=True)
        baidu = Baidu(self.config, rlist)

        num = query.data.split('_')[1]
        surl = rlist.dirdata.surl
        pwd = rlist.dirdata.pwd

        _dir = None
        if query.data == 'bd_rt':
            if len(rlist.dirdata.src) == 1:
                dir_list = self.chat_data.get(f'bd_rlist_{mid}_root') or await baidu.parse_list(surl=surl, pwd=pwd)
            elif len(rlist.dirdata.src) == 0:
                await bot.answer_callback_query(query.id, text="没有上一层了哟~", show_alert=True)
                return
            else:
                _dir = rlist.dirdata.src[-2].fullsrc
                dir_list = self.chat_data.get(f'bd_rlist_{mid}_{md5_hash(_dir)}') or await baidu.parse_list(dir_=_dir)
        elif query.data == 'bd_dl_rt':
            if rlist.dirdata.src:
                _dir = rlist.dirdata.src[-1].fullsrc
                dir_list = self.chat_data.get(f'bd_rlist_{mid}_{md5_hash(_dir)}') or await baidu.parse_list(dir_=_dir)
            else:
                dir_list = self.chat_data.get(f'bd_rlist_{mid}_root') or await baidu.parse_list(surl=surl, pwd=pwd)
        else:
            _dir = rlist.filedata[int(num)].path
            dir_list = self.chat_data.get(f'bd_rlist_{mid}_{md5_hash(_dir)}') or await baidu.parse_list(dir_=_dir)
        if _dir:
            self.chat_data[f'bd_rlist_{mid}_{md5_hash(_dir)}'] = dir_list
        self.chat_data[f'bd_rlist_{mid}'] = dir_list

        text, button = self.build_menu(dir_list)
        await bot.edit_message_text(
            text,
            query.message.chat.id,
            query.message.message_id,
            reply_markup=InlineKeyboardMarkup(button)
        )
        await self.preloading(rlist, dir_list, mid)

    async def baidu_file(self, bot, query):
        mid = f'{query.from_user.id}_{query.message.id}'
        rlist: ParseList = self.chat_data.get(f'bd_rlist_{mid}')
        if not rlist:
            return await bot.answer_callback_query(query.id, text="这不是你的解析结果哦", show_alert=True)
        num = query.data.split('_')[1]
        fs_id = rlist.filedata[int(num)].fs_id

        baidu = Baidu(self.config, rlist)
        dir_list = await baidu.get_dlurl(fs_id=fs_id)
        text = f"""
        路径：`{dir_list.path}`

        文件名称：`{dir_list.file_name}`
        文件大小：`{dir_list.file_size}`
        MD5：`{dir_list.md5}`
        上传时间：`{dir_list.upload_time}`
        User-Agent：`{dir_list.user_agent}`

        **>>>[点击查看下载教程](https://telegra.ph/%E4%B8%8B%E8%BD%BD%E6%8F%90%E7%A4%BA-07-13)<<<**
        """
        button = [
            [
                InlineKeyboardButton('💾下载文件', url=dir_list.directlink),
                InlineKeyboardButton('📖查看下载教程',
                                     url='https://telegra.ph/%E4%B8%8B%E8%BD%BD%E6%8F%90%E7%A4%BA-07-13')
            ],
            [
                InlineKeyboardButton("🔙返回上级", callback_data='bd_dl_rt'),
                InlineKeyboardButton('❌关闭菜单', callback_data='bdexit')
            ]
        ]
        await bot.edit_message_text(
            text,
            query.message.chat.id,
            query.message.message_id,
            reply_markup=InlineKeyboardMarkup(button),
            parse_mode='Markdown',
            disable_web_page_preview=True
        )

    async def baidu_all_dl(self, bot, query):
        mid = f'{query.from_user.id}_{query.message.id}'
        rlist: ParseList = self.chat_data.get(f'bd_rlist_{mid}')
        if not rlist:
            return await bot.answer_callback_query(query.id, text="这不是你的解析结果哦", show_alert=True)
        baidu = Baidu(self.config, rlist)
        fetch_failed = []

        async def add_dl(v):
            try:
                fs_id = v.fs_id
                dir_list = await baidu.get_dlurl(fs_id=fs_id)
                return dir_list.file_name, dir_list.directlink
            except Exception as ee:
                logger.error(ee)
                fetch_failed.append(v.name)

        dirname = rlist.dirdata.src[-1].dirname if rlist.dirdata.src else '根目录'
        await bot.edit_message_text(f'{dirname}|获取中...', query.message.chat.id, query.message.message_id)
        a = [v for v in rlist.filedata if not v.isdir]
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(asyncio.run, add_dl(v)) for v in a]
        results = [future.result() for future in concurrent.futures.wait(futures).done]

        button = [
            [
                InlineKeyboardButton('📖查看下载教程',
                                     url='https://telegra.ph/%E4%B8%8B%E8%BD%BD%E6%8F%90%E7%A4%BA-07-13')
            ],
            [
                InlineKeyboardButton("🔙返回上级", callback_data='bd_dl_rt'),
                InlineKeyboardButton('❌关闭菜单', callback_data='bdexit')
            ]
        ]
        t = [f"➡️{v[0]}\n{v[1]}" for v in results if v]
        u = '\n'.join([n[1] for n in results if n])
        text = f'\n\n{("=" * 40)}\n\n'.join(t)
        text = f"""路径：{rlist.dirdata.src[-1].fullsrc if rlist.dirdata.src else '根目录'}
        上部分为单个链接
        下部分为全部链接

        {text}
        \n\n\n
        {('*' * 100)}
        全部链接：
        {('*' * 100)}

        {u}

        """
        if not os.path.exists('downloads'):
            os.mkdir('downloads')
        path = f"downloads/{dirname}.txt"
        with open(path, 'w', encoding='utf-8') as f:
            f.write(text)
        e = '\n'.join(fetch_failed)
        msg: Message = await bot.send_document(
            query.message.chat.id,
            document=path,
            reply_markup=InlineKeyboardMarkup(button),
            caption=f"**获取失败：**\n{e}" if fetch_failed else ''
        )
        await query.message.delete()
        self.chat_data[f'bd_rlist_{query.from_user.id}_{msg.id}'] = self.chat_data[f'bd_rlist_{mid}']
        self.chat_data.pop(f'bd_rlist_{mid}')
        os.remove(path)

    async def baidu_exit(self, bot, query):
        mid = f'{query.from_user.id}_{query.message.id}'
        if self.chat_data.get(f'bd_rlist_{mid}'):
            await bot.edit_message_text('已退出『百度解析』', query.message.chat.id, query.message.message_id)
        else:
            return await bot.answer_callback_query(query.id, text="这不是你的解析结果哦", show_alert=True)

    def build_menu(self, root_list: ParseList):
        text = f"""目录：{f"`{root_list.dirdata.src[-1].fullsrc}`" if root_list.dirdata.src else '`/`'}
    数量：{root_list.filenum}
    """
        button = [
            [InlineKeyboardButton(
                text=f"{i + 1}.{'📁' if v.isdir else self.formats.get(os.path.splitext(v.name)[1], '📄')}{v.name}",
                callback_data=f'bd_{i}' if v.isdir else f"bdf_{i}"
            )] for i, v in enumerate(root_list.filedata)
        ]
        but = [InlineKeyboardButton(
            text='🔙返回上级',
            callback_data='bd_rt'
        ), InlineKeyboardButton(
            text='❌关闭菜单',
            callback_data='bdexit'
        )]
        but_1 = [InlineKeyboardButton(
            text='🌐获取本页所有文件下载链接',
            callback_data='bdAll_dl'
        ), ]
        if [v for v in root_list.filedata if not v.isdir]:
            button.insert(0, but_1)
            if root_list.filedata[7:]:
                button.append(but_1)

        button.insert(0, but)
        if root_list.filedata[7:]:
            button.append(but)

        return text, button

    async def preloading(self, rlist, dir_list: ParseList, mid):
        baidu = Baidu(self.config, rlist)

        async def load(dir_):
            try:
                dir_list = await baidu.parse_list(dir_=dir_)
                self.chat_data[f'bd_rlist_{mid}_{md5_hash(dir_)}'] = dir_list
            except Exception as ee:
                logger.error(ee)

        d_l = [i.path for i in dir_list.filedata if i.isdir and not self.chat_data.get(f'bd_rlist_{mid}_{md5_hash(i.path)}')]
        if not d_l[20:]:
            with concurrent.futures.ThreadPoolExecutor(max_workers=7) as executor:
                futures = [executor.submit(asyncio.run, load(v)) for v in d_l]
            [future.result() for future in concurrent.futures.wait(futures).done]


def pybyte(size, dot=2):
    size = float(size)
    if 0 <= size < 1:
        human_size = f'{str(round(size / 0.125, dot))}b'
    elif 1 <= size < 1024:
        human_size = f'{str(round(size, dot))}B'
    elif math.pow(1024, 1) <= size < math.pow(1024, 2):
        human_size = f'{str(round(size / math.pow(1024, 1), dot))}KB'
    elif math.pow(1024, 2) <= size < math.pow(1024, 3):
        human_size = f'{str(round(size / math.pow(1024, 2), dot))}MB'
    elif math.pow(1024, 3) <= size < math.pow(1024, 4):
        human_size = f'{str(round(size / math.pow(1024, 3), dot))}GB'
    elif math.pow(1024, 4) <= size < math.pow(1024, 5):
        human_size = f'{str(round(size / math.pow(1024, 4), dot))}TB'
    else:
        raise ValueError(
            f'{pybyte.__name__}() takes number than or equal to 0, but less than 0 given.'
        )
    return human_size


def md5_hash(input_string: str) -> str:
    md5_hash_object = hashlib.md5()
    md5_hash_object.update(input_string.encode('utf-8'))
    return md5_hash_object.hexdigest()


def retry(max_retries=3):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            for _ in range(max_retries):
                with contextlib.suppress(Exception):
                    return await func(*args, **kwargs)
                await asyncio.sleep(1)
            raise Exception('连接超时')

        return wrapper

    return decorator


@dataclass
class System:
    last_time: str
    limit: bool
    today_times: int
    today_flow: str
    all_times: int
    all_flow: str


@dataclass
class B:
    timestamp: str = None
    sign: str = None
    randsk: str = None
    shareid: str = None
    surl: str = None
    pwd: str = None
    uk: str = None


class DlUrl:
    def __init__(self, result):
        self.result = result
        self.path: str = self.result['filedata']['path']
        self.file_name: str = self.result['filedata']['filename']
        self.file_size: str = pybyte(self.result['filedata']['size'])
        self.md5: str = self.result['filedata']['md5']
        self.upload_time: datetime = datetime.datetime.fromtimestamp(int(self.result['filedata']['uploadtime']))
        self.user_agent: str = self.result['user_agent']
        self.directlink: str = self.result['directlink']


class Baidu:
    def __init__(self, config, page_results: ParseList = None):
        self.B = B()
        self.config = config
        if page_results:
            dirdata = page_results.dirdata
            self.B = B(dirdata.timestamp,
                       dirdata.sign,
                       dirdata.randsk,
                       dirdata.shareid,
                       dirdata.surl,
                       dirdata.pwd,
                       dirdata.uk
                       )

    @retry()
    async def parse_count(self) -> str:
        async with httpx.AsyncClient() as client:
            result = await client.get(f'{self.config.baidu_url}/api.php?m=ParseCount')
            result = result.json()['msg'].replace('<br />', '\n')
            return result

    @retry()
    async def last_parse(self) -> str:
        async with httpx.AsyncClient() as client:
            result = await client.get(f'{self.config.baidu_url}/api.php?m=LastParse')
            result = result.json()['msg'].replace('<br />', '\n')
            return result

    @retry()
    async def get_system(self) -> System:
        async with httpx.AsyncClient() as client:
            result = await client.get(f'{self.config.baidu_url}/system')
            result = result.json()

        return System(result['account']['last_time'], result['account']['limit'],
                      result['count']['today']['times'], result['count']['today']['flow'],
                      result['count']['all']['times'], result['count']['all']['flow'],
                      )

    async def system_text(self):
        if self.config.baidu_version == '3':
            parse_count = await self.parse_count()
            last_parse = await self.last_parse()
            return f"""
{parse_count}

{last_parse}
"""
        else:
            system = await self.get_system()
            return f"""
系统使用统计
累计解析: {system.all_times} ({pybyte(system.all_flow)})
今日解析: {system.today_times} ({pybyte(system.today_flow)})

SVIP账号状态
上次解析: {system.last_time}
账号状态: {'限速' if system.limit else '正常'}
"""

    @retry()
    async def get_root_list(
            self,
            surl: str,
            pwd: str,
    ) -> ParseList:
        """

        :param surl:
        :param pwd:
        :return:
        """
        data = {
            'surl': surl,
            'pwd': pwd,
            'password': self.config.baidu_password,
        }

        async with httpx.AsyncClient() as client:
            result = await client.post(f'{self.config.baidu_url}/api.php?m=GetList', data=data)
        return ParseList(result.json())

    @retry()
    async def get_list(
            self,
            surl: str = None,
            pwd: str = None,
            dir_: str = None,

    ) -> ParseList:
        """

        :param surl:
        :param pwd:
        :param dir_:
        :return:
        """

        data = {
            'dir': dir_,
            'timestamp': self.B.timestamp,
            'sign': self.B.sign,
            'randsk': self.B.randsk,
            'shareid': self.B.shareid,
            'surl': surl or self.B.surl,
            'pwd': pwd or self.B.pwd,
            'uk': self.B.uk,
            'password': self.config.baidu_password,
        }
        async with httpx.AsyncClient() as client:
            api = '/api.php?m=GetList' if self.config.baidu_version == '3' else '/parse/list'
            result = await client.post(f'{self.config.baidu_url}{api}', data=data)
            result = ParseList(result.json())
            if dir_:
                result.filedata = sorted(sorted(result.filedata, key=lambda x: x.name),
                                         key=lambda x: x.isdir,
                                         reverse=True)
            return result

    async def parse_list(self, surl: str = None, pwd: str = None, dir_: str = None) -> ParseList:
        """
        :param surl:
        :param pwd:
        :param dir_:
        :return:
        """
        return await self.get_root_list(surl, pwd) if self.config.baidu_version == '3' else await self.get_list(surl, pwd, dir_)

    @retry()
    async def get_dlurl(
            self,
            fs_id: str
    ) -> DlUrl:
        """

        :param fs_id:
        :return:
        """
        data = {
            'fs_id': fs_id,
            'timestamp': self.B.timestamp,
            'sign': self.B.sign,
            'randsk': self.B.randsk,
            'shareid': self.B.shareid,
            'surl': self.B.surl,
            'pwd': self.B.pwd,
            'uk': self.B.uk,
            'password': self.config.baidu_password,
        }
        async with httpx.AsyncClient() as client:
            api = '/api.php?m=Download' if self.config.baidu_version == '3' else '/parse/link'
            result = await client.post(f'{self.config.baidu_url}{api}', data=data)
            return DlUrl(result.json())
