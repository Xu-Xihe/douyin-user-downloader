<h1 align="center">Douyin-User-Downloader</h1>

<div align="center">
A tool for downloading the user(s) post from Douyin. </center>
</div>
<br/>

<div align="center">
<img alt="GitHub License" src="https://img.shields.io/github/license/Xu-Xihe/douyin-user-downloader">
<img alt="GitHub last commit" src="https://img.shields.io/github/last-commit/Xu-Xihe/douyin-user-downloader">
<img alt="GitHub repo size" src="https://img.shields.io/github/repo-size/Xu-Xihe/douyin-user-downloader">
<img alt="GitHub Issues or Pull Requests" src="https://img.shields.io/github/issues/Xu-Xihe/douyin-user-downloader">
<img alt="GitHub Issues or Pull Requests" src="https://img.shields.io/github/issues-closed/Xu-Xihe/douyin-user-downloader">
<img alt="Static Badge" src="https://img.shields.io/badge/Python3-8A2BE2">
<br>
<img alt="GitHub watchers" src="https://img.shields.io/github/watchers/Xu-Xihe/douyin-user-downloader">
<img alt="GitHub forks" src="https://img.shields.io/github/forks/Xu-Xihe/douyin-user-downloader">
<img alt="GitHub Repo stars" src="https://img.shields.io/github/stars/Xu-Xihe/douyin-user-downloader">
<br>
<img alt="GitHub Release" src="https://img.shields.io/github/v/release/Xu-Xihe/douyin-user-downloader">
<img alt="GitHub Actions Workflow Status" src="https://img.shields.io/github/actions/workflow/status/Xu-Xihe/douyin-user-downloader/docker_publish.yml">
</div>


## 0 Core Features

### Fully Content Support!

- **Video:** Support for high quality video download with no watermark

- **Photos:** Support for packaging download albums, also without watermark. Even the photos that not allowed to download from the app.

- **LIVE Photos:** Amazing improvement! Now LIVE Photos can be downloaded as `.mp4` files. The mix posts(contain both live and static pics) are also supported!

- **User Profiles:** Nickname, IP location, School..... Everything you want! What's more, it can record the history of profile changes!

### Flexible Configuration

-  **Separate Configuration:** Users are configured separately, easier for configing different path, alias and filters!
- **Filters:** Easily select the videos you want from a user using the familiar Python-kind expressions!
- **Time Limitation:** Choose the interval for videos you want!
- **Description:** The length of description in the file name is due to you! Also you can choose to abandon the description after '#'.
- **Folders Separation:** Auto make dir for a post if the num of the works inside is above the limit.
- **Multipul Command-line Parameters:** Flexibly and conveniently download users and posts temporarily and maintain database!

### Automation Design

- **Database:** A built-in database aims for increasing downloading, retrying failed tasks and updating user profiles.
- **Cron job:** Design for loop execution. You can add it to crontab manually. Also the cron job is embedded in the docker container.

## 1 Get Start!

### Docker (Recommend)

#### 0 Quick Start

```bash
docker run -d --name douyin-user-downloader -v /path/to/file/settings.json:/app/settings.json -v /path/to/download:/app/Downloads ghcr.io/xu-xihe/douyin-user-downloader
```

#### 1 Volums

- **settings.json (Required):** `-v /home/path/to/setting_file.json:/app/settings.json`
- **Download Folder (Required):** `-v /home/path/to/download:/container/path/to/download`
- **Logs Folder (Optional):** `-v /home/path/to/log:/app/data`

> [!CAUTION]
>
> Make sure file `/home/path/setting_file.json` is exist. Or docker will make a dir called `setting_file.json` instead of a file.
>
> So download the file `settings.json` from the repo before creating the docker container is recommended.

#### 2 Cron Schedule

The cron schedule can be changed by adding the option `-e` to `docker run`.

```bash
-e CRON_SCHEDULE="your schedule"
```

Default is `CRON_SCHEDULE="0 8,20 * * *"`.

### Local Installation

#### Install Python

Please go to [python.org](https://www.python.org/downloads/) and download the proper package for your system.

> [!CAUTION]
>
> Make sure your python version is **>=3.10**.

#### Clone the repo

```bash
git clone --recurse-submodules https://github.com/Xu-Xihe/douyin-user-downloader.git
```

#### Install requirements

```bash
pip install -r requirements.txt
```

#### Run the program

```bash
python3 main.py
```

or

```bash
python main.py
```

#### (Optional) Add cron job

Refer to system documents. **Plan recommendation:** 0 8,20 * * *

> [!TIP]
>
> Make sure the interval between each excuse is longer than the time of one time excuse. Or something may get wrong.

## 2 Configuration

### Fetch Cookie **(Important)**

The program needs cookie to avoid api rick management. Please follow the step to get your cookie.

1. Open the browser and visit [doyin_web](https://www.douyin.com/).
2. Sign in your account.
3. Open the developer tools of your browser.
4. Go to the Network page and select the filter `XHR/Fetch.`
5. Your will find the cookie string at the `Headers` of some files. Copy it and fill in the `settings.json`.

> [!WARNING]
>
> If the downloads continue showing failed, please refresh the cookie first!

### Config File

`"users":[]`:

​        **Value:** LIST

​        **Required:** ✅

​        **Description:** Users for download.

`"cookie": ""`:

​        **Value:** Str

​        **Required:** ✅

​        **Description:** Enter your Douyin cookie here.

`"database": true`:

​        **Value:** BOOL

​        **Required:** ❌

​        **Description:** Enable the database-relatied functions. If false, the operation will still be excused but the changes will not be committed.

`"file_check: false"`:

​	**Value:** BOOL

​        **Required:** ❌

​	**Description:** Enable the file check for the downloaded posts.

> [!CAUTION]
>
> This relay on the path & the prefix of the file.
>
> Make sure the file name continues to be the same.
>
> Or it may cause muliple re-download.

`"default_path": "Downloads/"`:

​        **Value:** Path_Str

​        **Required:** ❌

​        **Description:** The default path for download files. Resolve path is recommended in docker container. Use '/', even on Windows.

`"retry_downloaded": true`:

​        **Value:** BOOL

​        **Required:** ❌

​        **Description:** Retry the failed download task that recorded in the database.

`"stream_level": "WARNING"` & `"file_level": "INFO"`:

​        **Value:** Str

​        **Required:** ❌

​        **Description:** Set the log level for stdout and file.

​        **Option:** `DEBUG`, `INFO`, `WARNING`, `ERROR`.

`"date_format": "%Y-%m-%d"`:

​        **Value:** Str

​        **Required:** ❌

​        **Description:** The format of data in the name of download files.

​        **Parameters:**

| **Parameter** | **Value** | **Parameter** | **Value** |
| ------------- | --------- | ------------- | --------- |
| %Y            | Year      | %H            | Hour      |
| %m            | Month     | %M            | Minute    |
| %d            | Day       | %S            | Second    |

`"desc_length": -15`:

​        **Value:** INT

​        **Required:** ❌

​        **Description:** The length of description in the name of download files. If it is negative, all content after '#' will be abandoned.

#### users

`"url": ""`:

​        **Value:** Str

​        **Required:** ✅

​        **Description:** The url of user post page, shaped like "https://www.douyin.com/user/xxx" or "https://v.douyin.com/xxx".

> [!WARNING]
>
> Douyin share link(shaped like "https://v.douyin.com/xxx") may changed after a period of time. Try to avoid use it.

`"nickname": ""`:

​        **Value:** Str

​        **Required:** ❌

​        **Description:** Custom alias. Use for logs and folder name. Empty for default nickname.

`"path": ""`:

​        **Value:** Path_Str

​        **Required:** ❌

​        **Description:** Custom download path. Empty for `"default_path"`.

`"remark": ""`:

​        **Value:** Str

​        **Required:** ❌

​        **Description:** This str will be added to the readme.md. `"readme"` should be set to true.

`"time_limit": ""`:

​        **Value:** Str

​        **Required:** ❌

​        **Description:** Only download the post which posted inside the interval.

​        **Date Format:** **"Year.Month.Day"** or **"Year.Month.Day Hour:Minute:Second"**. The hour, minute and second is optional. They will be set to 00:00:00 as default.

​        **Format:** **"Start-End"**. Keep any boundary empty for no limitaion.

​        **Example:** 

	                - "2024.9.1-2025.9.1"
	                - "-2025.3.1"
	                - "2025.1.1-"
	                - "2024.9.3 20:12:3-2025.3.9 2:21:3"

`"separate_limit": 2`:

​        **Value:** INT

​        **Required:** ❌

​        **Description:** If the files in a single post is more or equal to this num, they will be put in a single folder.

`"new_folder": true`:

​        **Value:** BOOL

​        **Required:** ❌

​        **Description:** Make new folder in the path for download.

​        **Example:** 

- True:

	-user

​        -2022-11-28 13:09 xxx.mp4

​        -2022-11-28 13:09 xxx.mp4

- False

​    -2022-11-28 13:09 xxx.mp4

​    -2022-11-28 13:09 xxx.mp4

`"readme": true`:

​        **Value:** BOOL

​        **Required:** ❌

​        **Description:** Create a readme file for users to store the details.

`"filter": ""`:

​        **Value:** Str

​        **Required:** ❌

​        **Description:** Select which posts from a user to download.

​        **Format:** 

- Key word must be in `${xxxxx}`.
- Any space in the key word will be ignored.
- If `{`, `}`, `\`, `$` is in the key word, use `\{`, `\}`, `\`, `\$` instead.
- Use `not`, `or`, `and`, `()` to show a pattern.

​        **Example:** ***(\${Hello} or \${Hi}) and \${Jon} and not \${Harry}*** Only download posts with "Hello" or "Hi" in the description. "Jon" must inside either but "Harry" must not inside.

### Arguments

Run `python main.py -h` for details.

## Thanks

Thanks developers from [Douyin_TikTok_Download_API](https://github.com/Evil0ctal/Douyin_TikTok_Download_API#). This program uses some of its apis.
