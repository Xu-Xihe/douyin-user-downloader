import logging
import asyncio
import time
import sys
from API.crawlers.douyin.web.web_crawler import DouyinWebCrawler
from dataclasses import dataclass, field

@dataclass
class post:
    aweme_id: str
    desc: str
    url: list[str]
    date: int
    type: bool
    num: int

@dataclass
class poster:
    nickname: str
    sec_user_id: str
    user_id: str
    avatar: str
    cover: str
    ip: str
    signature: str
    gender: int
    unique_id: str
    age: int
    country: str
    province: str
    city: str
    school: str
    posts: list[post] = field(default_factory=list)

# init
API = DouyinWebCrawler()
last = time.time()

def fetch_post_url(data: dict, logger: logging.Logger) -> post:
    if "2" in str(data["media_type"]):
        type = True
    else:
        type = False
    share = []
    share.append(data["share_info"]["share_url"])
    num = 0
    if type:
        for I in data["images"]:
            num+=1
            if "video" in I:
                for url in I["video"]["play_addr"]["url_list"]:
                    if "douyin.com" in url:
                        share.append(url)
                        break
            else:
                for url in I["url_list"]:
                    if "jpeg" in url:
                        share.append(url)
                        break
    else:
        num+=1
        for url in data["video"]["bit_rate"][0]["play_addr"]["url_list"]:
            if "douyin.com" in url:
                share.append(url)
                break
    s = data["desc"].replace("  "," ")
    s = s.replace("\n", "")
    s = s.replace(" #", "#")
    s = s.replace("/", "_")
    logger.debug(f"Post {s[:5]} {data["aweme_id"]} data get. Total: {num}.")
    return post(data["aweme_id"], s, share, data["create_time"], type, num)

def fetch_user_profile(url: str, logger: logging.Logger) -> poster:
    global last
    #Get sec_user_id
    try:
        sec_user_id = asyncio.run(API.get_sec_user_id(url))
    except Exception as e:
        logger.error(f"Get sec_user_id failed: {e}")
        return False
    else:
        logger.debug(f"Get sec_user_id success: {sec_user_id}")

    #Get details
    try:
        if not time.time() - last > 1:
            time.sleep(1)
        last = time.time()
        r = asyncio.run(API.handler_user_profile(sec_user_id))
    except Exception as e:
        logger.error(f"Get user nickname failed: {e}")
        return False
    else:
        data = r["user"]
        rtn = poster(nickname       = data["nickname"],
                     sec_user_id    = sec_user_id,
                     user_id        = data["uid"],
                     avatar         = data["avatar_300x300"]["url_list"][0],
                     cover          = data["cover_url"][0]["url_list"][0],
                     ip             = data["ip_location"] if "ip_location" in data else "",
                     signature      = data["signature"],
                     gender         = data["gender"],
                     unique_id      = data["unique_id"],
                     age            = data["user_age"],
                     country        = data["country"],
                     province       = data["province"],
                     city           = data["city"],
                     school         = data["school_name"])
        logger.debug(f"Get user {rtn.user_id} nickname {rtn.nickname} success.")
        return rtn

def get_posts(url: str, logger: logging.Logger) -> poster:
    global last
    rtn = fetch_user_profile(url, logger)

    #Get posts
    cursor, page = 0, 0
    while True:
        page += 1
        # Fetch data
        got = False
        for i in range(6):
            try:
                if not time.time() - last > 1:
                    time.sleep(1)
                last = time.time()
                r = asyncio.run(API.fetch_user_post_videos(rtn.sec_user_id, cursor, 20))
            except Exception as e:
                logger.error(f"Get posts failed (retry {i}): {e}")
            else:
                logger.debug(f"Current page is {page}; cursor is {cursor}.")
            # If empty 
            if "aweme_list" not in r:
                logger.error(f"Requests suceess but no data in return. Retry {i}.")
            else:
                got = True
            if got:
                break
            else:
                time.sleep(4*2**i)
        if not got:
            logger.error(f"Get posts failed: {rtn.sec_user_id}")
            sys.exit(1)
        
        # Get urls
        for P in r["aweme_list"]:
            rtn.posts.append(fetch_post_url(P, logger))
        
        #Turn page
        if r["has_more"] == 1:
            cursor = r["max_cursor"]
        else:
            logger.debug(f"Get poster {rtn.nickname} {rtn.sec_user_id} success. Total: {len(rtn.posts)}")
            return rtn
        
def get_single_post(url: str, logger: logging.Logger) -> post:
    if "http" in url:
        aweme_id = asyncio.run(API.get_aweme_id(url))
    elif not url.isdigit():
        logger.error("Input error!")
    else:
        aweme_id = url
    logger.debug(f"Input aweme_id: {aweme_id}")
    try:
        data = asyncio.run(API.fetch_one_video(aweme_id))
    except Exception as e:
        logger.error(f"Get single post failed: {aweme_id} : {e}")
        return False
    else:
        logger.debug(f"Get single post success: {aweme_id}")
        return fetch_post_url(data["aweme_detail"], logger)