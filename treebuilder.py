import re

def flip(filename): 
    lines = []
    with open(filename, 'r', encoding='utf-8') as f:
        data = f.readlines()
        for i, line in enumerate(data):
            if i > 0:
                if not line.strip():
                    break
                else:
                        #if 'MIN' in line and i > 1:
                            #line = line.replace('box', 'point')
                    lines.append(line)
            
        lines = lines[::-1]

        for i, line in enumerate(data):
            if i > 0:
                if not line.strip():
                    break
                else:
                    data[i] = lines[i-1]
            
        data.append(data[-1])
        sub_ids = []
        for i in data:
            if 'SUB' in i:
                sub_ids.append('SUB' + re.search(r"SUB(.+?)\"", i).group(1))
            
        sub_ids = list(dict.fromkeys(sub_ids))

        data[-2] = '\t{rank = same; ' + '; '.join([i for i in sub_ids]) + '}'
            
    with open(filename, 'w', encoding='utf-8') as g:
        g.writelines(data)

def style(filename, accent_style): 
    with open(filename, 'r', encoding='utf-8') as f:
        data = f.readlines()
        for n, line in enumerate(data):
            if '->' in line:
                data[n] = f"\t{line.strip()} [arrowhead=none]\r\n"
            else:
                if 'MIN' in line:
                    data[n] = line.replace('box', accent_style)
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.writelines(data)

