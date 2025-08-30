import argparse
import os
import logging
import re
import sqlite3
if __name__ != "__main__":
    import src.post
    import src.downloader
    import src.database
    import src.filter
    from src.align_unicode import align_unicode

def setup_args() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Download posts and users from Douyin.com Caution: When any is chosen, program won't download users in the settings.json.")

    # Download
    download = parser.add_argument_group("Download Settings", "At least one of \"-U\", \"-P\" and \"-F\" should be selected.")
    download.add_argument("-U", "--user", action="append", metavar="urls", help="Download all posts from the user (support directly paste from app)")
    download.add_argument("-P", "--post", action="append", metavar="urls", help="Download single post (support directly paste from app)")
    download.add_argument("-F", "--file", type=argparse.FileType("r",encoding="UTF-8"), metavar="path", help="Arguments can be read from file. Useful when multiple urls are input. Only \"-U\", \"-P\" and \"-c\" are supported.")
    download.add_argument("-c", "--cookie", type=str, default="", help="Enter your douyin.com cookie here. Default copy from settings.json.")
    download.add_argument("-p", "--path", type=str, help=f"Download path. Default: {os.getcwd()}", default=os.getcwd())
    download.add_argument("-t", "--time", type=str, default="", help="Only download the post which posted inside the interval. The date format should be \"%%Y.%%m.%%d\" or \"%%Y.%%m.%%d %%H:%%M:%%S\". The whole expression should be \"{start}-{end}\". Divide with a '-'. Keep any boundary empty for no limitaion.")
    download.add_argument("-s", "--separate_limit", type=int, default=2, help="If the files in the post is more or equal to this num, they will be put in a single folder. Default is 2.")
    download.add_argument("-r", "--readme", action="store_true", help="Create a readme file for users to store the details. Only works when -U is chosen.")
    download.add_argument(
        "-f",
        "--filter",
        type=str,
        default="",
        help=(
            "Supports Python expressions for filtering. "
            "Keywords must be in ${xxxxx}, e.g., ${Hello}. "
            "Spaces in keywords are ignored. "
            "For special characters '{', '}', '\\', '$', use '\\{', '\\}', '\\\\', '\\$'. "
            "Logical operators not, or, and, and parentheses () are supported. "
            "Example: ${cat} and not ${dog}."
        )
    )
    # Database
    database = parser.add_argument_group("Database Maintenance")
    database.add_argument("-l", "--list", type=str, nargs='?', const="All_Users", metavar="uid", help="List all users in the database or all posts of the user.")
    database.add_argument("-d", "--delete", type=str, metavar="uid", help="Delete user data from the database.")
    database.add_argument("-e", "--execute", type=str, metavar="cmd", help="Execute a SQL cmd to the database.")

    # Version
    version = parser.add_argument_group("Version")
    version.add_argument('--version', action='version', version='0.2.0', help="Show program's version")

    # Get args && Args in file
    args = parser.parse_args()
    if args.file:
        file_lines = args.file.read().splitlines()
        extra_args = []
        for line in file_lines:
            extra_args.extend(parser.convert_arg_line_to_args(line))
        f_args = parser.parse_args(extra_args)
        if f_args.user:
            if args.user is None:
                args.user = []
            args.user += f_args.user
        if f_args.post:
            if args.post is None:
                args.post = []
            args.post += f_args.post
        if f_args.cookie:
            args.cookie += f_args.cookie
    
    return args

def exe_args(args: argparse.Namespace, cur: sqlite3.Cursor, logger: logging.Logger) -> bool:
    if args.user:
        error = 0
        user_pin = 0
        for url in args.user:
            user_pin += 1
            match = re.search(r"http[^\s]*/?", url)
            if not match:
                logger.error(f"Invalid user URL: {url}")
                continue
            U = src.post.get_posts(match.group(), logger)
            if not U:
                continue
            logger.info(f"User {U.nickname} {U.sec_user_id} downloading...  Save_path: {args.path} ")
            for P in U.posts:
                if src.filter.filter(P.desc, args.filter, logger) and src.filter.time_limit(P.date, args.time, logger):
                    down = src.downloader.mkdir_download_path(P, args.path + '/' + U.nickname, args.separate_limit, r"%Y-%m-%d", -15, logger)
                    if down:
                        if not args.cookie:
                            logger.warning("Cookie required. Post may not download without it.")
                        error += src.downloader.V_downloader(down, P, args.cookie, 3, 3, logger, f"{user_pin}/{len(args.user)}")
                    else:
                        continue
                else:
                    logger.info(f"Post {P.aweme_id} {align_unicode(P.desc[:8], 20, False)} skip download. {user_pin}/{len(args.user)}")
        if error:
            logger.error(f"Download users finished. Error: {error}")
        else:
            logger.info("Download users finished. All success!")

    if args.list:
        print(src.database.execute(f"SELECT * FROM \"{args.list}\";", cur, logger))
    
    if args.delete:
        src.database.erase_user(args.delete, cur, logger)
    
    if args.execute:
        print(src.database.execute(args.execute, cur, logger))

    if any([args.user, args.post, args.list, args.delete, args.execute]):
        return True
    else:
        return False


if __name__ == "__main__":
    args = setup_args()
    print(args)