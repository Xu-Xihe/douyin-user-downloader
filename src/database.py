import sqlite3
import logging
import sys
import pathlib
from src.align_unicode import align_unicode as align
from src.post import poster
from src.align_unicode import align_address

class database:
    # Value
    _path = pathlib.Path(__file__).parent.parent / "data" / "downloaded.db"
    _enable = None
    _database = None
    _logger = None
    cursor = None

    # Logger
    @classmethod
    def lg_error(cls, message: str):
        if cls._enable:
            cls._logger.error(message)
    @classmethod
    def lg_debug(cls, message: str):
        if cls._enable:
            cls._logger.debug(message)
    @classmethod
    def lg_info(cls, message: str):
        if cls._enable:
            cls._logger.info(message)
    
    # init
    def __new__(cls, enable: bool, logger: logging.Logger):
        # Value
        cls._logger = logger
        cls._enable = enable

        # Connect to database
        try:
            cls._database = sqlite3.connect(str(cls._path.resolve()))
        except Exception as e:
                cls.lg_error(f"Connect to database failed: {e}")
                if cls._enable:
                    sys.exit(1)
        else:
            cls.cursor = cls._database.cursor()
            cls.lg_debug("Successfully connected to database.")

        # All_Users table check
        try:
            cls.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?;", ("All_Users",))
        except Exception as e:
            cls.lg_error(f"Database error: {e}")
        else:
            if cls.cursor.fetchone() is None:
                try:
                    cls.cursor.execute("""CREATE TABLE \"All_Users\" (
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
                except Exception as e:
                    cls.lg_error(f"Database error: {e}")
                else:
                    cls.lg_debug(f"Database init done!")
                    cls._database.commit()
        return super().__new__(cls)

    # Commit
    @classmethod
    def commit(cls):
        if cls._enable:
            cls._database.commit()
        else:
            cls._database.rollback()

    # Check user
    @classmethod
    def find_user(cls, U: poster, nickname: str) -> list:
        try:
            cls.cursor.execute("SELECT * FROM \"All_Users\" WHERE user_id=?;", (U.user_id,))
        except Exception as e:
            cls.lg_error(f"Database error: {e}")
            return []
        else:
            rtn = cls.cursor.fetchone()
            if rtn:
                cls.lg_debug(f"Table \"{U.user_id}\" is already exist!")
            else:
                try:
                    cls.cursor.execute(f"""CREATE TABLE \"{U.user_id}\"(
                                aweme_id VARCHAR(30) PRIMARY KEY NOT NULL,
                                filter BOOLEAN NOT NULL,
                                exist BOOLEAN NOT NULL);""")
                except Exception as e:
                    cls.lg_error(f"Database error: {e}")
                else:
                    cls.lg_debug(f"New table created: {align(nickname, 20, False)} {U.user_id}.")
                try:
                    cls.cursor.execute("INSERT INTO \"All_Users\" VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",(
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
                except Exception as e:
                    cls.lg_error(f"Database error: {e}")
                else:
                    cls._database.commit()
            return rtn

    # Update user info
    @classmethod
    def update_user(cls, user_id: str, col: str, value):
        try:
            cls.cursor.execute(f"UPDATE \"All_Users\" SET {col} = ? WHERE user_id = ?;",(value, user_id,))
        except Exception as e:
            cls.lg_error(f"Database error: {e}")
        else:
            cls._database.commit()
            cls.lg_debug(f"Update user profile success: {user_id} {col} {value}")

    # Find Video
    @classmethod
    def find_V(cls, user_id: str, aweme_id: str, fit: bool) -> int:
        """
        Determines the status of a video post in the database.

        Returns:
            0: No need to download (already exists or filtered out).
            1: Need to download (not in database or needs download).
            2: Retry download (previous download failed).
            -1: Error (multiple entries found).
        """
        try:
            cls.cursor.execute(f"SELECT * FROM \"{user_id}\" WHERE aweme_id = ?;",(aweme_id,))
        except Exception as e:
            cls.lg_error(f"Database error: {e}")
        else:
            rt=cls.cursor.fetchall()
            if len(rt) == 0: # Video not in database
                try:
                    cls.cursor.execute(f"INSERT INTO \"{user_id}\" VALUES (?, ?, ?);", (aweme_id, fit, False))
                except Exception as e:
                    cls.lg_error(f"Database error: {e}")
                else:
                    cls.lg_debug(f"Post {aweme_id} is not in the database.")
                    ans = int(fit)
            elif len(rt) == 1: # Video find in database
                if rt[0][2]: # exist = True
                    if not fit:
                        cls.lg_info(f"Post {aweme_id} is downloaded but filtered out.")
                    else:
                        cls.lg_debug(f"Post {aweme_id} is already exist, skip the download.")
                    ans = 0
                elif fit: # exist = False but filter = True
                    if rt[0][1] == fit: # filter = need_download = True
                        cls.lg_info(f"Post {aweme_id} has been downloaded but failed. Retrying...")
                        ans = 2
                    else:
                        try:
                            cls.cursor.execute(f"UPDATE \"{user_id}\" SET filter = ? WHERE aweme_id = ?", (True, aweme_id)) 
                        except Exception as e:
                            cls.lg_error(f"Database error: (find_V_3) InterfaceError {e}")
                        else:
                            cls.lg_debug(f"Post {aweme_id} is in the database but not downloaded.(May because last download failed or the change of the filter) Video is now downloading...")
                            ans = 1
                else:
                    cls.lg_debug(f"Post {aweme_id} is filtered out. Skip download.")
                    ans = 0
            else:
                cls.lg_error(f"Post {aweme_id} has been found more than once in the database.")
                ans = -1
            cls.commit()
            return ans

    # Record Video download done
    @classmethod
    def download_V(cls, user_id: str, aweme_id: str):
        try:
            cls.cursor.execute(f"UPDATE \"{user_id}\" SET exist = ? WHERE aweme_id = ?;", (True, aweme_id))
        except Exception as e:
            cls.lg_error(f"Database error: {e}")
        else:
            cls.commit()

    # Delete user from database
    @classmethod
    def erase_user(cls, user_id: str):
        try:
            cls.cursor.execute(f"DROP TABLE IF EXISTS \"{user_id}\";")
            cls.cursor.execute("DELETE FROM \"All_Users\" WHERE user_id = ?", (user_id,))
        except Exception as e:
            cls.lg_error(f"Database error: {e}")
        else:
            cls._logger.info(f"Delete database: {user_id}")
            print(f"Delete database: {user_id}")
            cls._database.commit()

    # Execute custom command to database
    @classmethod
    def execute(cls, cmd: str):
        try:
            cls.cursor.execute(cmd)
        except Exception as e:
            cls.lg_error(f"Database error: {e}")
            return False
        else:
            cls._database.commit()
            return cls.cursor.fetchall()
    
    # Close the database
    def close(self):
        self.cursor.close()
        self.commit()
        self._database.close()