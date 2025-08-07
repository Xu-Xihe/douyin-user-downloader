import requests
import logging
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

def get_post(url: str, base_url: str, logger: logging.Logger):
    #Get sec_user_id
    r = requests.get(base_url+"/api/douyin/web/get_sec_user_id",params={"url":url})
    if r.status_code == 200:
        rtn = poster(sec_user_id=r.json()["data"])
        logger.debug(r.text)
    else:
        logger.error(f"Get sec_user_id failed! Code:{r.status_code}")
        logger.debug(r.text)
        return False
    
    #Get nickname
    r=requests.get(base_url+"/api/douyin/web/handler_user_profile",params={"sec_user_id":rtn.sec_user_id})
    if r.status_code == 200:
        rtn.nickname = r.json()["data"]["user"]["nickname"]
        rtn.user_id = r.json()["data"]["user"]["signature_extra"][0]["user_id"]
        logger.debug(f"Get user {rtn.user_id} nickname {rtn.nickname} success.")
    else:
        logger.error(f"Get user nickname failed! Code:{r.status_code}")
        logger.debug(r.text)
        return False
    
    #Get posts
    cursor, page = 0, 0
    while True:
        page += 1
        # Fetch data
        r = requests.get(base_url + "/api/douyin/web/fetch_user_post_videos", params= {"sec_user_id": rtn.sec_user_id, "max_cursor": cursor, "count": "20"})
        if r.status_code == 200:
            logger.debug(f"Current page is {page}; cursor is {cursor}.")
        else:                
            logger.error(f"Get posts failed! Code:{r.status_code}")
            logger.debug(r.text)
            return False
        
        # If empty 
        r_json = r.json()["data"]
        if "aweme_list" not in r_json:
            logger.error(f"Requests suceess but no data in return.")
            return False
        
        # Get urls
        for P in r_json["aweme_list"]:
            if "2" in str(P["media_type"]):
                type = True
            else:
                type = False
            share = []
            share.append(P["share_info"]["share_url"])
            num = 0
            if type:
                for I in P["images"]:
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
            s = P["desc"].replace("  "," ")
            post_obj = post(P["aweme_id"], s.replace(" #","#"), share, P["create_time"], type, num)
            rtn.posts.append(post_obj)
            logger.debug(f"Post {s.replace(" #","#")[:5]} {P["aweme_id"]} data get. Total: {num}")
        
        #Turn page
        if r_json["has_more"] == 1:
            cursor = r_json["max_cursor"]
        else:
            logger.debug(f"Get poster {rtn.nickname:<14} {rtn.sec_user_id} success. Total: {len(rtn.posts)}")
            return rtn