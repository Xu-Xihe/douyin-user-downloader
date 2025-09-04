#!/usr/bin/env python3
# Add model searching path
import sys
import pathlib
BASE_PATH = pathlib.Path(__file__).resolve().parent
sys.path.append(str(BASE_PATH / "API"))
import src.args

# Fetch args
args = src.args.setup_args()

import sqlite3
import json5
import yaml
from pydantic import BaseModel, ValidationError
from src.logger import setup_log
from src.align_unicode import align_unicode
from src.readme import generate_readme
import src.downloader
import src.filter
import src.post
import src.database

# Settings class
class user(BaseModel):
    url: str
    nickname: str = ""
    path: str = ""
    remark: str = ""
    time_limit: str = ""
    separate_limit: int = 2
    new_folder: bool = True
    readme: bool = True
    filter: str = ""

class setting(BaseModel):
    database: bool = True
    default_path:str = "~/Downloads"
    date_format:str = r"%Y-%m-%d"
    desc_length: int = -15
    users: list[user]
    cookie: str
    retry_downloaded: bool = True
    retry: int = 3
    retry_sec: int = 3
    # Allow self class
    model_config = {
        "arbitrary_types_allowed": True
    }

# Statistics
download_p = 0
download_f = 0
error_p = 0
error_f = 0
user_pin = 0

# Setup logger
main_log = setup_log()

# Import settings
with open(BASE_PATH / str("settings.json"), "r", encoding="utf-8") as f:
    try:
        settings = setting(**json5.load(f))
    except ValidationError as e:
        main_log.error(f"Failed to load the config: {e}")
        exit()
    else:
        main_log.info(f"Successfully loaded config from file.")
        main_log.debug(f"Config loaded: {settings}")

if not args.cookie:
    args.cookie = settings.cookie

# Copy cookie to API config file
API_config_file_path = BASE_PATH / "API" / "crawlers" / "douyin" / "web" / "config.yaml"
if not API_config_file_path.exists():
    main_log.error("API config file does not exist.")
    exit()
with open(API_config_file_path, "r", encoding="utf-8") as f:
    API_config_file = yaml.safe_load(f)
API_config_file["TokenManager"]["douyin"]["headers"]["Cookie"] = args.cookie
with open(API_config_file_path, "w", encoding="utf-8") as f:
    yaml.safe_dump(API_config_file, f, allow_unicode=True)

# Connect database
try:
    dtbe = sqlite3.connect(str(BASE_PATH / "logs/downloaded.db"))
except sqlite3.OperationalError as e:
        main_log.error(f"Connect to database failed: OperationalError {e}")
except sqlite3.Error as e:
        main_log.error(f"Connect to database failed: {e}")
else:
    cur = dtbe.cursor()
    main_log.debug("Successfully connected to database.")

# If args, exit program
if src.args.exe_args(args, cur, main_log):
    cur.close()
    if settings.database:
        try:
            dtbe.commit()
        except sqlite3.OperationalError as e:
            main_log.error(f"Commit to database failed: OperationalError {e}")
        except sqlite3.Error as e:
            main_log.error(f"Commit to database failed: {e}")
    dtbe.close()
    exit()

if not settings.cookie:
    main_log.warning("Cookie required. Post may not download without it.")

for U in settings.users:
    #Get posts data
    user_pin += 1
    P = src.post.get_posts(U.url, main_log)
    main_log.info(f"Posts info of user {U.nickname if U.nickname else P.nickname} get. {user_pin}/{len(settings.users)}")
    if not P:
        main_log.error(f"Get posts from {U.url} failed!")
        continue
    
    # Generate save path
    if U.path:
        path_str = U.path
    else:
        path_str = settings.default_path
    if U.new_folder:
        if U.nickname:
            path_str += '/' + U.nickname
        else:
            path_str += '/' + P.nickname

    # Check in database
    dt_user = src.database.find_user(P, U.nickname if U.nickname else P.nickname, cur, main_log)

    # Generate readme
    if U.readme:
        generate_readme(dt_user, P, U.nickname if U.nickname else P.nickname, U.remark, path_str, settings.cookie, cur, main_log)

    # Post download      
    main_log.info(f"User {P.nickname if U.nickname == "" else U.nickname} {P.sec_user_id} Save_path: {path_str} downloading... ")
    num = 0
    for V in P.posts:
        num += 1
        # Database Check
        fit = src.filter.filter(V.desc, U.filter, main_log) and src.filter.time_limit(V.date, U.time_limit, main_log)
        exist_V = src.database.find_V(P.user_id, V.aweme_id, fit, cur, main_log)

        if (fit and exist_V == 1) or (fit and settings.retry_downloaded and exist_V == 2):
            # Make download dir
            mkdir = src.downloader.mkdir_download_path(V, path_str, U.separate_limit, settings.date_format, settings.desc_length, main_log)
            if not mkdir:
                continue
            
            # Download post
            download_error = src.downloader.V_downloader(mkdir, V, settings.cookie, settings.retry, settings.retry_sec, main_log, f"{num}/{len(P.posts)}")
            if download_error:
                error_p += 1
                error_f += download_error
            else:
                src.database.download_V(P.user_id, V.aweme_id, cur, main_log)
            download_p += 1
            download_f += V.num
        else:
            main_log.info(f"Post {V.aweme_id} {align_unicode(V.desc[:8], 20, False)} skip download. {num}/{len(P.posts)}")
    main_log.info(f"User {align_unicode(P.nickname if U.nickname == "" else U.nickname, 20, False)} {P.sec_user_id} is done!")

# Close database
cur.close()
if settings.database:
    try:
        dtbe.commit()
    except sqlite3.OperationalError as e:
        main_log.error(f"Commit to database failed: OperationalError {e}")
    except sqlite3.Error as e:
        main_log.error(f"Commit to database failed: {e}")
dtbe.close()

# Statistics
main_log.info(f"""Download completed! Total download:
    Users: {len(settings.users)}
    Post:  {download_p - error_p}/{download_p}
    Files: {download_f - error_f}/{download_f}
    """)