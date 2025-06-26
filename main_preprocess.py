import re
from itertools import chain, combinations
from treelib import Tree
from hebrew_text_processing import *
from hebrew import Hebrew
from numpy import sign
from models import CNode, Word, session
from hebmaps import to_heb
from wtm_word_process import strongest_code, accent_ranks, accents_by_code, get_agr, get_state, get_suffix
import graphviz
from treebuilder import flip

constituent_types = {0 : 'half_verse', 1 : '1rank', 2 : '2rank', 3 : '3rank', 4 : 'connectives', 5 : 'accentless'}

def powerset(li):
    return chain.from_iterable(combinations(li, r) for r in range(len(li)+1))

def powerlist(li):
    res = []
    for i in powerset(li):
        res.append(list(i))
    return res

def get_accent(li):
    if type(li) == list:
        return get_accent(li[-1])
    else:
        return li.accent_code

def get_id(li):
    if type(li) == list:
        return ' '.join([get_id(i) for i in li])
    else:
        return str(li.id)

def addchildren(constituent, const_id, tree, verse_index):
    for i in constituent:
        new_id = get_id(i)
        if type(i) == SubConst:
            i.add_repr(verse_index)
            tree.create_node(i.graphical, new_id, const_id, verse_index)
        else:
            acc_code = get_accent(i)
            tree.create_node(str(accent_ranks[acc_code]), new_id, const_id)
            addchildren(i, new_id, tree, verse_index)

def viewable_tree(title, verse_index, structure):
    tree = Tree()
    const_id = "HALF_VERSE"
    #print(const_id)
    #print(len(structure[0]))
    #for i in structure[0]:
        #print(get_id(i))
    tree.create_node(title, const_id)
    addchildren(structure, const_id, tree, verse_index)
    return tree

def tree_db(title, verse_index, structure, parsing):
    tree = Tree()
    #const_id = get_id(structure)
    #print(const_id)
    #print(len(structure[0]))
    #for i in structure[0]:
        #print(get_id(i))
    #tree.create_node(title, const_id)
    root = CNode(name=title, accent_rank=0)
    root.parsing = parsing
    session.add(root)
    addchildren_db(structure, verse_index, root, parsing)
    return tree

def addchildren_db(constituent, verse_index, mother, parsing):
    for i in constituent:
        acct = get_accent(i)
        #new_id = get_id(i)
        if type(i) == SubConst:
            i.add_repr(verse_index)
            #tree.create_node(i.graphical, new_id, const_id, verse_index)
            curr_node = CNode(name=i.graphical, accent_rank=accent_ranks[acct])
            curr_node.mother = mother
            curr_node.parsing = parsing

            for word in i:
                pos = word.pos
                lemma = word.form
                p_suffix = word.suffix
                agr = word.agr
                state = word.state
                verb_stem = word.stem
                tense_etc = word.vrb_m
                aram = word.aram
                word = Word(pos=pos, lemma=lemma)
                if aram:
                    word.aramaic = aram
                if p_suffix:
                    word.p_suffix = p_suffix
                if agr:
                    word.agr = agr
                if state:
                    word.state = state
                if verb_stem:
                    word.verb_stem = verb_stem
                if tense_etc:
                    word.tense_etc = tense_etc
                word.mother_node= curr_node

            session.add(curr_node)
        else:
            #acc_code = get_accent(i)
            #tree.create_node(accents_by_code[acc_code] + ' ' + str(accent_ranks[acc_code]), new_id, const_id)
            curr_node = CNode(name=accents_by_code[acct], accent_rank=accent_ranks[acct])
            curr_node.mother = mother
            curr_node.parsing = parsing
            session.add(curr_node)
            addchildren_db(i, verse_index, curr_node, parsing)


class Unit:
    def __init__(self, form, analysis, code, position):
        form = form.replace('-', ' ')
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
        if self.analysis[0] == '%':
            self.aram = True
        else:
            self.aram = False
        self.analysis = self.analysis[1:]         
        if self.analysis[0] == 'P':
            self.pos = self.analysis[1]
        else:
            self.pos = self.analysis[0]
            if self.pos == 'a':
                self.pos == 'adj'
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
        self.accent_code, self.paseq = strongest_code(code, 0)
        self.maqqef = self.analysis[-1] == '!'
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

class SubConst:
    def __init__(self, var, *tokens, lft=0, rgt=0):
        self.tokens = list(tokens)
        self.position = list(dict.fromkeys([i.position for i in self.tokens]))
        self.lft = lft
        self.rgt = rgt
        assert not self.tokens[-1].maqqef
        self.graphical = None
        self.id = 'SUB' + str(self.position[-1])
        self.forms = [i.form for i in self.tokens]
        self.accent_codes = [i.accent_code for i in self.tokens]
        self.accent_ranks = [i.accent_rank for i in self.tokens]
        if not var:    
            if self.tokens[-1].accent_rank == 5:
                for n, i in enumerate(self.accent_ranks):
                    if i != 5:
                        self.accent_code = self.accent_codes[n]
                    else: print(self.tokens)
                #assert 'j' in self.accent_codes
                #self.accent_code = 'j'
            else:
                self.accent_code = self.tokens[-1].accent_code
        else:
            #print(self.tokens[-1].accent_code)
            print(self.tokens)
            print(self.tokens[-1].accent_code)
            if self.tokens[-1].accent_code in 'wyz7ne6':
                self.accent_code = self.tokens[-1].accent_code + '+'
            else:
                self.accent_code = self.tokens[-1].accent_code
        assert self.accent_code != 'x'
        self.accent_rank = accent_ranks[self.accent_code]
        self.accent_name = accents_by_code[self.accent_code]
        self.dict_form = {'tokens' : self.tokens, 
                          'accent' : f'code: {self.accent_code}, name: {self.accent_name}, rank: {self.accent_rank}'}

    def __repr__(self):
        return str(self.dict_form)
    
    def __contains__(self, item):
        return item in self.tokens
    
    def __iter__(self):
        return iter(self.tokens)
    
    def __next__(self):
        return next(self.tokens)
    
    def add_repr(self, verse_index):
        m = 0
        for w in self.tokens:
            if w.maqqef:
                m += 1
        self.graphical = Book.text[verse_index].get_sub_line(self.position).replace('+', ' ')
        
        if m != 0:
            mg = self.graphical.count('־')
            #for w in self.tokens:
                #if w.analysis[:2] == 'np':
                    #if ' ' in w.form:
                        #if str(Hebrew(w.form).text_only()) in str(Hebrew(self.graphical).text_only()).replace():
                            #mg -= 1
            if mg != m:
                print(m)
                print(mg)
                print(self.graphical)
                print(self.tokens)
                print(Book.text[verse_index])
            assert mg >= m
        

class MinConst:
    def __init__(self, *tokens, lft=0, rgt=0):
        self.tokens = list(tokens)
        self.position = self.tokens[-1].position[-1]
        self.id = 'MIN' + str(self.position)
        #for i in tokens:
            #print(i.id)
        self.forms = [i.forms for i in self.tokens]
        self.accent_code = self.tokens[-1].accent_code
        self.accent_name = self.tokens[-1].accent_name
        self.accent_rank = self.tokens[-1].accent_rank
        #self.paseq = self.tokens[-1].paseq  
        assert self.accent_rank < 4
        self.dict_form = {'tokens' : self.tokens, 
                          'accent' : f'code: {self.accent_code}, name: {self.accent_name}, rank: {self.accent_rank}',}

    def __repr__(self):
        return str(self.dict_form)
    
    def __contains__(self, item):
        return item in self.tokens
    
    def __iter__(self):
        return iter(self.tokens)
    
    def __next__(self):
        return next(self.tokens)

class Constituent:
    def __init__(self, *tokens):
        self.tokens = list(tokens)
        self.forms = [i.forms for i in self.tokens]
        self.last_token = self.tokens[-1]
        self.accent_code = self.last_token.accent_code
        self.accent_name = self.last_token.accent_name
        self.accent_rank = self.last_token.accent_rank
        #self.paseq = self.tokens[-1].paseq
        self.rank_list = [word.accent_rank for word in tokens]
        assert min(self.rank_list) == self.rank_list[-1]
        self.nodes = []
        self.node = []
        self.indivisible = 0
        if len(self.tokens) == 1:
            self.indivisible = 1
        if not self.indivisible:
            self.first_sep = self.rank_list.index(min(self.rank_list[:-1]))
        self.dict_form = {'tokens' : self.tokens, 
                          'accent' : f'code: {self.accent_code}, name: {self.accent_name}, rank: {self.accent_rank}'}

    def split_into_nodes(self):
        if self.indivisible:
            self.nodes = self.tokens[0]
        else:
            self.node = Constituent(*(self.tokens[: self.first_sep + 1]))
            self.nodes = [self.node] 
            self.node = Constituent(*self.tokens[self.first_sep + 1 :])
            self.nodes.append(self.node)
            for n, node in enumerate(self.nodes):
                self.nodes[n] = node.split_into_nodes()
            
        return self.nodes

    def __repr__(self):
        return str(self.dict_form)
    
    def __contains__(self, item):
        return item in self.tokens

    def __iter__(self):
        return iter(self.tokens)
    
    def __next__(self):
        return next(self.tokens)

class HalfVerse:
    def __init__(self, *tokens):
        self.tokens = list(tokens)
        self.parsings = []
        self.vars = 1
        self.var_indices = []
        for n, token in enumerate(self.tokens):
            if token.paseq:
                self.parsings *= 2
                self.vars *= 2
                self.var_indices.append(n)

        if self.var_indices:
            #print([w.paseq for  w in self.tokens])
            #print([w.accent_code for w in self.tokens])
            #print(type(self.tokens))
            #print(self.var_indices)
            for i in powerlist(self.var_indices):
                self.parsings.append(pars_half_verse(self.tokens, i))
        else:
            self.parsings.append(pars_half_verse(self.tokens, self.var_indices))

    def __contains__(self, item):
        return item in self.tokens
    
    def __iter__(self):
        return iter(self.tokens)
    
    def __next__(self):
        return next(self.tokens)
        
class Book:
    text = None
    mqf_inds = None

    def __init__(self, hebrewlines):
        Book.mqf_inds = []
        Book.text = hebrewlines
        for i in hebrewlines:
            Book.mqf_inds.append([])
        
        

        #self.parsings.append(Constituent(*self.tokens).split_into_nodes()) #so we want the Constituent to operate on the level of units


def parse_analysis(analysis_str: str):
    merge_next = analysis_str[0] == "+"
    if merge_next:
        analysis_str = analysis_str[1:]

    analysis_str = analysis_str.strip("()")
    
    assert analysis_str[0]
    analysis_str = analysis_str[1:]         # consume `@` symbol, which always exists
    
    pos = analysis_str[0]
    # separate parsing for each part of speech

    cantillation_sign = re.search(r"Z(.+?)R", analysis_str).group(1)

    kethib = re.search(r"R(.+?)", analysis_str).group(1)[0] == 'k'

    maqqef = analysis_str[-2] == '!'

    analysis = {"pos": pos, "merge_next": merge_next, "accent": cantillation_sign, "maqqef" : maqqef, "kethib" : kethib}

    return analysis


def pars_half_verse(half_verse, var_indices):
    cur_sub_const = []
    subc_var_indices = []
    counter = 0
    sub_consts = [cur_sub_const]
    for n, word in enumerate(half_verse):
        cur_sub_const.append(word)
        if n in var_indices:
            subc_var_indices.append(counter)
        if word.merge_next == False:                                                                                                                                                                                                                                                                                                                            
            cur_sub_const = []
            sub_consts.append(cur_sub_const)
            counter += 1
    
    if not cur_sub_const:
        sub_consts.pop()
    
    for n, sub_const in enumerate(sub_consts):
        if n in subc_var_indices:
            #print(n)
            #print(subc_var_indices)
            #print(var_indices)
            #print(sub_const)
            sub_consts[n] = SubConst(1, *sub_const)
        else:
            sub_consts[n] = SubConst(0, *sub_const)
    
    cur_min_const = []
    min_consts = [cur_min_const]
    for sub_const in sub_consts:
        cur_min_const.append(sub_const)
        if sub_const.accent_rank < 4:
            cur_min_const = []
            min_consts.append(cur_min_const)
    
    if not cur_min_const:
        min_consts.pop()

    for n, min_const in enumerate(min_consts):
        min_consts[n] = MinConst(*min_const)

    structure = Constituent(*min_consts).split_into_nodes()

    return structure
    

def parse_verse(verse: str, verse_index):
    verse_title, content = re.split(" {2}", verse)
    words_strings = re.split("(?<=\)) ", content.strip())
    
    words = []
    graphic_counter = 0
    for word in words_strings:
        form, analysis = word.split()[:-1], word.split()[-1]
        if type(form) == list:
            form = ' '.join(form)
        #print("form:", form, "analysis:", analysis)
        
        parsed_analysis = parse_analysis(analysis)
        if not parsed_analysis["kethib"]:      
            word_data = {"form": form, **parsed_analysis, "_analysis": analysis}
            if not analysis[2] in 'xk':  #get rid of parapgraph markers, which aren't words but are coded as such
                words.append(word_data)
    #paragraph_marker = 0
    #paragraph_marker_index = []
    graphic_counter = 0
    for n, word in enumerate(words):
        code = re.search(r"Z(.+?)R", word['_analysis']).group(1)
        words[n] = Unit(word['form'], word['_analysis'], code, graphic_counter)
        if n + 1 == len(words):
            words[n] = Unit(word['form'], word['_analysis'], '9', graphic_counter)
        if not word['merge_next']:
            graphic_counter += 1
        #else:
            #paragraph_marker_index.append(n)
            #paragraph_marker += 1
    
    #if paragraph_marker:
        #for n in paragraph_marker_index[::-1]:
            #words.pop(n)

    # split into half-verses
    cur_half_verse = []
    half_verses = [cur_half_verse]
    for enum, word in enumerate(words):
        cur_half_verse.append(word)
        if type(word) != Unit:
            print(word)
        if word.accent_code == "5" and enum != len(words) - 1:
            cur_half_verse = []
            half_verses.append(cur_half_verse)
        
    #assert len(half_verses) <= 2
    #pprint(half_verses, indent=4)
    
    structures = []
    c = 0
    for half_verse in half_verses:
        structure = HalfVerse(*half_verse).parsings
        if len(half_verses) > 1:
            a = 0
            #print(verse_title + 'abc'[c])
        else:
            a = 0
            #print(verse_title)
        if len(structure) == 1:
            a = 0
            #print(structure[0])
        else:
            for i in range(len(structure)):
                a = 0
                #print(f'parsing variant {i + 1} :')
                #print(structure[i])
        structures.append(structure)
        c += 1
    
    return verse_title, structures

