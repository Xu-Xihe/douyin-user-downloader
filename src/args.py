import argparse
import os
import logging
import sqlite3
from src.progress import Progress

def setup_args() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Download posts and users from Douyin.com Caution: When any is chosen, program won't download users in the settings.json.")

    # Download
    download = parser.add_argument_group("Download Settings", "At least one of \"-U\", \"-P\" and \"-F\" should be selected.")
    download.add_argument("-U", "--user", nargs="+", metavar="URLs", help="Download all posts from the user (support directly paste from app)")
    download.add_argument("-P", "--post", nargs="+", metavar="URLs", help="Download single post (support directly paste from app)")
    download.add_argument("-F", "--file", type=argparse.FileType("r",encoding="UTF-8"), metavar="path", help="Arguments can be read from file. Useful when multiple urls are input. Only \"-U\", \"-P\" and \"-c\" are supported.")
    download.add_argument("-c", "--cookie", type=str, default="", help="Enter your douyin.com cookie here. Default copy from settings.json.")
    download.add_argument("-p", "--path", type=str, help=f"Download path. Default: {os.getcwd()}", default=os.getcwd())
    download.add_argument("-s", "--separate_limit", type=int, default=2, help="If the files in the post is more or equal to this num, they will be put in a single folder. Default is 2.")
    download.add_argument("-d", "--desc_length", metavar="LENGTH",type=int, default=-15, help="The length of description of the video in the file name. The abs value is the length and if negative, all letter behind '#' will be abandoned.")
    download.add_argument("-t", "--time", type=str, default="", help="Only download the post which posted inside the interval. The date format should be \"%%Y.%%m.%%d\" or \"%%Y.%%m.%%d %%H:%%M:%%S\". The whole expression should be \"{start}-{end}\". Divide with a '-'. Keep any boundary empty for no limitaion.  Only works for -U.")
    download.add_argument("-r", "--readme", action="store_true", help="Create a readme file for users to store the details. Only works for -U.")
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
            "Only works for -U."
        )
    )
    # Database
    database = parser.add_argument_group("Database Maintenance")
    database.add_argument("-L", "--list", type=str, nargs='?', const="All_Users", metavar="uid", help="List all users in the database or all posts of the user.")
    database.add_argument("-D", "--delete", type=str, metavar="uid", help="Delete user data from the database.")
    database.add_argument("-E", "--execute", type=str, metavar="cmd", help="Execute a SQL cmd to the database.")

    # Version
    version = parser.add_argument_group("Version")
    version.add_argument("-v", "--version", action='version', version='V1.4.0', help="Show program's version")

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

def exe_args(args: argparse.Namespace, logger: logging.Logger) -> bool:
    # Import
    from src.database import database
    if args.user or args.post:
        import src.post
        import src.downloader
        import src.filter
        from src.readme import generate_readme
        from src.align_unicode import align_unicode
        pgs = Progress()
        Progress.new(0)

    # Cookie
    if not args.cookie:
        logger.warning("Cookie required. Post may not download without it.")

    # Users
    if args.user:
        # init
        error = 0
        user_pin = 0

        for url in args.user:
            if "http" not in url:
                continue
            
            # Add user_progress task
            task_user = Progress.execute(0).add_task(description="", total=None)
            Progress.update()
            
            # Statistics
            user_pin += 1
            post_pin = 0

            #Get posts data
            U = src.post.get_posts(url, logger)
            if not U:
                logger.error(f"Get posts failed! {user_pin}/{len(args.user)}")
                continue
            logger.info(f"User {U.nickname} {U.sec_user_id} downloading... {user_pin}/{len(args.user)} Save_path: {args.path} ")

            # Check in database
            dt_user = database.find_user(U, U.nickname)

            # Readme
            if args.readme:
                generate_readme(dt_user, U, U.nickname, "", args.path + '/' + U.nickname, args.cookie, logger)
            
            # Update user_progress task
            Progress.new(1)
            Progress.execute(0).update(task_user, total=len(U.posts), description=f"{U.nickname}[bold orange] {user_pin}/{len(args.user)}")
            
            # Download posts
            for P in U.posts:
                # init
                post_pin += 1
                post_task = Progress.execute(1).add_task(description=P.desc[:10], status="[yellow]Checking...", total=None)
                Progress.update()
                
                # filter check
                if src.filter.filter(P.desc, args.filter, logger) and src.filter.time_limit(P.date, args.time, logger):
                    down = src.downloader.mkdir_download_path(P, args.path + '/' + U.nickname, args.separate_limit, r"%Y-%m-%d", args.desc_length, logger)
                    if down:
                        # Download posts
                        Progress.execute(1).update(post_task, status="[green]processing...", total=P.num)
                        download_error = src.downloader.V_downloader(down, P, args.cookie, logger, post_task, f"{post_pin}/{len(U.posts)}")
                        if download_error:
                            error += download_error
                            Progress.execute(1).update(post_task, status="[bold red]Error")
                        else:
                            Progress.execute(1).update(post_task, status="[bold green]Done")
                    else:
                        Progress.execute(1).update(post_task, total=0, status="[bold red]Dir Error")
                        continue
                else:
                    Progress.execute(1).update(post_task, status="[bold purple]Skip", total=0)
                    logger.info(f"Post {P.aweme_id} {align_unicode(P.desc[:8], 20, False)} skip download. {post_pin}/{len(U.posts)}")
                Progress.execute(0).update(task_user, advance=1)
        if error:
            logger.error(f"Download users finished. Error: {error}")
        else:
            logger.info(f"Download users finished. All success! Total: {user_pin}")

    # Post
    if args.post:
        # init
        error = 0
        post_pin = 0
        Progress.new(1)

        for url in args.post:
            if "http" not in url:
                continue

            # init
            post_pin += 1
            post_task = Progress.execute(1).add_task(description="", status="[yellow]Checking...", total=None)
            Progress.update()
            
            P = src.post.get_single_post(url, logger)
            if P:
                down = src.downloader.mkdir_download_path(P, args.path, args.separate_limit, r"%Y-%m-%d", args.desc_length, logger)
                if down:
                    Progress.execute(1).update(post_task, status="[green]processing...", total=P.num, description=P.desc[:10])
                    download_error = src.downloader.V_downloader(down, P, args.cookie, logger, post_task, f"{post_pin}/{len(args.post)}")
                    if download_error:
                        error += download_error
                        Progress.execute(1).update(post_task, status="[bold red]Error")
                    else:
                        Progress.execute(1).update(post_task, status="[bold green]Done")
                else:
                    logger.error(f"Make dir failed: {P.aweme_id} {P.desc[:6]}")
                    Progress.execute(1).update(post_task, total=0, status="[bold red]Dir Error", description=P.desc[:10])
                    continue
            else:
                logger.error("Get post error!")
                Progress.execute(1).update(post_task, status="[bold red]Get Post Error", total=0)
        if error:
            logger.error(f"Download posts finished. Error: {error}")
        else:
            logger.info(f"Download posts finished. All success! Total: {post_pin}")

    # Stop live
    if args.user or args.post:
        Progress.new(2)
        pgs.stop()

    # Database
    if args.list:
        print(database.execute(f"SELECT * FROM \"{args.list}\";"))
    
    if args.delete:
        database.erase_user(args.delete)
    
    if args.execute:
        rp = database.execute(args.execute)
        print(f"Database response: {rp}")
        logger.info(f"Database response: {rp}")

    # Args use?
    if any([args.user, args.post, args.list, args.delete, args.execute]):
        return True
    else:
        return False


if __name__ == "__main__":
    args = setup_args()
    print(args)