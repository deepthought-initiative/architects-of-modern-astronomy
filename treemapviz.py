import pandas as pd
import matplotlib.pyplot as plt
import mpl_extra.treemap as tr
import sys

names = []
projects = []
weights = []

for line in open(sys.argv[1]):
    name, part = line.split(';')
    if '[bot]' in name or name.endswith('-bot') or name.lower() in ('GitHub Actions', 'conda bot'):
        continue
    project, weightstr = part.split()
    weights.append(int(weightstr))
    projects.append(project)
    names.append(name)
    #if len(names) > 100:
    #   break


df = pd.DataFrame(dict(weights=weights, projects=projects, names=names))

fig, ax = plt.subplots(figsize=(20,10), dpi=100, subplot_kw=dict(aspect=0.5))
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
fig.savefig('fig2.png', dpi='figure')  #, bbox_inches='tight')
plt.close()
