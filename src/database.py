import sqlite3
import logging
from src.align_unicode import align_unicode as align
from src.post import poster
from src.align_unicode import align_address

def init(cur: sqlite3.Cursor, logger: logging.Logger):
    try:
        cur.execute("""CREATE TABLE \"All_Users\" (
                    user_id VARCHAR(30) PRIMARY KEY NOT NULL,
                    alias VARCHAR(30) NOT NULL,
                    nickname VARCHAR(30) NOT NULL,
                    unique_id VARCHAR(30) NOT NULL,
                    gender INT,
                    age INT,
                    address VARCHAR(30),
                    school VARCHAR(30),
                    IP VARCHAR(30) NOT NULL,
                    Signature VARCHAR(300)
                    );""")
    except sqlite3.InterfaceError as e:
        logger.error(f"Database error (init): InterfaceError {e}")
    except sqlite3.DatabaseError as e:
        logger.error(f"Database error (init): DatabaseError {e}")
    else:
        logger.debug(f"Database init done!")

def find_user(U: poster, nickname: str, cur: sqlite3.Cursor, logger: logging.Logger) -> list:
    try:
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?;", ("All_Users",))
    except sqlite3.InterfaceError as e:
        logger.error(f"Database error (find_user_0): InterfaceError {e}")
    except sqlite3.DatabaseError as e:
        logger.error(f"Database error (find_user_0): DatabaseError {e}")
    else:
        if cur.fetchone() is None:
            init(cur, logger)
    try:
        cur.execute("SELECT * FROM \"All_Users\" WHERE user_id=?;", (U.user_id,))
    except sqlite3.InterfaceError as e:
        logger.error(f"Database error (find_user_1): InterfaceError {e}")
    except sqlite3.DatabaseError as e:
        logger.error(f"Database error (find_user_1): DatabaseError {e}")
    else:
        rtn = cur.fetchone()
        if rtn:
            logger.debug(f"Table \"{U.user_id}\" is already exist!")
        else:
            try:
                cur.execute(f"""CREATE TABLE \"{U.user_id}\"(
                            aweme_id VARCHAR(30) PRIMARY KEY NOT NULL,
                            filter BOOLEAN NOT NULL,
                            exist BOOLEAN NOT NULL);""")
            except sqlite3.InterfaceError as e:
                logger.error(f"Database error (find_user_2): InterfaceError {e}")
            except sqlite3.DatabaseError as e:
                logger.error(f"Database error (find_user_2): DatabaseError {e}")
            else:
                logger.debug(f"New table created: {align(nickname, 20, False)} {U.user_id}.")
            try:
                cur.execute("INSERT INTO \"All_Users\" VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",(
                    U.user_id,
                    nickname,
                    U.nickname,
                    U.unique_id,
                    U.gender,
                    U.age,
                    align_address(U.country, U.province, U.city),
                    U.school,
                    U.ip,
                    U.signature,))
            except sqlite3.InterfaceError as e:
                logger.error(f"Database error (find_user_2): InterfaceError {e}")
            except sqlite3.DatabaseError as e:
                logger.error(f"Database error (find_user_2): DatabaseError {e}")
        return rtn

def update_user(user_id: str, col: str, value, cur:sqlite3.Cursor, logger:logging.Logger):
    try:
        cur.execute(f"UPDATE \"All_Users\" SET {col} = ? WHERE user_id = ?;",(value, user_id,))
    except sqlite3.InterfaceError as e:
        logger.error(f"Database error (update_user): InterfaceError {e}")
    except sqlite3.DatabaseError as e:
        logger.error(f"Database error (update_user): DatabaseError {e}")
    else:
        logger.debug(f"Update user profile success: {user_id} {col} {value}")

def find_V(user_id: str, aweme_id: str, fit: bool, cur: sqlite3.Cursor, logger: logging.Logger) -> int:
    """
    Determines the status of a video post in the database.

    Returns:
        0: No need to download (already exists or filtered out).
        1: Need to download (not in database or needs re-download).
        2: Retry download (previous download failed).
        -1: Error (multiple entries found).
    """
    try:
        cur.execute(f"SELECT * FROM \"{user_id}\" WHERE aweme_id = ?;",(aweme_id,))
    except sqlite3.InterfaceError as e:
        logger.error(f"Database error: (find_V_1) InterfaceError {e}")
    except sqlite3.DatabaseError as e:
        logger.error(f"Database error: (find_V_1) DatabaseError {e}")
    else:
        rt=cur.fetchall()
        if len(rt) == 0:
            try:
                cur.execute(f"INSERT INTO \"{user_id}\" VALUES (?, ?, ?);", (aweme_id, fit, False))
            except sqlite3.InterfaceError as e:
                logger.error(f"Database error: (find_V_2) InterfaceError {e}")
            except sqlite3.DatabaseError as e:
                logger.error(f"Database error: (find_V_2) DatabaseError {e}")
            else:
                logger.debug(f"Post {aweme_id} is not in the database.")
                return int(fit)
        elif len(rt) == 1:
            if rt[0][2]:
                logger.debug(f"Post {aweme_id} is already exist, skip the download.")
                return 0
            elif fit:
                if rt[0][1] == fit:
                    logger.info(f"Post {aweme_id} has been downloaded but failed. Retrying...")
                    return 2
                else:
                    try:
                        cur.execute(f"UPDATE \"{user_id}\" SET filter = ? WHERE aweme_id = ?", (True, aweme_id)) 
                    except sqlite3.InterfaceError as e:
                        logger.error(f"Database error: (find_V_3) InterfaceError {e}")
                    except sqlite3.DatabaseError as e:
                        logger.error(f"Database error: (find_V_3) DatabaseError {e}")
                    else:
                        logger.debug(f"Post {aweme_id} is in the database but not downloaded.(May because last download failed or the change of the filter) Video is now downloading...")
                        return 1
            else:
                logger.info(f"Post {aweme_id} is downloaded but filtered out.")
                return 0
        else:
            logger.error(f"Post {aweme_id} has been found more than once in the database.")
            return -1

def download_V(user_id: str, aweme_id: str, cur: sqlite3.Cursor, logger: logging.Logger):
    try:
        cur.execute(f"UPDATE \"{user_id}\" SET exist = ? WHERE aweme_id = ?;", (True, aweme_id))
    except sqlite3.InterfaceError as e:
        logger.error(f"Database error: (download_V) InterfaceError {e}")
    except sqlite3.DatabaseError as e:
        logger.error(f"Database error: (download_V) DatabaseError {e}")

def erase_user(user_id: str, cur: sqlite3.Cursor, logger: logging.Logger):
    try:
        cur.execute(f"DROP TABLE IF EXISTS \"{user_id}\";")
    except sqlite3.InterfaceError as e:
        logger.error(f"Database error: (erase_user) InterfaceError {e}")
    except sqlite3.DatabaseError as e:
        logger.error(f"Database error: (erase_user) DatabaseError {e}")

def execute(cmd: str, cur: sqlite3.Cursor, logger: logging.Logger):
    try:
        cur.execute(cmd)
    except sqlite3.InterfaceError as e:
        logger.error(f"Database error: (execute) InterfaceError {e}")
        return False
    except sqlite3.DatabaseError as e:
        logger.error(f"Database error: (execute) DatabaseError {e}")
        return False
    else:
        return cur.fetchall()