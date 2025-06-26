from treelib import Tree, Node
from hebrew import Hebrew
import re
from main_preprocess import viewable_tree, parse_verse
import graphviz
import os
from pathlib import Path

def make_img(bkname, format):
    pth = f"resgvs\{bkname}"
    rpth = f"resimgs\{bkname}"
    Path(f"resimgs/{bkname}").mkdir(parents=True, exist_ok=True)
    gvs = os.listdir(pth)
    for file in gvs:
        if file[-3::] == '.gv':
            if file[:len(bkname)] == bkname.capitalize():
                    name = pth + '\\' + file
                    print(name)
                    dot = graphviz.Source.from_file(name, encoding='latin-1')
                    dot.render(directory=rpth, filename=file, format=format)

bkname = 'jos'
make_img(bkname, 'svg')