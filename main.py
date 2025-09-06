#!/usr/bin/env python3
# Add model searching path
import sys
import pathlib
BASE_PATH = pathlib.Path(__file__).resolve().parent
sys.path.append(str(BASE_PATH / "API"))

# Fetch args
import src.args
args = src.args.setup_args()

# Import tools
import sqlite3
import json5
import yaml
from pydantic import BaseModel
from src.logger import setup_log
from src.align_unicode import align_unicode
from src.readme import generate_readme
from src.progress import pg
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
    stream_level: str = "WARNING"
    file_level: str = "INFO"
    # Allow self class
    model_config = {
        "arbitrary_types_allowed": True
    }

# Statistics
download_f = 0
download_p = 0
user_pin = 0
error_f = 0
error_p = 0
error_u = []

# Import settings
with open(BASE_PATH / str("settings.json"), "r", encoding="utf-8") as f:
    settings = setting(**json5.load(f))

if not args.cookie:
    args.cookie = settings.cookie

# Copy cookie to API config file
API_config_file_path = BASE_PATH / "API" / "crawlers" / "douyin" / "web" / "config.yaml"
if not API_config_file_path.exists():
    print("API config file does not exist.")
    sys.exit(1)
with open(API_config_file_path, "r", encoding="utf-8") as f:
    API_config_file = yaml.safe_load(f)
API_config_file["TokenManager"]["douyin"]["headers"]["Cookie"] = args.cookie
with open(API_config_file_path, "w", encoding="utf-8") as f:
    yaml.safe_dump(API_config_file, f, allow_unicode=True)

# Setup logger
main_log = setup_log(settings.stream_level, settings.file_level)

# Connect database
try:
    dtbe = sqlite3.connect(str(BASE_PATH / "data/downloaded.db"))
except sqlite3.OperationalError as e:
        main_log.error(f"Connect to database failed: OperationalError {e}")
        if settings.database:
            sys.exit(1)
except sqlite3.Error as e:
        main_log.error(f"Connect to database failed: {e}")
        if settings.database:
            sys.exit(1)
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
    sys.exit(1)

if not settings.cookie:
    main_log.warning("Cookie required. Post may not download without it.")

# Set up progress & live
if pg.isatty():
    pg.live().start()
    pg.new(0)

for U in settings.users:
    # Add user_progress task
    if pg.isatty():
        task_user = pg.execute(0).add_task(description="", total=None)
        pg.live().update(pg.get_group())

    # Get posts data
    user_pin += 1
    P = src.post.get_posts(U.url, main_log)
    if not P:
        main_log.error(f"Get posts from {U.nickname} {U.url} failed!")
        continue
    main_log.debug(f"Posts info of user {U.nickname if U.nickname else P.nickname} get. {user_pin}/{len(settings.users)}")
    
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
    if U.readme and U.new_folder:
        generate_readme(dt_user, P, U.nickname if U.nickname else P.nickname, U.remark, path_str, settings.cookie, cur, main_log)
    
    # Update user_progress task
    if pg.isatty():
        pg.new(1)
        pg.execute(0).update(task_user, total=len(P.posts), description=f"{P.nickname}[bold orange] {user_pin}/{len(settings.users)}")
    
    # Post download      
    main_log.debug(f"User {P.nickname if U.nickname == "" else U.nickname} {P.sec_user_id} Save_path: {path_str} downloading... ")
    num = 0
    for V in P.posts:
        # init
        num += 1
        if pg.isatty():
            post_task = pg.execute(1).add_task(description=V.desc[:10], status="[yellow]Checking...", total=None)
            pg.live().update(pg.get_group())

        # Database Check
        fit = src.filter.filter(V.desc, U.filter, main_log) and src.filter.time_limit(V.date, U.time_limit, main_log)
        exist_V = src.database.find_V(P.user_id, V.aweme_id, fit, cur, main_log)

        if (fit and exist_V == 1) or (fit and settings.retry_downloaded and exist_V == 2):
            # Make download dir
            mkdir = src.downloader.mkdir_download_path(V, path_str, U.separate_limit, settings.date_format, settings.desc_length, main_log)
            if mkdir:
                # Download posts
                if pg.isatty():
                    pg.execute(1).update(post_task, status="[green]processing...", total=V.num)
                    download_error = src.downloader.V_downloader(mkdir, V, settings.cookie, main_log, f"{num}/{len(P.posts)}", post_task)
                else:
                    download_error = src.downloader.V_downloader(mkdir, V, settings.cookie, main_log, f"{num}/{len(P.posts)}")
                if download_error:
                    error_p += 1
                    error_f += download_error
                    try:
                        error_u.index(P.nickname)
                    except ValueError:
                        error_u.append(P.nickname)
                    if pg.isatty():
                        pg.execute(1).update(post_task, status="[bold red]Error")
                else:
                    src.database.download_V(P.user_id, V.aweme_id, cur, main_log)
                    if pg.isatty():
                        pg.execute(1).update(post_task, status="[bold green]Done")
                download_p += 1
                download_f += V.num
            else:
                main_log.error(f"Make dir failed: {V.aweme_id} {V.desc[:6]}")
                if pg.isatty():
                    pg.execute(1).update(post_task, total=0, status="[bold red]Dir Error")
                continue
        else:
            if pg.isatty():
                pg.execute(1).update(post_task, status="[bold purple]Skip", total=0)
            main_log.debug(f"Post {V.aweme_id} {align_unicode(V.desc[:8], 20, False)} skip download. {num}/{len(P.posts)}")
        if pg.isatty():
            pg.execute(0).update(task_user, advance=1)
    main_log.info(f"User {align_unicode(U.nickname if U.nickname else P.nickname, 20, False)} {P.sec_user_id} is done!")
    if settings.database:
        try:
            dtbe.commit()
        except sqlite3.OperationalError as e:
            main_log.error(f"Commit to database failed: OperationalError {e}")
        except sqlite3.Error as e:
            main_log.error(f"Commit to database failed: {e}")

if pg.isatty():
    pg.new(2)
    pg.live().stop()

# Close database
cur.close()
dtbe.close()

# Statistics
if error_u:
    main_log.error(f"""Download completed! Total download:
    Users: {len(settings.users)-len(error_u)}/{len(settings.users)}
    Post:  {download_p - error_p}/{download_p}
    Files: {download_f - error_f}/{download_f}
Errors:
    {error_u}
""")
else:
    main_log.info(f"""Download completed! Total download:
    Users: {len(settings.users)}
    Post:  {download_p}
    Files: {download_f}
""")