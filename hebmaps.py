import typing as T
import re
import binascii as bn
import codecs
from pprint import pprint
from unicodedata import normalize
from hebrew import Hebrew
from hebrew.chars import HebrewChar

hebmap_dict = {}

with open("hebmaps.txt", 'r', encoding='utf-8') as hm:
    data = hm.readlines()
    for i, line in enumerate(data):
        lin = [j.strip() for j in line.split("|")]
        lin = [lin[-3].lower(), lin[-2].lower()]
        data[i] = ', '.join(lin) + '\n'

with open("hebmaps_edit.txt", 'w', encoding='utf-8') as hm:
    hm.writelines(data)

with open("hebmaps_edit.txt", 'r', encoding='utf-8') as hm:
    for i in hm:
        i = i.split(', ')
        hebmap_dict.update({i[0].strip() : i[1].strip()})


def to_heb(tl):
    res = ''
    for ltr in tl:
        if len(ltr) > 1:
            print(ltr)
        code = str(hex(ord(ltr)))
        code = code[2::]
        while len(code) < 4:
            code = '0' + code
        rc = hebmap_dict[code].split()
        hex_ints = [int('0x' + j, 16) for j in rc]
        for j in hex_ints:
            res += chr(j)
    res = ''.join(list(Hebrew(res).graphemes)[::-1])
    
    return res


