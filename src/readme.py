import logging
import pathlib
import re
import io
import time
import filecmp
import src.downloader
from src.post import poster
from src.database import database
from src.align_unicode import align_address

def diff_img(org_img: str, upt_img: str) -> bool:
    if "0.jpeg" in org_img:
        return True
    try:
        diff = filecmp.cmp(org_img, upt_img, shallow=False)
    except Exception:
        pathlib.Path(upt_img).unlink()
        return False
    else:
        if not diff:
            return True
        else:
            pathlib.Path(upt_img).unlink()
            return False

def find_largest_file(dir: pathlib.Path, prefix: str) -> int:
    pattern = re.compile(prefix + r"(\d+)\.jpeg", re.IGNORECASE)
    max_num = 0
    for p in dir.rglob(f"{prefix}*.jpeg"):
        m = pattern.fullmatch(p.name)
        if m:
            num = int(m.group(1))
            if num > max_num:
                max_num = num
    return max_num

def add_history(title: str, new_value, old: list, f: io.TextIOWrapper, add: bool = True):
    f.write(f"### {title}\n\n")
    try:
        pin = old.index(f"### {title}\n") +2
    except ValueError:
        pass
    else:
        while True:
            f.write(old[pin])
            if old[pin] == '\n' or "###" in old[pin]:
                break
            else:
                pin += 1
    finally:
        if add:
            f.write(f"- <span style=\"color: purple;\">{time.strftime(r"%Y.%m.%d", time.localtime(time.time()))}:</span>")
            if (title == "Avatar" or title == "Cover"):
                f.write(f"""
    <p align="center">
    <img src="./.{str.lower(title)}/{str.lower(title)}{abs(new_value)}.jpeg" alt="{str.lower(title)}" />
    </p>\n\n""")
            else:
                f.write(f" {new_value}\n\n")


def generate_readme(histroy: list, U: poster, nickname: str, remark: str, path_str:str, Cookie: str, logger: logging.Logger):
    path_readme = pathlib.Path(path_str).expanduser() / "readme.md"
    path_cover = pathlib.Path(path_str).expanduser() / ".cover"
    path_avatar = pathlib.Path(path_str).expanduser() / ".avatar"
    path_cover.mkdir(parents=True, exist_ok=True)
    path_avatar.mkdir(parents=True, exist_ok=True)
    num_cover = find_largest_file(path_cover,"cover")
    num_avatar = find_largest_file(path_avatar,"avatar")
    if not histroy:
        num_avatar = 0
        num_cover = 0
    src.downloader.single_downloader(U.avatar,
                                     f"{str(path_avatar.resolve())}/avatar{num_avatar + 1}.jpeg",
                                     Cookie, logger)
    src.downloader.single_downloader(U.cover,
                                     f"{str(path_cover.resolve())}/cover{num_cover + 1}.jpeg",
                                     Cookie, logger)
    if diff_img(f"{str(path_avatar.resolve())}/avatar{num_avatar}.jpeg", f"{str(path_avatar.resolve())}/avatar{num_avatar + 1}.jpeg"):
        num_avatar += 1
        num_avatar *= -1
    if diff_img(f"{str(path_cover.resolve())}/cover{num_cover}.jpeg", f"{str(path_cover.resolve())}/cover{num_cover + 1}.jpeg"):
        num_cover += 1
        num_cover *= -1
    old = []
    if path_readme.exists():
        try:
            with open (path_readme, "r", encoding="UTF-8") as f:
                while True:
                    if f.readline() == "## Update history\n" or f.readline() == "":
                        if histroy:
                            old = f.readlines()
                        break
        except OSError as e:
            logger.error(f"Open readme.md failed: {e}")
            return
    try:
        with open(path_readme, "w", encoding="UTF-8") as f:
            f.write(f"""# {nickname if nickname else U.nickname}

<p align="center">
  <img src="./.avatar/avatar{abs(num_avatar)}.jpeg" alt="avatar" />
</p>
                    
| <span style="color: purple;"><b>Item</b></span> | <span style="color: purple;"><b>Content</b></span> |
| :--------: | :-: |
| Nickname | {U.nickname} |
| Douyin ID | {U.unique_id} |
| Gender | {"Male" if U.gender == 1 else "Female" if U.gender == 2 else "Unknown"} |
| Age | {U.age if not U.age == -1 else "Unknown"} |
| Address | {align_address(U.country, U.province, U.city)} |
| School | {U.school if U.school else "Unknown"} |
| IP | {U.ip[5:]} |
| Signature | {U.signature.replace("\n", "<br>")} |
| Remark | {remark.replace("\n", "<br>")} |
| user_id | {U.user_id} |
| sec_user_id | {U.sec_user_id} |

<p align="center">
  <img src="./.cover/cover{abs(num_cover)}.jpeg" alt="" />
</p>
## Update history

""")
            if histroy:
                if not U.nickname == histroy[2]:
                    add_history("Nickname", U.nickname, old, f)
                    database.update_user(U.user_id, "nickname", U.nickname)
                else:
                    add_history("Nickname", "", old, f, False)
                if not U.unique_id == histroy[3]:
                    add_history("Douyin ID", U.unique_id, old, f)
                    database.update_user(U.user_id, "unique_id", U.unique_id)
                else:
                    add_history("Douyin ID", "", old, f, False)
                if not U.gender == histroy[4]:
                    add_history("Gender", "Male" if U.gender == 1 else "Female" if U.gender == 2 else "Unknown", old, f)
                    database.update_user(U.user_id, "gender", U.gender)
                else:
                    add_history("Gender", "", old, f, False)
                if not U.age == histroy[5]:
                    add_history("Age", {str(U.age) if not U.age == -1 else "Unknown"}, old, f)
                    database.update_user(U.user_id, "age", U.age)
                else:
                    add_history("Age", "", old, f, False)
                if not align_address(U.country, U.province, U.city) == histroy[6]:
                    add_history("Address", align_address(U.country, U.province, U.city), old, f)
                    database.update_user(U.user_id, "address", align_address(U.country, U.province, U.city))
                else:
                    add_history("Address", "", old, f, False)
                if not U.school == histroy[7]:
                    add_history("School", U.school if U.school else "Unknown", old, f)
                    database.update_user(U.user_id, "school", U.school)
                else:
                    add_history("School", "", old, f, False)
                if not U.ip == histroy[8]:
                    add_history("IP", U.ip[5:], old, f)
                    database.update_user(U.user_id, "ip", U.ip)
                else:
                    add_history("IP", "", old, f, False)
                if not U.signature == histroy[9]:
                    add_history("Signature", U.signature, old, f)
                    database.update_user(U.user_id, "signature", U.signature)
                else:
                    add_history("Signature", "", old, f, False)
                if num_avatar < 0:
                    add_history("Avatar", abs(num_avatar), old, f)
                else:
                    add_history("Avatar", "", old, f, False)
                if num_cover < 0:
                    add_history("Cover", abs(num_cover), old, f)
                else:
                    add_history("Cover", "", old, f, False)
            else:
                add_history("Nickname", U.nickname, old, f)
                add_history("Douyin ID", U.unique_id, old, f)
                add_history("Gender", "Male" if U.gender == 1 else "Female" if U.gender == 2 else "Unknown", old, f)
                add_history("Age", {str(U.age) if not U.age == -1 else "Unknown"}, old, f)
                add_history("Address", align_address(U.country, U.province, U.city), old, f)
                add_history("School", U.school if U.school else "Unknown", old, f)
                add_history("IP", U.ip[5:], old, f)
                add_history("Signature", U.signature, old, f)
                add_history("Avatar", abs(num_avatar), old, f)
                add_history("Cover", abs(num_cover), old, f)

    except IOError as e:
        logger.error(f"Generate readme file error: {e}")