from pydantic import BaseModel, ValidationError
from src.logger import setup_log
from src.downloader import V_downloader, single_downloader
import src.post
import src.database
import pathlib
import sqlite3
import datetime
import json5
import time

# Settings class
class user(BaseModel):
    nickname: str
    url: str
    path: str
    separate_limit: int = 2
    new_folder: bool = True
    key_filter: str
    key_include: bool = True

class setting(BaseModel):
    base_url: str = "https://douyin.wtf"
    database: bool = True
    default_path:str = "~/Downloads"
    date_format:str = r"%Y-%m-%d"
    desc_length: int = 15
    users: list[user]
    cookie: str
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

# Run
main_log.info("\n\nProgram Start\n\n")

# Import settings
with open("settings.json", "r", encoding="utf-8") as f:
    try:
        settings = setting(**json5.load(f))
    except ValidationError as e:
        main_log.error(f"Failed to load the config: {e}")
        exit()
    else:
        main_log.info(f"Successfully loaded config from file.")
        main_log.debug(f"Config loaded: {settings}")

# Connect database
try:
    dtbe = sqlite3.connect("log/downloaded.db")
except sqlite3.OperationalError as e:
    if settings.database:
        main_log.error(f"Connect to database failed: OperationalError {e}")
    else:
        main_log.info(f"Connect to database failed: OperationalError {e}")
except sqlite3.Error as e:
    if settings.database:
        main_log.error(f"Connect to database failed: {e}")
    else:
        main_log.info(f"Connect to database failed: {e}")
else:
    cur = dtbe.cursor()
    main_log.debug("Successfully connected to database.")

for U in settings.users:
    user_pin += 1
    main_log.info(f"Geting posts info of user {U.nickname}... {user_pin}/{len(settings.users)}")
    P = src.post.get_post(U.url, settings.base_url, main_log)
    if P == False:
        main_log.error(f"Get posts from {U.url} failed!")
        continue

    # Generate save path
    if U.path == "":
        path_str = settings.default_path
    else:
        path_str = U.path
    if U.new_folder:
        if U.nickname == "":
            path_str += "/"+P.nickname
        else:
            path_str += "/"+U.nickname
    path_str.replace("//","/")
    path = pathlib.Path(path_str).expanduser()
    path_str = str(path.resolve()) # Transform to absolute path
    try:
        path.mkdir(parents = True, exist_ok= True)
    except PermissionError as e:
        main_log.error(f"Make dir at path {path_str} failed! Permission deny.")

    main_log.info(f"User {P.nickname if U.nickname == "" else U.nickname} {P.sec_user_id} save_path: {path_str} downloading... ")

    # All-new download check
    exist_TABLE = src.database.find_user(P.user_id, cur, main_log)
    if settings.database == False or (settings.database == True and exist_TABLE == False):
        exist = False
    else:
        exist = True

    num = 0
    for V in P.posts:
        num += 1
        #Database Check
        if U.key_filter == "":
            fit = True
        elif (U.key_filter in V.desc and U.key_include) or (U.key_filter not in V.desc and U.key_include == False):
            fit = True
        else:
            fit = False
        need_D = src.database.find_V(P.user_id, V.aweme_id, fit, cur, main_log)

        #Post time & name
        post_dt = datetime.datetime.fromtimestamp(V.date)
        name = post_dt.strftime(settings.date_format) + "_" + V.desc[:settings.desc_length]
        
        #Download post
        if exist == False or (exist and need_D):
            if V.num >= U.separate_limit:
                V_path = path / name
                try:
                    V_path.mkdir(exist_ok=True)
                except PermissionError as e:
                    main_log.error(f"Make dir at path {V_path.resolve()} failed! Permission deny.")
            else:
                V_path = path
            erf = V_downloader(str(V_path.resolve()) + "/" + name, V, settings.base_url, settings.cookie, main_log)
            download_p += 1
            download_f += V.num
            # Retry download
            for i in range(settings.retry):
                if len(erf) == 0:
                    break
                for j in erf:
                    main_log.info(f"Wait for retry: {1 if j == 0 else j}/{V.num}. {settings.retry_sec}s.")
                    time.sleep(settings.retry_sec)
                    if single_downloader(V.url[j], str(V_path.resolve()) + "/" + name, settings.base_url, settings.cookie, main_log, False if j == 0 else True):
                        erf.remove(j)

            if not len(erf) == 0:
                main_log.error(f"Download Post {V.aweme_id} {V.desc[:8]} failed. Total: {V.num - len(erf)}/{V.num}. {num}/{len(P.posts)}")
                error_f += erf
                error_p += 1
            else:
                main_log.info(f"Download Post {V.aweme_id} {V.desc[:8]:<20} done. Total: {V.num}/{V.num}. {num}/{len(P.posts)}")
        else:
            main_log.info(f"Post {V.aweme_id} {V.desc[:8]} is exist or be filtered off, download jumped. {num}/{len(P.posts)}")
    main_log.info(f"User {P.nickname if U.nickname == "" else U.nickname} {P.sec_user_id} is done!")

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

# Statisticsx
main_log.info(f"""Download completed! Total download:
    Users: {len(settings.users)}
    Post:  {download_p - error_p}/{download_p}
    Files: {download_f - error_f}/{download_f}
    """)