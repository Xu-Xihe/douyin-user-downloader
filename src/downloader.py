import requests
import logging
from src.post import post

def single_downloader(url: str, path: str, Cookie: str, logger: logging.Logger) -> bool:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
        "Referer": "https://www.douyin.com/",
        "Cookie": Cookie
    }
    try:
        r = requests.get(url, stream=True, headers=headers)
        r.raise_for_status()
        with open(path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    except requests.exceptions.ChunkedEncodingError as e:
        logger.error(f"Error downloading {url}: ChunkedEncodingError {e}")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading {url}: RequestException {e}")
        return False
    except Exception as e:
        logger.error(f"Error downloading {url}: {e}")
        return False
    else:
        logger.debug(f"Successfully! Downloaded {path} Link: {url}")
        return True
    
def V_downloader(path_str: str, V: post, Cookie: str, logger: logging.Logger) -> list:
    error_f = []
    for x in range(1,V.num+1):
        if V.num > 2:
            name = f"{path_str}_{x}"
        else:
            name = path_str
        if "jpeg" in V.url[x]:
            name += ".jpeg"
        else:
            name += ".mp4"
        if not single_downloader(V.url[x], name, Cookie, logger):
            error_f.append(x)
    return error_f # Num of failed download