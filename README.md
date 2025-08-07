<h1 align="center">Douyin-User-Downloader</h1>

<div align="center">
A tool for downloading the user(s) post from Douyin. </center>
</div>

<br/>

<div align="center">
<img alt="GitHub License" src="https://img.shields.io/github/license/Xu-Xihe/douyin-user-downloader">
<img alt="GitHub last commit" src="https://img.shields.io/github/last-commit/Xu-Xihe/douyin-user-downloader">
<img alt="GitHub Release" src="https://img.shields.io/github/v/release/Xu-Xihe/douyin-user-downloader">
<img alt="GitHub repo size" src="https://img.shields.io/github/repo-size/Xu-Xihe/douyin-user-downloader">
<img alt="GitHub Issues or Pull Requests" src="https://img.shields.io/github/issues/Xu-Xihe/douyin-user-downloader">
<img alt="GitHub Issues or Pull Requests" src="https://img.shields.io/github/issues-closed/Xu-Xihe/douyin-user-downloader">
<br>
<img alt="GitHub watchers" src="https://img.shields.io/github/watchers/Xu-Xihe/douyin-user-downloader">
<img alt="GitHub forks" src="https://img.shields.io/github/forks/Xu-Xihe/douyin-user-downloader">
<img alt="GitHub Repo stars" src="https://img.shields.io/github/stars/Xu-Xihe/douyin-user-downloader">
<br>
<img alt="Python Version from PEP 621 TOML" src="https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2Fnumpy%2Fnumpy%2Fmain%2Fpyproject.toml">
</div>

## 0 Core Features

### Fully Content Support!

- Video: Support for high quality video download with no watermark

- Photos: Support for packaging download albums, also without watermark. Even the photos that not allowed to download from the app.

- LIVE Photos: Amazing improvement! Now LIVE Photos can be downloaded as `.mp4` files. The mix posts(contain both live and static pics) are also supported.

- User profiles(In dev): Nickname, IP location..... Everything you want!

### Flexible Configuration

-  Separate Configuration: Users are configured separately, easier for configing path, alias and filters!
- Filters: Two models filters are supported, convient for downloading part of one user's posts.
- Increase download: Using database, only download update posts.
- Folders separation: Auto make dir for a post if the num of the works inside is above the limit.

## 1 Get start!

### Python

Please go to [python.org](https://www.python.org/downloads/) and download the proper package for your system.

> [!CAUTION]
>
> Make sure your python version is **>=3.11**.

### Clone the repo

```bash
git clone --recurse-submodules https://github.com/Xu-Xihe/douyin-user-downloader.git
```

### Install requirements

```bash
pip install -r requirements.txt
```

### Run the program

```bash
python3 main.py
```

or

```bash
python main.py
```

## 2 Configuration

### Base URL

Although it will be replaced finally, but at least not now.

You need to set up the server of [Douyin_TikTok_Download_API](https://github.com/Evil0ctal/Douyin_TikTok_Download_API#) and fill in the url in the config file.

> [!NOTE]
>
> This will be solved in the future versions.

### Fetch Cookie

The program needs cookie to avoid api rick management. Please follow the step to get your cookie.

1. Open the browser and visit [doyin_web](https://www.douyin.com/).
2. Sign in your account.
3. Open the developer tools of your browser.
4. Go to the Network page and select the filter `XHR/Fetch.`
5. Your will find the cookie string at the `Headers` of some files. Copy it and fill in the `config.json`.

> [!WARNING]
>
> If the downloads continue failed, please refresh cookie first!

### Edit the config file

```json
{
    // Replace this url with your own server
    "base_url": "https://douyin.wtf",
    // Enable the database for increasing update
    "database": true,
    //default download path
    "default_path": "~/Downloads",
    //date formate
    "date_format": "%Y-%m-%d",
    //The length of description of the video in the file name
    "desc_length": 15,
    //Retry times when failed
    "retry": 3,
    //Seconds between each try
    "retry_sec": 3,
    //Users to download
    "users": [
        {
            //The url of the user's home page. Example:
            //"https://www.douyin.com/user/xxx" or "https://v.douyin.com/xxx"
            "url": "",
            //The folder name of this user, empty for default nickname
            "nickname": "",
            //The save path for this user, empty for "default_path"
            "path": "",
            //If the post files is more or equal to this num, they will be put in a separate folder
            "separate_limit": 2,
            //Make new folder in the path for download
            // True
            // user
            //     - 2022-11-28 13:09 xxx.mp4
            //     - 2022-11-28 13:09 xxx.mp4
            // False
            // 2022-11-28 13:09 xxx.mp4
            // 2022-11-28 13:09 xxx.mp4
            "new_folder": true,
            //True
            //Only download the videos which description contains the key_filter
            //False
            //Only download the videos which description dose not contain the key_filter
            "key_filter": "",
            "key_include": true
        } //,
    ],
    // Required
    "cookie": ""
}
```

## API Repo

Thanks developers from [Douyin_TikTok_Download_API](https://github.com/Evil0ctal/Douyin_TikTok_Download_API#). This program uses some of its apis.
