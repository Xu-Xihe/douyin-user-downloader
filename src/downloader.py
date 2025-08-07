import requests
import logging
import pathlib
from src.post import post

def single_downloader(url: str, path: str, base_url: str, Cookie: str, logger: logging.Logger, orig_url: bool = False) -> bool:
    if orig_url:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
            "Referer": "https://www.douyin.com/",
            "Cookie": Cookie
        }
        r = requests.get(url, stream=True, headers=headers)
    else:
        r = requests.get(base_url + "/api/download", stream=True, params={"url": url, "prefix": "true", "with_watermark": "false"})
    if r.status_code == 200:
        with open(path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        logger.debug(f"Successfully! Downloaded {path} Link: {url}")
        return True
    else:
        logger.debug(f"Download failed! Code: {r.status_code} File: {path} Link: {url}")
        logger.debug(r.text)
        return False
    
def V_downloader(path_str: str, V: post, base_url: str, Cookie: str, logger: logging.Logger) -> list:
    error_f = []
    if V.type:
        for x in range(1,V.num+1):
            if "jpeg" in V.url[x]:
                suc = single_downloader(V.url[x], f"{path_str}_{x}.jpeg", base_url, Cookie, logger, True)
            else:
                suc = single_downloader(V.url[x], f"{path_str}_{x}.mp4", base_url, Cookie, logger, True)
            if not suc:
                error_f.append(x)

    else:
        if not single_downloader(V.url[0], path_str + ".mp4", base_url, Cookie, logger, False):
            error_f.append(0)
    return error_f # Num of failed download