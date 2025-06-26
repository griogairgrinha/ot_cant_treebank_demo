from numpy import sign
from hebrew_text_processing import wtt_proc, emp_set
from main_preprocess import parse_verse, viewable_tree, Book, tree_db
from treebuilder import flip, style
from models import Parsing, session, CNode
from pathlib import Path


pn_sep = 0x83.to_bytes()

booklist = ['gen', 'exo', 'lev', 'num', 'deu', 'jos',
             'jdg', '1sa', '2sa', '1ki', '2ki', 'isa',
               'jer', 'eze', 'hos', 'joe', 'amo', 'oba',
                'jon', 'mic', 'nah', 'hab', 'zep', 'hag',
                 'zec', 'mal', 'job', 'rut', 'sol', 'ecc',
                  'lam', 'est', 'dan', 'ezr', 'neh', '1ch',
                   '2ch']

make_viz = 1
populate = 1

for bookname in booklist:
    filename = f"wtm\\wtm{bookname.upper()}.txt"
    Path(f"resgvs/{bookname.lower()}").mkdir(parents=True, exist_ok=True)
    with open(filename, "rb") as f:
        hebrewlines = Book(wtt_proc(bookname))
        for i, line in enumerate(f):
            if 1:
                print(i)
                line = line.replace(pn_sep, b' ').replace(emp_set, b'')
                s_line = line.decode("utf-8")
                title, s = parse_verse(s_line, i)
                print(title)
                for k, j in enumerate(s):
                    for n, q in enumerate(j):
                        ftitle = title.replace(' ', '').replace(':', '-') + ('abc'[k] * sign(len(s) - 1)) + (('_' + str(n+1) + 'p') * sign(len(j) - 1))
                        ttitle = title + ('abc'[k] * sign(len(s) - 1)) + ((', ' + str(n+1) + ' parsing') * sign(len(j) - 1))
                        resfname = 'resgvs\\' + bookname.lower() + '\\' + ftitle + '.gv' 
                        print(ftitle)
                        print(resfname)
                        if make_viz:
                            t = viewable_tree(ttitle, i, q)
                            t.to_graphviz(filename=resfname, shape='box', sorting=False)
                            flip(resfname)
                            style(resfname, 'plain')
                        if populate:
                            book, chapterverse = title.split()
                            chapterverse = [int(numb) for numb in chapterverse.split(':')]
                            chapter, verse = chapterverse[0], chapterverse[1]
                            hlf = 'abc'[k]
                            new_parsing = Parsing(book=book, chapter=chapter, verse=verse, half_verse=hlf, parsing_num=n+1,
                                                  gvpath=resfname)
                            session.add(new_parsing)
                            tree_db(title + hlf, i, q, new_parsing)
                            print(new_parsing.gvpath)
                            session.commit()
                            all_nodes = new_parsing.nodes
                            for node in all_nodes:
                                node.add_bl()
                            session.commit()
                            print('commited')
