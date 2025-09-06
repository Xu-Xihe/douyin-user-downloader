import requests
import logging
import datetime
import pathlib
import sys
import rich.progress as pgs
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from src.progress import pg
from src.post import post
from src.align_unicode import align_unicode

# Generate single post download path and name
def mkdir_download_path(post_info: post, path_str: str, separate_limit: int, data_format: str, desc_length: int, logger:logging.Logger):
    #Post time & name
    post_date = datetime.datetime.fromtimestamp(post_info.date)
    desc = post_info.desc.replace("  ", " ")
    desc = desc.replace(" #", "#")
    pin = desc.find('#')
    if pin == -1:
        pin = abs(desc_length)
    if desc_length < 0:
        slice_length = min(pin, abs(desc_length))
    else:
        slice_length = desc_length
    name = post_date.strftime(data_format) + "_" + desc[:slice_length]

    # Generate path
    path_str = path_str.replace("//", "/")
    if post_info.num >= separate_limit:
        path_str += '/' + name
    
    # Make dir
    try:
        path = pathlib.Path(path_str).expanduser()
        path.mkdir(parents = True, exist_ok= True)
    except PermissionError as e:
        logger.error(f"Make dir at path {path_str} failed! Permission deny.")
        return False
    else:
        return str(path / name)
    
def single_downloader(url: str, path: str, Cookie: str, logger: logging.Logger) -> bool:
    # Set headers
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
        "Referer": "https://www.douyin.com/",
        "Cookie": Cookie
    }

    # Set retry strategy
    retry_strategy = Retry(
    total=4,
    backoff_factor=2,
    status_forcelist=[500, 502, 503, 504],
    allowed_methods=["HEAD", "GET", "OPTIONS", "POST"])
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session = requests.Session()
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    # Download
    try:
        r = session.get(url, stream=True, headers=headers, timeout=(15, 30))
        r.raise_for_status()
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
        total = int(r.headers.get("Content-Length", 0))
        try:
            with open(path, "wb") as f:
                if pg.isatty():
                    pg.new(2)
                    task = pg.execute(2).add_task(description=str(pathlib.Path(path).name), total=total)
                    pg.live().update(pg.get_group())
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
                    if pg.isatty():
                        pg.execute(2).update(task, advance=len(chunk))
                pg.stop(2)
        except IOError as e:
            logger.error(f"Single_downloader: Error writing to file {path}: {e}")
            return False
        else:
            logger.debug(f"Successfully! Downloaded {path} Link: {url}")
            return True
    finally:
        r.close()
    
def V_downloader(path_str: str, V: post, Cookie: str, logger: logging.Logger, statistic: str = "", task = None) -> int:
    error = 0
    for x in range(1,V.num+1):
        if V.num >= 2:
            name = f"{path_str}_{x}"
        else:
            name = path_str
        if "jpeg" in V.url[x]:
            name += ".jpeg"
        else:
            name += ".mp4"
        if not single_downloader(V.url[x], name, Cookie, logger):
            error += 1
        elif pg.isatty() and task:
            pg.execute(1).update(task, advance=1)
    
    # Result
    if error == 0:
        logger.info(f"Post {V.aweme_id} {align_unicode(V.desc[:8], 20, False)} downloaded.      Total: {V.num}/{V.num}. {statistic}")
        return 0
    else:
        logger.error(f"Post {V.aweme_id} {align_unicode(V.desc[:8], 20, False)} download failed. Total: {V.num - error}/{V.num}. {statistic}")
        return error