import pandas as pd
import matplotlib.pyplot as plt
import mpl_extra.treemap as tr
import sys
from collections import Counter

names = []
projects = []
weights = []

for line in open(sys.argv[1]):
    name, part = line.split(';')
    if '[bot]' in name or name.endswith('-bot') or name.lower() in ('github actions', 'conda bot', 'google code exporter'):
        continue
    project, weightstr = part.split()
    weights.append(int(weightstr))
    projects.append(project)
    names.append(name)


df = pd.DataFrame(dict(weights=weights, projects=projects, names=names))
print("%d entries" % len(df))
suffix = ''
if '--cut-tiny' in sys.argv:
    df = df[df.weights > 0.001 * df.weights.max()]
    print("%d entries after cut" % len(df))
    suffix += '_withouttiny'
if '--cut-major' in sys.argv:
    #top_projects = 'PypeIt', 'pencil-code', 'seaborn', 'moose', 'starlink', 'astropy', 'yt', 'pycbc', 'q-e', 'nemo', 'class_public', 'matplotlib', 'miriad', 'mesa'
    top_projects = Counter()
    for k, v in zip(projects, weights):
        top_projects[k] += v
    
    for project, _ in top_projects.most_common(20):
        df = df[df.projects != project]
    print("%d entries after cut" % len(df))
    suffix += '_withoutmajor'

fig, ax = plt.subplots(figsize=(20,20), dpi=100, subplot_kw=dict(aspect=2.0))
trc = tr.treemap(
    ax, df, area='weights', fill='projects', labels='names',
    levels=['projects', 'names'],
    textprops={'c':'w', 'reflow':True,
              'place':'bottom left', 'max_fontsize':14},
    rectprops={'ec':'w'},
    subgroup_rectprops={'projects':{'ec':'k', 'alpha':0.5, 'lw':4, 'fill':False,
                                 'zorder':5
                                 }},
    subgroup_textprops={'projects':{'c':'brown', 'fontstyle':'italic', 
        'max_fontsize':14, 'place':'top left', 'zorder':5}},
)
ax.axis('off')

#cb = fig.colorbar(trc.mappable, ax=ax, shrink=0.5)
#cb.ax.set_title('hdi')
#cb.outline.set_edgecolor('w')

#plt.title('by person-days')
fig.savefig(sys.argv[1] + suffix + '.png', dpi='figure')  #, bbox_inches='tight')
fig.savefig(sys.argv[1] + suffix + '.pdf', dpi='figure')  #, bbox_inches='tight')
plt.close()
