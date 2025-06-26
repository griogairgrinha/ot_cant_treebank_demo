import re

from hebmaps import to_heb

accent_ranks = {'x' : 5, '3' : 5, '2' : 5, '8' : 5}
for n, codes in enumerate([['5', '9', '99'], ['a', '%', 'q', 'v', '0'], ['b', 'c', 'dc', 'd', 'g', '4', 'r'], ['l', 'm', 't', 'u', 'j', '&', '#', 'w+', 'y+',
                                                                                                     'z+', '7+', 'e+', '6+'],
                ['1', 'w', 'y', 'z', '7', 'n', 'e', '6', '`']]):
    for code in codes:
        accent_ranks.update({code : n})

accents_by_code = {'x' : 'no_accent',
                   '3' : 'no_accent',
                   '2' : 'no_accent', 
                   '8' : 'no_accent',
                   '1' : 'Munah',
                   'w' : 'Mahpak',
                   'y' : 'Mereka',
                   'z' : 'Mereka_Kepula',
                   'n' : 'Azla',
                   'e' : 'Telisha_parv',
                   '6' : 'Galgal',
                   '7' : 'Darga',
                   'l' : 'Geresh',
                   'm' : 'Garshayim',
                   't' : 'Pazer',
                   'u' : 'Pazer_magn',
                   'j' : 'Telisha_magn',
                   '&' : 'Munah_Legarmeh',
                   'b' : 'Zarqa',
                   'c' : 'Pashta',
                   'dc' : 'Pashta_dupl',
                   'd' : 'Pashta',
                   'g' : 'Yetib',
                   '4' : 'Tebir',
                   'r' : 'Rebia',
                   'a' : 'Segolta',
                   '%' : 'Shalshelet',
                   'q' : 'Zaqep_parv',
                   'v' : 'Zaqep_magn',
                   '0' : 'Tipha',
                   '5' : 'Atnah',
                   '9' : 'Sop_pasuq',
                   'w+' : 'Mahpak+paseq',
                   'y+' : 'Mereka+paseq',
                   'z+' : 'Mereka_Kepula+paseq',
                   '7+' : 'Darga+paseq',
                   '#' : 'Azla_Legarmeh',
                   'e+' : 'Telisha_parv+paseq',
                   '6+' : 'Galgal+paseq',
                   '`' : 'unidentified_connective'}

def get_agr(analysis):
    if analysis[0] in 'nu':
        return analysis[2:4]
    elif analysis[0] == 'a':
        return analysis[1:3]
    elif analysis[0] == 'v':
        if analysis[2] in 'vPs':
            return analysis[3:5]
        elif not analysis[2] in 'ca':
            return analysis[3:6]
    else:
        return None
    
def get_state(analysis):
    frm = analysis.split('+')[0]
    if frm[0] in 'nu':
        if len(frm) == 5:
            return frm[-1]
        else:
            return '?'
    elif frm[0] == 'a':
        if len(frm) == 4:
            return frm[-1]
        else:
            return '?'
    elif frm[0] == 'v' and frm[2] in 'Ps':
        if len(frm) == 6:
            return frm[-1]
        else:
            return '?'
    
def get_suffix(analysis):
    suffix = re.search(r'S(.{3})', analysis).group(1)
    suffix = suffix.strip('x')
    if suffix:
        #print(suffix)
        return suffix
    else:
        return None

def strongest_code(code, paseq):
    for sym in '23C-':
        code = code.replace(sym, '')
    code = code.replace('Ae', 'e')
    if len(code) == 0:
        code = 'x'
    code = ''.join(list(dict.fromkeys(code)))
    if 'd' in code and 'c' in code:
        code = code.replace('c', '')
    if 'f' in code:
        if 'p' in code:
            code = code.replace('f', '').replace('p', '%')
        elif 'n' in code:
            code = code.replace('f', '').replace('n', '#')
        elif '1' in code:
            code = code.replace('f', '').replace('1', '&')
        else:
            code = code.replace('f', '')
            paseq += 1
    if len(code) == 1:
        return code, paseq
    print(code)
    codes = code
    cd0 = codes[0]
    for cd in codes:
        if accent_ranks[cd] < accent_ranks[cd0]:
            cd0 = cd
    return cd0, paseq

paseq = 0
print(strongest_code('y', paseq))

class Unit:
    def __init__(self, form, analysis, code, position):
        if ' ' in form:
            self.form = form.split(' ')
            self.form = ' '.join([to_heb(part) for part in self.form][::-1])
        else:
            self.form = to_heb(form)
        self.position = position
        self.analysis = analysis
        self.merge_next = analysis[0] == "+"
        if self.merge_next:
            self.analysis = self.analysis[1:]

        self.analysis = self.analysis.strip("()")
        
        assert self.analysis[0]
        self.analysis = self.analysis[1:]         # consume `@` symbol, which always exists
        if self.analysis[0] == 'P':
            self.pos = self.analysis[1]
        else:
            self.pos = self.analysis[0]
        self.agr = get_agr(self.analysis)
        self.state = get_state(self.analysis)
        if self.pos == 'v':
            self.stem = self.analysis[1]
            self.vrb_m = self.analysis[2]
            if 'J' in self.analysis:
                if re.search(r"J(.?)", self.analysis).group(1) != 'x':
                    self.vrb_m = 'j' + re.search(r"J(.?)", self.analysis).group(1)
        else:
            self.stem = None
            self.vrb_m = None
        #for letter in 'JCAEHN':
            #if letter in self.analysis:
        self.suffix = get_suffix(self.analysis)
        self.accent_code, self.paseq = strongest_code(code, paseq)
        self.maqqef = self.analysis[-2] == '!'
        self.accent_rank = accent_ranks[self.accent_code]
        self.accent_name = accents_by_code[self.accent_code]
        self.dict_form = {'form' : self.form,
                #'analysis' : self.analysis,
                #'pos' : self.pos,
                'merge_next' : self.merge_next,
                #'maqqef' : self.maqqef
                }

    def __repr__(self):
        return str(self.dict_form)
    
