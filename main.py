#!/usr/bin/env python3
# Add model searching path
import sys
import pathlib
import atexit
from rich.console import Console

# Add python search path
BASE_PATH = pathlib.Path(__file__).resolve().parent
sys.path.append(str(BASE_PATH / "API"))

# Add cmd before exit & file lock
if pathlib.Path(BASE_PATH / "data" / "run_lock.lock").exists():
    print("Another program is running... Try again later!")
    sys.exit(1)
else:
    pathlib.Path(BASE_PATH / "data" / "run_lock.lock").touch()
atexit.register(pathlib.Path(BASE_PATH / "data" / "run_lock.lock").unlink)
console = Console()
atexit.register(console.show_cursor)

# Fetch args
import src.args
args = src.args.setup_args()

# Settings class
from pydantic import BaseModel
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
user_total = 0
error_f = 0
error_p = 0
error_u = []

# Import settings
import json5
with open(BASE_PATH / str("settings.json"), "r", encoding="utf-8") as f:
    settings = setting(**json5.load(f))

if not args.cookie:
    args.cookie = settings.cookie

# Copy cookie to API config file
import yaml
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
from src.logger import setup_log
main_log = setup_log(settings.stream_level, settings.file_level)

# Setup database
from src.database import database
dtbe = database(settings.database, main_log)

# If args, exit program
if src.args.exe_args(args, main_log):
    # Close database
    dtbe.close()
    # exit program
    sys.exit(1)

# Setup progress
from src.progress import Progress
pgs = Progress()
Progress.new(0)

if not settings.cookie:
    main_log.warning("Cookie required. Post may not download without it.")

# Import tools
from src.align_unicode import align_unicode
from src.readme import generate_readme
import src.downloader
import src.filter
import src.post

user_total = len(settings.users)
for U in settings.users:
    # Empty jump
    if not U.url:
        user_total -= 1
        continue

    # Add user_progress task
    task_user = Progress.execute(0).add_task(description=f"{user_pin}/{user_total}", total=None, status="[yellow]Fetching...")
    Progress.update()

    # Get posts data
    user_pin += 1
    P = src.post.get_posts(U.url, main_log)
    if not P:
        main_log.error(f"Get posts from {U.nickname} {U.url} failed!")
        error_u.append(f"{U.nickname if U.nickname else "Unknown"}")
        continue
    main_log.debug(f"Posts info of user {U.nickname if U.nickname else P.nickname} get. {P} {user_pin}/{user_total}")
    
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
    dt_user = database.find_user(P, U.nickname if U.nickname else P.nickname)

    # Generate readme
    if U.readme and U.new_folder:
        generate_readme(dt_user, P, U.nickname if U.nickname else P.nickname, U.remark, path_str, settings.cookie, main_log)
    
    # Update user_progress task
    Progress.new(1)
    Progress.execute(0).update(task_user, total=len(P.posts), description=f"{P.nickname}[bold orange] {user_pin}/{user_total}", status="[green]Downloading...")
    
    # Post download      
    main_log.debug(f"User {P.nickname if U.nickname == "" else U.nickname} {P.sec_user_id} Save_path: {path_str} downloading... ")
    num = 0
    error_p_s = 0
    for V in P.posts:
        # init
        num += 1
        post_task = Progress.execute(1).add_task(description=V.desc[:10], status="[yellow]Checking...", total=None)
        Progress.update()

        # Database Check
        fit = src.filter.filter(V.desc, U.filter, main_log) and src.filter.time_limit(V.date, U.time_limit, main_log)
        exist_V = database.find_V(P.user_id, V.aweme_id, fit)

        if (fit and exist_V == 1) or (fit and settings.retry_downloaded and exist_V == 2):
            # Make download dir
            mkdir = src.downloader.mkdir_download_path(V, path_str, U.separate_limit, settings.date_format, settings.desc_length, main_log)
            if mkdir:
                # Download posts
                Progress.execute(1).update(post_task, status="[green]processing...", total=V.num)
                download_error = src.downloader.V_downloader(mkdir, V, settings.cookie, main_log, post_task, f"{num}/{len(P.posts)}")
                if download_error:
                    error_p += 1
                    error_f += download_error
                    error_p_s += 1
                    try:
                        error_u.index(P.nickname)
                    except ValueError:
                        error_u.append(P.nickname)
                    Progress.execute(1).update(post_task, status=f"[bold red]Error {download_error}", completed=V.num)
                else:
                    database.download_V(P.user_id, V.aweme_id)
                    Progress.execute(1).update(post_task, status="[bold green]Done")
                    
                download_p += 1
                download_f += V.num
            else:
                main_log.error(f"Make dir failed: {V.aweme_id} {V.desc[:6]}")
                Progress.execute(1).update(post_task, total=0, status="[bold red]Dir Error")
                continue
        else:
            Progress.execute(1).update(post_task, status="[bold purple]Skip", total=V.num, completed=V.num)
            main_log.debug(f"Post {V.aweme_id} {align_unicode(V.desc[:8], 20, False)} skip download. {num}/{len(P.posts)}")
        Progress.execute(0).update(task_user, advance=1)
    if error_p_s:
        Progress.execute(0).update(task_user, status=f"[bold red]Error {error_p_s}")
    else:
        Progress.execute(0).update(task_user, status="[bold green]Done")
    main_log.info(f"User {align_unicode(U.nickname if U.nickname else P.nickname, 20, False)} {P.sec_user_id} is done!")

# Close Progress
Progress.new(2)
pgs.stop()

# Close database
dtbe.close()

# Statistics
if error_u:
    main_log.error(f"""Download completed! Total download:
    Users: {user_total-len(error_u)}/{user_total}
    Post:  {download_p - error_p}/{download_p}
    Files: {download_f - error_f}/{download_f}
Errors:
    {error_u}
""")
else:
    main_log.info(f"""Download completed! Total download:
    Users: {user_pin}
    Post:  {download_p}
    Files: {download_f}
""")