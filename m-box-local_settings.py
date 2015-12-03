#!/usr/bin/python
# -*- coding: utf-8 -*-

is_doc = False
adv_server = '10.10.65.129'
new_adv_server1 = '10.103.51.113'
new_adv_server2 = '10.103.51.108'

pid = 'XMTAyOA=='
pid_auth = 'ZThiMGNhM2M3ZDVmNTAxM2Y5ZDQxNzMyZDQzZTkxMDI='
pid_paike = 'XMjE4OA=='
aes_key = 'qwer3as2jin4fdsa'

#用于调用youku openapi
#client_id = '74c61f909cf2fcf7'
#secret = 'eb91bdf2c58977a81bf63e6870efab32'

#OTT专用
client_id = '28dfb02c6f5dffb6'
secret = 'c5ab23d98f384422598df1cd027a0c40'

game_server = 'api.gamex.mobile.youku.com'
#vvcounter_server = "yws.youku.com"
play_control_server = '10.103.88.113'
session_server = '10.103.88.155'

mf_server = 'mf.atm.youku.com'
mb_server = 'mb.atm.youku.com'
mp_server = 'mp.atm.youku.com'
mc_server = 'mc.atm.youku.com'
mi_server = 'mi.atm.youku.com'

pay_pubkey_B001 = 'B001'
pay_pubkey_C001 = 'C001'
pay_pubkey_D001 = 'D001'

#支付测试秘钥
pay_secret = '123456'

#支付线上秘钥
prod_pay_secret = 'b2bde3024d5584d843329062df0c3882'

#websocket相关秘钥
websocket_pubkey = 'YoukuTV001'
websocket_secret = '72f2a39de4bdf6c22ac548e0f77d552c'

#ykew pay相关秘钥
ykew_pay_pubkey = 'Ykew001'
ykew_pay_secret = '2oifjowfjwofijwoqfjwoqfjiwwhfowih'

#中国天气网提供的秘钥
weather_appid = 'da402ee40d130067'
weather_private_key = '9c0c2e_SmartWeatherAPI_25a99f9'

clear_cache_host = '10.103.188.23'

tv_ctype = '30'
tv_aes_key = '197d21f1722361ac'

vvcounter_server = (
                    # vip
                    '10.111.88.125',
                    '10.111.88.126',
                    '10.111.88.127',
                    '10.111.88.128',
                    #'10.103.55.129',
                    #'10.103.55.130',
                    #'10.103.55.131',
                    #'10.103.55.132',
                    # '10.103.24.61',
                    # '10.103.24.62',
                    # '10.103.24.63',
                    # '10.103.24.64',
                    # '10.103.24.65',
                    # '10.103.24.66',
                    # '10.103.24.67',
                    # '10.103.24.68'
                )

default_avatar = 'http://static.youku.com/v1.0.0769/user/img/head/150/999.jpg'
paike_share_suffix = u'(分享自：优酷拍客客户端 http://mobile.youku.com )'

is_debug = False

play_list_server = "10.102.9.111"

play_log_server = (
    '10.111.188.11',
    '10.111.188.12',
    '10.111.188.13',
    '10.111.188.14',
)

cache_servers0 = (
    "10.103.28.147:11211",
    "10.103.28.148:11211",
)

cache_servers1 = cache_servers0

cache_nutcracker = ("10.105.28.41:22120",)
cache_nutcracker_backup = ("10.105.28.41:22120",)

search_cache_servers0 = (
    "10.103.28.147:11211",
    "10.103.28.148:11211",
)

cibn_cache_servers0 = (
    "10.103.28.147:11213",
    "10.103.28.148:11213",
)

search_cache_servers1 = search_cache_servers0


statis_cache_server0 = (
    '10.103.28.141:11211',
    '10.103.28.142:11211',
    '10.103.28.143:11211',
    '10.103.28.144:11211',
)
statis_cache_server1 = search_cache_servers0


redis_servers0 = {
    'host': '10.103.13.36',
    'port': 6379,
}

redis_servers1 = {
    'host': '10.103.13.37',
    'port': 6379,
}

mongodb_config = {
    'host': 'localhost',
    'port': 27017,
    'db': 'ott_production',
    'username': 'OTT',
    'password': 'orrrorrreeww22'
}

cms_db_config = {
    'host': '10.103.88.20',
    'user': 'wireless-select',
    'passwd': '1LytXCuf3trN',
    'db': 'mos',
    'use_unicode': True,
    'charset': 'utf8'
}

redis_server = {
    'host': '10.103.28.93',
    'port': 6379,
}

thrift_server = {
    'host': '10.103.88.100',
    'port': 8774,
}

cms_server = {
    #'server': '10.103.13.11:3000',
    #'server': '10.103.88.59:3000',
    'server': '10.103.188.22:6300',
}

cms_django_server = {
    "server":"10.103.13.32:6543",
}

box_cms_server={
    'server': '10.103.188.22',
}

#观影券cms服务器
# cms_ticket_server = '10.103.14.122:7070'
cms_ticket_server = '10.103.188.22'

cms_ykew_server = '10.100.188.18'

# direct search cateId (1,2,3,5,8,9)
direct_search_cate_id = '1,2,3,5,8,9'


cms_openapi_tv_server = {
    'server': '10.100.188.18',
}

cms_tv_recomment={
    "server":"10.103.13.103:5200",
}

cms_upgrade_server = '10.103.188.22:4000'

openapi_server = '10.103.88.98'

#openapi_server2 = '10.105.88.75'
#临时切换为10.105.88.13
#openapi_server2 = '10.105.88.13'
openapi_server2 = '10.105.88.74'

#短域名q.youku.com
short_url_server = '10.105.88.12'

# m3u8播放地址使用域名
playapi_server = 'pl.youku.com'
# m3u8 play 开关
use_new_playapi_server = True

#hasadv播放接口是否打开播控
open_play_control = False

#hasadv使用getPlayList接口播控
open_playlist_control = False

#屏蔽ugc内容
shield_ugc = False

#过滤节目黑名单功能是否打开: True打开, False关闭
open_show_black_filter = True

#是否使用支付正式环境: True使用正式环境, False使用测试环境
use_prod_pay_server = True

#是否启动下线
open_offline = True

# 内部接口服务器, /etc/hosts: front.api.3g.youku.com => 211.151.146.59"
#internal_server = '10.103.88.157'
internal_server = '10.103.188.23'

v_server = ['10.103.55.105']

#云存储服务器地址,yus.navi.youku.com
yus_server = {'server':'yus.navi.youku.com' }

passport_server = [
    '10.103.88.171:8081',
    '10.103.88.172:8082',
    '10.103.88.173:8083',
    '10.103.88.174:8084',
    '10.103.88.175:8085',
    '10.103.88.176:8086',
]

# 短链接解释服务器
qr_server=["10.105.88.12"]

#restapi服务器地址，restapi.youku.com
restapi_server = "10.10.221.107:8081"

internal_pid = '127f7a5e3a366bd0'

# 缓存超时时间, 单位秒
cache_expire_S = 60
cache_expire_MS = 60 * 5
cache_expire_M = 60 * 10
cache_expire_L = 60 * 30
cache_expire_XL = 60 * 60
cache_expire_XXL = 60 * 60 * 12
cache_expire_XXXL = 60 * 60 * 24
cache_expire_MAX = 60 * 60 * 24 * 2

cache_expire_Ten_Minute = 60 * 10
cache_expire_One_Hour = 60 * 60
cache_expire_Two_Hour = 60 * 60 * 2
cache_expire_Four_Hour = 60 * 60 * 4
cache_expire_One_Day = 60 * 60 * 24 * 1
cache_expire_Two_Day = 60 * 60 * 24 * 2
cache_expire_One_Week = 60 * 60 * 24 * 7
cache_expire_One_Month =  60 * 60 * 24 * 30

video_delete_image = 'http://g3.ykimg.com/053201015367515E0A8C84685EAA0D52'
video_shield_image = 'http://g1.ykimg.com/053201015367515E0A8C84685E13EBA2'

show_fields_code = {
    'sid':'showid',
    'snam':'showname',
    'sdes':'showdesc',
    'desh':'deschead',
    'scat':'showcategory',
    'area':'area',
    'tvcat':'tv_genre',
    'ancat':'anime_genre',
    'mvcat':'mv_genre',
    'vacat':'variety_genre',
    'mocat':'movie_genre',
    'dire':'director',
    'perf':'performer',
    'host':'host',
    'stat':'station',
    'stvv':'showtotal_vv',
    'stup':'showtotal_up',
    'stdo':'showtotal_down',
    'stco':'showtotal_comment',
    'stfa':'showtotal_fav',
    'repu':'reputation',
    'rdat':'releasedate',
    'scti':'showcreatetime',
    'etot':'episode_total',
    'elas':'episode_last',
    'sturl':'show_thumburl',
    'svturl': 'show_vthumburl',
    'sburl': 'show_bannerurl',
    'fvid': 'firstepisode_videoid',
    'lvid': 'lastepisode_videoid',
    'fvti': 'firstepisode_videotitle',
    'lvti': 'lastepisode_videotitle',
    'orig': 'original',
    'voic': 'voice',
    'sing': 'singer',
    'slen': 'showlength',
    'comp': 'completed',
    'sydvr': 'showyesterday_vr',
    'pk_odshow': 'pk_odshow',
    'hasvideotype': 'hasvideotype',
    'streamtypes': 'streamtypes',
    #"showtotal_search":"showtotal_search",
    #"douban_rating":"douban_rating",
}

videos_fields_code = {
    'titl':'title',
    'img':'img',
    'imghd':'img_hd',
    'comm':'desc',
    'dura':'duration',
    'pdat':'pubdate',
    'userid':'userid',
    'user':'username',
    'pv':'total_pv',
    'tcomm':'total_comment',
    'cats':'cats',
    'tags':'tags',
    'fav':'total_fav',
    'vup':'total_up',
    'vdown':'total_down',
    'repu':'reputation',
    'vid':'videoid',
    'lim': 'limit',
    'stat': 'state',
    'ptype': 'publicType',
}

show_types = [u"电影", u"电视剧", u"综艺", u"动漫", u"音乐", u"纪录⽚", u"教育"]
category_map = {84: u'纪录片', 96: u'电影', 97: u'电视剧', 85: u'综艺', 90: u'母婴', 91: u'资讯', 98: u'体育', 104: u'汽车', 105: u'科技', 86: u'娱乐', 92: u'原创', 95: u'音乐', 99: u'游戏', 89: u'时尚', 88: u'旅游', 94: u'搞笑', 100: u'动漫', 102: u'广告', 103: u'生活',87:u'教育', 669:u'少儿', 174:u'拍客'}
CHANNEL_ART = 85
CHANNEL_EDU = 87
CHANNEL_TV = 97
CHANNEL_ANIME = 100
CHANNEL_DV = 92
CHANNEL_MUSIC = 95
CHANNEL_MOVIE = 96
CHANNEL_YULE = 86
CHANNEL_INFO = 91
CHANNEL_ALL = 1002
CHANNEL_CAR = 104
CHANNEL_DOCUME = 84
CHANNEL_SPORTS = 98


category_map_rev = dict([(y, x) for x, y in category_map.items()])

# language code
lang = [
    (0, u'default', u'默认语言'),
    (1, u'guoyu', u'国语'),
    (2, u'yue', u'粤语'),
    (3, u'chuan', u'川话'),
    (4, u'tai', u'台湾'),
    (5, u'min', u'闽南'),
    (6, u'en', u'英语'),
    (7, u'ja', u'日语'),
    (8, u'kr', u'韩语'),
    (9, u'in', u'印度'),
    (10, u'ru', u'俄语'),
    (11, u'fr', u'法语'),
    (12, u'de', u'德语'),
    (13, u'it', u'意大利语'),
    (14, u'es', u'西班牙语'),
    (15, u'th', u'泰国语'),
    (16, u'po', u'葡萄牙语'),
]
lang_zh_map = {v[1]:v[2] for v in lang }        #guoyu:国语
lang_zh_map_rev = {v[2]:v[1] for v in lang }    #国语:guoyu
lang_id_map = {v[0]:v[1] for v in lang }        #1:guoyu
lang_id_map_rev = {v[1]:v[0] for v in lang }    #guoyu:1

company_user_map = {'sony':'UNDA3NDMxNzA4'}
promote_cats_id = [801, 802, 803, 804]
#soku
source_icon = {1:u'http://res.mfs.ykimg.com/051000005029B6DB6714C043FD068F90', 2:u'http://res.mfs.ykimg.com/051000005029B6766714C043F40D7651', 3:u'http://res.mfs.ykimg.com/051000005029B6CC6714C0448B0B8C52', 6:u'http://res.mfs.ykimg.com/051000005029B6D36714C043FC05265B', 9:u'http://res.mfs.ykimg.com/051000005029B68F6714C047A607D02B', 14:u'http://res.mfs.ykimg.com/051000005029B6E16714C043FE0E5FD2', 15:u'http://res.mfs.ykimg.com/051000005029B6826714C044D4018B05', 16:u'http://res.mfs.ykimg.com/051000005029B6A26714C0448A033E1E', 17:u'http://res.mfs.ykimg.com/051000005029B6996714C047A706B102', 19:u'http://res.mfs.ykimg.com/051000005029B6C06714C067A203AA00', 27:u'http://res.mfs.ykimg.com/051000005029B6C46714C043FA024F3E', 31:u'http://res.mfs.ykimg.com/051000005029B6B96714C043F905A533'}
source_site_map = {1:u'土豆', 2:u'56网', 3:u'新浪', 4:u'琥珀', 5:u'第一视频', 6:u'搜狐', 7:u'央视', 8:u'凤凰', 9:u'激动', 10:u'酷6', 11:u'天线视频', 12:u'六间房', 13:u'中关村在', 14:u'优酷', 31:u'PPTV', 27:u'腾讯', 15:u'CNTV', 16:u'电影网', 17:u'乐视', 18:u'小银幕', 19:u'奇艺', 20:u'江苏卫视', 21:u'浙江卫视', 23:u'安徽卫视', 24:u'芒果', 25:u'爱拍游戏', 26:u'音乐台', 28:u'迅雷', 29:u'优米', 30:u'163', 31:u'pptv'}
soku_cateid = {0:u'其它', 1:u'电视剧', 2:u'电影', 3: u'综艺', 4:u'音乐', 5:u'动漫', 6:u'人物', 7:u'体育', 8:u'教育', 9:u'纪录片', 10:u'排行榜', 11:u'专辑', 12:u'html碎片'}
soku_catename = dict([(y, x) for x, y in soku_cateid.iteritems()])
guding_channel_menu = [ {'title': u"音乐", 'type': "show", 'cid': 95}, {'title': u"综艺", 'type': "show", 'cid': 85}, {'title': u"动漫", 'type': "show", 'cid': 100},
                        {'title': u"排行榜", 'type': "video", 'cid': 1001}, {'title': u"电视剧", 'type': "show", 'cid': 97}, {'title': u"电影", 'type': "show", 'cid': 96},
                        {'title': u"视频", 'type': "video", 'cid': 1002} ]

Personal_Layout_Tag = {'favorite': 1 ,'upload': 2,'follow_video':3,'history':4,'video_list':5,'followee':6,'follower':7,'fee':8}

cms_top_content_type = dict(
    (('video', '1'),
     ('show', '2'),
     ('playlist', '3')))

sign_verify = False
encrypt_data = True

# import local settings
try:
    from local_settings import *
except:
    pass

