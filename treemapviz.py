import pandas as pd
import matplotlib.pyplot as plt
import mpl_extra.treemap as tr
import sys
from collections import Counter
import itertools
import pycountry

countries_abbr = {c.alpha_2 for c in pycountry.countries}
#countries_map = {}
#countries_map.update({sd.code.split('-')[-1]:'US' for sd in pycountry.subdivisions.get(country_code='US')})
#countries_map.update({c.alpha_3:c.alpha_2 for c in pycountry.countries})
#countries_map.update({c.alpha_2:c.alpha_2 for c in pycountry.countries})
#countries_map.update({c.name.split(',').upper():c.alpha_2 for c in pycountry.countries})
#countries_map.update({c.official_name.split(',').upper():c.alpha_2 for c in pycountry.countries})

def get_country(name):
    country = name.split(',')[-1].strip()
    return country if country in countries_abbr else None
def get_short_name(name, maxlength):
    #return name
    parts = name.split(',')
    if parts[-1] in countries_abbr:
        parts = parts[:-1]
    
    if len(parts[0]) > maxlength:
        parts[0] = parts[0].replace('School of', '').replace('Dep of', '')
    if len(','.join(parts)) < maxlength:
        return ','.join(parts)
    try:
        rindex = (' '.join(parts)[:maxlength+5]).rindex(',')
    except ValueError:
        rindex = maxlength
    return ','.join(parts)[:rindex].rstrip(', ')
        
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
viz_countries = '--countries' in sys.argv
suffix = ''
if viz_countries:
    suffix = '_countries'
    df['countries'] = [get_country(name) for name in names]
    df['names'] = [get_short_name(name, 30) for name in names]
if '--cut-tiny' in sys.argv:
    df = df[df.weights > 0.005 * df.weights.max()]
    print("%d entries after cut" % len(df))
    suffix += '_withouttiny'
if '--cut-major' in sys.argv:
    #top_projects = 'PypeIt', 'pencil-code', 'seaborn', 'moose', 'starlink', 'astropy', 'yt', 'pycbc', 'q-e', 'nemo', 'class_public', 'matplotlib', 'miriad', 'mesa'
    top_projects = Counter()
    for k, v in zip(projects, weights):
        top_projects[k] += v
    
    for project, _ in top_projects.most_common(30):
        df = df[df.projects != project]
    print("%d entries after cut" % len(df))
    suffix += '_withoutmajor'

colors = plt.cm.tab10.colors
cmap = dict(zip(df['projects'].unique(), itertools.cycle(colors)))
cmap['yt'] = 'k'
cmap['astropy'] = 'darkgrey'
cmap['starlink'] = 'navy'

if viz_countries:
    fig, ax = plt.subplots(figsize=(20,20), dpi=100, subplot_kw=dict(aspect=1.2))
    trc = tr.treemap(
        ax, df[~df['countries'].isna()], area='weights', fill='projects', labels='projects',
        levels=['countries', 'names', 'projects'], cmap=cmap,
        textprops=dict(c='w', reflow=True, max_fontsize=12, alpha=0.5, fontstyle='italic', place='bottom center'),
        rectprops=dict(ec='w', lw=0.1),
        subgroup_textprops={'countries':dict(c='white', alpha=0.5, zorder=5),
                           'names':dict(c='w', place='top left', max_fontsize=18, reflow=True)},
        subgroup_rectprops={'countries':dict(ec='w', lw=5, zorder=1, fill=False),
                           'names':dict(ec='w', lw=2, fill=False, zorder=4)}
    )
else:
    fig, ax = plt.subplots(figsize=(20,20), dpi=100, subplot_kw=dict(aspect=1.3))
    trc = tr.treemap(
        ax, df, area='weights', fill='projects', labels='names',
        levels=['projects', 'names'], cmap=cmap,
        textprops={'c':'w', 'reflow':True,
                  'place':'bottom left', 'max_fontsize':14},
        rectprops={'ec':'w'},
        subgroup_rectprops={'projects':{'ec':'k', 'alpha':0.5, 'lw':4, 'fill':False,
                                     'zorder':5
                                     }},
        subgroup_textprops={'projects':{'c':'white', 'fontweight':'bold', 
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
