import logging
import asyncio
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
    nickname: str = ""
    sec_user_id: str = ""
    user_id: str = ""
    posts: list[post] = field(default_factory=list)

# init
API = DouyinWebCrawler()

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
    s.replace("\n", "")
    logger.debug(f"Post {s.replace(" #","#")[:5]} {data["aweme_id"]} data get. Total: {num}.")
    return post(data["aweme_id"], s.replace(" #","#"), share, data["create_time"], type, num)

def get_posts(url: str, logger: logging.Logger):
    #Get sec_user_id
    try:
        r = asyncio.run(API.get_sec_user_id(url))
    except Exception as e:
        logger.error(f"Get sec_user_id failed: {e}")
        return False
    else:
        rtn = poster(sec_user_id=r)
        logger.debug(f"Get sec_user_id success: {r}")
    
    #Get nickname
    try:
        r = asyncio.run(API.handler_user_profile(rtn.sec_user_id))
    except Exception as e:
        logger.error(f"Get user nickname failed: {e}")
        return False
    else:
        rtn.nickname = r["user"]["nickname"]
        rtn.user_id = r["user"]["signature_extra"][0]["user_id"]
        logger.debug(f"Get user {rtn.user_id} nickname {rtn.nickname} success.")

    #Get posts
    cursor, page = 0, 0
    while True:
        page += 1
        # Fetch data
        try:
            r = asyncio.run(API.fetch_user_post_videos(rtn.sec_user_id, cursor, 20))
        except Exception as e:
            logger.error(f"Get posts failed: {e}")
            return False
        else:
            logger.debug(f"Current page is {page}; cursor is {cursor}.")
        
        # If empty 
        if "aweme_list" not in r:
            logger.error(f"Requests suceess but no data in return.")
            return False
        
        # Get urls
        for P in r["aweme_list"]:
            rtn.posts.append(fetch_post_url(P, logger))
        
        #Turn page
        if r["has_more"] == 1:
            cursor = r["max_cursor"]
        else:
            logger.debug(f"Get poster {rtn.nickname} {rtn.sec_user_id} success. Total: {len(rtn.posts)}")
            return rtn