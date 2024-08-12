from adjustText import adjust_text
from collections import Counter
import numpy as np
import matplotlib.pyplot as plt

hosts = [line.split(';')[0].replace('https://','').replace('http://','').replace('www.', '').split('/')[0]
	for line in open('outputs/scientific-software.txt')]
is_github = [h == 'github.com' for h in hosts]
print('Github: %.2f%%' % (sum(is_github)*100 / len(is_github)))
print(Counter(hosts))

impact_map = np.array([int(line.split(';')[2]) for line in open('outputs/scientific-software.txt')])
impact = np.array([int(line.split(';')[2]) for line in open('outputs/scientific-software.txt')])
plt.hist(np.log10(impact+0.1), bins=np.log10([0.1, 1, 10, 100, 1000, 10000, 100000, 1000000]))
plt.xticks(np.log10([0.1, 1, 10, 100, 1000, 10000, 100000, 1000000]), [0.1, 1, 10, 100, 1000, 10000, 100000, 1000000])
plt.xlabel('Impact')
plt.ylabel('# Software')
plt.savefig('impact.pdf')
plt.close()

filename = 'outputs/scientific-software-contributions-days_active.txt'
names = [line.split(';')[0] for line in open(filename)]
project = [line.split(';')[1] for line in open(filename)]
contributions = np.array([int(line.split(';')[2]) for line in open(filename)])
impacts = np.array([int(line.split(';')[3]) for line in open(filename)])

project_colors = {'astropy':'orange', 'yt':'darkgreen', 'starlink':'navy'}
plt.figure(figsize=(12, 12))
plt.yscale('log')
plt.xscale('log')
plt.ylabel('Effort (Contributor # of Active Days)')
plt.xlabel('Impact (# of citations to papers citing software)')
plt.plot(impacts, contributions, 'x ', mfc='none', mec='k', ms=2)
texts = []
for i in np.where(np.logical_or(impacts > 30000, contributions > 1000))[0]:
	color = project_colors.get(project[i], 'k')
	if color != 'k':
		plt.plot(impacts[i], contributions[i], 'x ', mfc='none', mec=color, ms=2)
	if not any(c > contributions[i] for p, c in zip(project, contributions) if p == project[i]):
		texts.append(plt.text(impacts[i], contributions[i], project[i] + ':' + names[i], size=8, alpha=0.5, color=color))
adjust_text(texts, expand=(1.1, 1.5), # expand text bounding boxes by 1.2 fold in x direction and 2 fold in y direction
            arrowprops=dict(arrowstyle='->', color=color, linewidth=0.1, alpha=0.5), time_lim=10)
plt.savefig('impact_contributions.pdf')
plt.close()
