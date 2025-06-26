from hebrew import Hebrew
import re
import typing as T

def readable(hebstr):
    return ''.join(list(Hebrew(hebstr).graphemes)[::-1])

emp_set = 0xd8.to_bytes()
pn_sep = b'\xc2\x83'

class HebrewLine:
    def __init__(self, title, words):
        self.title = title
        self.words = words
    
    def get_sub_line(self, positions):
        #print(hebrewlines)

        #print(positions)
        #for i in positions:
            #if i >= len(self.words):
                #print(self.words)    
        res = ' '.join([self.words[i] for i in positions])
        return res
    
    def __repr__(self):
        return self.title + ' ' + ' '.join([readable(j) for j in self.words[2:]])

def wtt_proc(bookname):
    hebrewlines = []
    filename = f"wtt\\wtt{bookname.upper()}.txt"
    with open(filename, 'rb') as g:
        data = g.readlines()
        print(type(data))
        for num, line in enumerate(data):
            if pn_sep in line:
                print(line)
            data[num] = line.replace(pn_sep, b'+')
    with open(filename, 'wb') as g:
        g.writelines(data)
    with open(filename, encoding='utf-8') as g:
        for i, line in enumerate(g):
            outp = line.strip().replace('Ø', '')
            outp = outp.replace('( ]', '(]').replace('( )', '()')
            outp = outp.replace(']קק[', '').replace('[', '').replace(']', '')
            outp = re.sub(r"\)(.+?)\(", '', outp).split()
            outp = [w for w in outp if not w in ['ס', 'פ']]
            hebrewlines.append(HebrewLine(' '.join(outp[:2]), [j for j in outp[2:]])) #delete readable() before exporting
        
    return hebrewlines

def wtt_line_proc(bookname, n, mqf_inds=[]):
    filename = f"wtt{bookname.upper()}.txt"
    with open(filename, encoding='utf-8') as g:
        for i, line in enumerate(g):
            if i == n:
                outp = line.strip().replace('Ø', '').replace('[', '').replace(']', '').split()
                for ind in mqf_inds[::-1]:
                    if not '־' in outp[ind]:
                        outp[ind+2] += '־' + outp[ind+1+2]
                    else:
                        mqf_inds.pop(ind)
                for ind in mqf_inds[::-1]:
                    outp.pop(ind+2)
                for en, word in enumerate(outp):
                    if word[0] == ')' and word[-1] == '(':
                        #print(word)
                        outp.pop(en)
                        word = ''
                    elif ')' in word:
                        #print(i)
                        #print(outp[:2])
                        if word[-1] != '(':
                            outp[en] = re.sub(r"\)(.+?)\(", '', word)
                            outp[en] = outp[en].replace(')', '').replace('(', '')
                        else:
                            outp[en] = re.sub(r"\)(.+?)\(", outp[en + 1], word)
                            outp[en + 1] = ')' + outp[en + 1][1:-1] + '('

                for ch in 'ספ':
                    if ch in outp:
                        outp.pop(outp.index(ch))

    return HebrewLine(' '.join(outp[:2]), [j for j in outp[2:]]) 
