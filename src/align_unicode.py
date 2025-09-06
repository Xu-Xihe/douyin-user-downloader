#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from wcwidth import wcwidth
import emoji

def display_width(s: str) -> int:
    """
    Calculate the total width of the string based on the terminal's emoji width.
    """
    width = 0
    for ch in s:
        if emoji.is_emoji(ch):
            width += 2
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
    space_count = max(width - int(text_width), 0)
    return (" " * space_count + text) if align_right else (text + " " * space_count)

def align_address(country: str, province: str, city: str) -> str:
    rtn = country if country else ""
    if province and country:
        rtn += '-' + province
    else:
        rtn += province if province else ""
    if rtn and city:
        rtn += '-' + city
    else:
        rtn += city if city else ""
    if rtn:
        return rtn
    else:
        return "Unknown"

if __name__ == "__main__":
    s1 = "你好abc"
    s2 = "🚀rocket"
    s3 = "😄😄abc"

    print(f"'{align_unicode(s1, 12, False)}'")  # Left aligned
    print(f"'{align_unicode(s1, 12, True)}'")   # Right aligned
    print(f"'{align_unicode(s2, 12, False)}'")  # Left aligned
    print(f"'{align_unicode(s3, 12, True)}'")   # Right aligned