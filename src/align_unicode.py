#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import termios
import tty
from wcwidth import wcwidth
import shutil
import emoji

def get_cursor_position():
    """
    Query the current cursor position in the terminal.
    Returns (row, col) as integers.
    """
    buf = ""
    sys.stdout.write("\033[6n")
    sys.stdout.flush()
    while True:
        ch = sys.stdin.read(1)
        buf += ch
        if ch == "R":
            break
    try:
        # Response looks like: ESC[row;colR
        _, rowcol = buf.split("[", 1)
        row, col = rowcol[:-1].split(";")
        return int(row), int(col)
    except:
        return None, None

def detect_emoji_width(ch):
    """
    Measure the width of a single emoji in the current terminal.
    This is done once during initialization.
    """
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)  # Put stdin in cbreak mode
        sys.stdout.write("\0337")  # Save cursor position
        sys.stdout.flush()

        # Get starting column
        _, col_start = get_cursor_position()

        # Print character
        sys.stdout.write(ch)
        sys.stdout.flush()

        # Get ending column
        _, col_end = get_cursor_position()

        # Restore cursor position
        sys.stdout.write("\0338")  # Restore cursor position
        sys.stdout.flush()

        if col_start is not None and col_end is not None:
            width = col_end - col_start
            if width <= 0:  # Wrapped to next line
                width += get_terminal_columns()
            return width
        else:
            return 1
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def get_terminal_columns():
    """Return terminal column count."""
    return shutil.get_terminal_size().columns

# Initialize and detect emoji width
EMOJI_TEST_CHAR = "🚀"
EMOJI_WIDTH = detect_emoji_width(EMOJI_TEST_CHAR)

def display_width(s: str) -> int:
    """
    Calculate the total width of the string based on the terminal's emoji width.
    """
    width = 0
    for ch in s:
        if emoji.is_emoji(ch):
            width += EMOJI_WIDTH
        else:
            width += wcwidth(ch)
    return width

def align_unicode(text: str, width: int, align_right: bool) -> str:
    """
    Align the input text to the specified width.
    :param text: Input string (can contain CJK, emoji, etc.)
    :param width: Desired width to align to
    :param align_right: True for right alignment, False for left alignment
    :return: Aligned string with spaces
    """
    text_width = display_width(text)
    space_count = max(width - text_width, 0)
    return (" " * space_count + text) if align_right else (text + " " * space_count)

if __name__ == "__main__":
    s1 = "你好abc"
    s2 = "🚀rocket"
    s3 = "😄😄abc"

    print(f"'{align_unicode(s1, 12, False)}'")  # Left aligned
    print(f"'{align_unicode(s1, 12, True)}'")   # Right aligned
    print(f"'{align_unicode(s2, 12, False)}'")  # Left aligned
    print(f"'{align_unicode(s3, 12, True)}'")   # Right aligned