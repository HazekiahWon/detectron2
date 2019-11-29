
import os.path as osp

def foo(line):
    line = str(line.strip())
    s = line.split(' ')
    return [l for l in s if l!='']
folder = osp.join('anno')
lines = list()
split = 'particles'
with open(osp.join(folder,f'{split}.star'),'r') as f:
    for line in f.readlines(): lines.append(line)

fields = lines[5:35]
header = [x.split(' ')[0] for x in fields]
lines = [foo(l) for l in lines[35:]]

with open(osp.join(folder, f'{split}.csv'),'w') as f:
    f.write(','.join(header))
    f.write('\n')
    for line in lines:
        f.write(','.join(line))
        f.write('\n')
print(f'{split}.csv saved.')