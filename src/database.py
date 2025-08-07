import pathlib
import sqlite3
import logging

def find_user(user_id: str, cur: sqlite3.Cursor, logger: logging.Logger) -> bool:
    try:
        cur.execute("SELECT EXISTS ( SELECT 1 FROM sqlite_master WHERE type='table' AND name=?)", (user_id,))
    except sqlite3.InterfaceError as e:
        logger.error(f"Database error (find_user_1): InterfaceError {e}")
    except sqlite3.DatabaseError as e:
        logger.error(f"Database error (find_user_1): DatabaseError {e}")
    else:
        if cur.fetchone()[0] == 1:
            logger.debug(f"Table \"{user_id}\" is already exist!")
            return True
        else:
            try:
                cur.execute(f"CREATE TABLE \"{user_id}\" ( aweme_id VARCHAR(30) PRIMARY KEY NOT NULL, filter BOOLEAN NOT NULL );")
            except sqlite3.InterfaceError as e:
                logger.error(f"Database error (find_user_2): InterfaceError {e}")
            except sqlite3.DatabaseError as e:
                logger.error(f"Database error (find_user_2): DatabaseError {e}")
            else:
                logger.debug(f"New table created: \"{user_id}\".")
                return False

def find_V(user_id: str, aweme_id: str, fit: bool, cur: sqlite3.Cursor, logger: logging.Logger) -> bool:
    try:
        cur.execute(f"SELECT aweme_id, filter FROM \"{user_id}\" WHERE aweme_id = ?;",(aweme_id,))
    except sqlite3.InterfaceError as e:
        logger.error(f"Database error: InterfaceError {e}")
    except sqlite3.DatabaseError as e:
        logger.error(f"Database error: DatabaseError {e}")
    else:
        rt=cur.fetchall()
        if len(rt) == 0:
            try:
                cur.execute(f"INSERT INTO \"{user_id}\" VALUES (?, ?);", (aweme_id, fit))
            except sqlite3.InterfaceError as e:
                logger.error(f"Database error: InterfaceError {e}")
            except sqlite3.DatabaseError as e:
                logger.error(f"Database error: DatabaseError {e}")
            else:
                logger.debug(f"Post {aweme_id} is not in the database.")
                return fit
        elif len(rt) == 1:
            if rt[0][1] == fit:
                logger.debug(f"Post {aweme_id} is already exist, skip the download.")
                return False
            elif fit:
                try:
                    cur.execute(f"UPDATE \"{user_id}\" SET filter = ? WHERE aweme_id = ?", (True, aweme_id)) 
                except sqlite3.InterfaceError as e:
                    logger.error(f"Database error: InterfaceError {e}")
                except sqlite3.DatabaseError as e:
                    logger.error(f"Database error: DatabaseError {e}")
                else:
                    logger.debug(f"Post {aweme_id} is in the database but not downloaded.(May because the filter has been changed) Video is now downloading...")
                    return True
            else:
                logger.info(f"Post {aweme_id} is downloaded but filtered out.")
                return False
        else:
            logger.error(f"Post {aweme_id} has been found more than once in the database.")
            return False