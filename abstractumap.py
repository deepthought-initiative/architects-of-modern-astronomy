import corner
import adjustText
import matplotlib.pyplot as plt
import umap
import numpy as np
import tqdm
from urllib.parse import unquote
import fetchgit
import json
import requests_cache
import ads
import spacy
import sys
from sklearn.decomposition import NMF
from sklearn.feature_extraction.text import TfidfVectorizer

def bibcode_query(bib_url):
    if bib_url.startswith('http://'):
        bib_url = bib_url.replace('http://', '')
    elif bib_url.startswith('https://'):
        bib_url = bib_url.replace('https://', '')

    if bib_url.startswith('adsabs.harvard.edu/abs/'):
        bib_url = bib_url.replace('adsabs.harvard.edu/abs/', '')
    elif bib_url.startswith('ui.adsabs.harvard.edu/abs/'):
        bib_url = bib_url.replace('ui.adsabs.harvard.edu/abs/', '')
    elif bib_url.startswith('ui.adsabs.harvard.edu/#abs/'):
        bib_url = bib_url.replace('ui.adsabs.harvard.edu/#abs/', '')
    return 'bibcode:%s' % unquote(bib_url)

# reuse same cache
mem = fetchgit.mem
requests_cache.install_cache('demo_cache', allowable_methods=('GET', 'POST'), expire_after=3600 * 24 * 30)

@mem.cache
def get_abstract(bib_urls):
    """Get paper authors and ORCID"""
    abstracts = []
    for bib_url in bib_urls:
        if 'adsabs.harvard.edu' in bib_url:
            query = bibcode_query(bib_url)
            for p in ads.SearchQuery(q=query, fl=['abstract'], sort="date"):
                if p.abstract is not None:
                    abstracts.append(p.abstract)
    return abstracts

@mem.cache
def get_title(bib_urls):
    """Get paper authors and ORCID"""
    for bib_url in bib_urls:
        if 'adsabs.harvard.edu' in bib_url:
            query = bibcode_query(bib_url)
            for p in ads.SearchQuery(q=query, fl=['title'], sort="date"):
                if p.title is not None:
                    return p.title
    return ''

seed = int(sys.argv[1])

corpus = []
print("loading data...")
data_full = json.load(open("outputs/scientific-software-contributions-days_active.json"))
print("loading data... done")
#data = [e for e in data_full if e['project_impact'] >= 5]
data = data_full
for e in tqdm.tqdm(data):
    words = e['paper_title'] + "\n" + "\n".join(get_abstract(e['bib_urls']))
    #if len(words) == 0:
    #    print(e['project_name'], 'has no words', e['bib_urls'])
    corpus.append(words)

nlp = spacy.load("en_core_web_sm")
for line in open('stopwords.txt'):
    nlp.Defaults.stop_words.add(line.strip())
print(nlp.Defaults.stop_words)

n_features = 1000
n_components = 7
n_top_words = 20
init = "nndsvda"


vectorizer = TfidfVectorizer(max_df=0.95, min_df=2, max_features=n_features, stop_words=list(nlp.Defaults.stop_words))
tfidf = vectorizer.fit_transform(corpus)
#print(tfidf[0].todense())
feature_names = vectorizer.get_feature_names_out()

component_words = []
print("NMF-Frobenius:")
nmf = NMF(
    n_components=n_components,
    random_state=seed,
    init=init,
    beta_loss="frobenius",
    alpha_W=0.00005,
    alpha_H=0.00005,
    l1_ratio=1,
    max_iter=10000,
)
tfidf_reduced = nmf.fit_transform(tfidf)

plt.rcParams.update({
    "text.usetex": True,
    "font.family": "Helvetica"
})

chosen_names_mapping = {
    'cosmological':'cosmology', 
    'reduction':'data reduction pipelines',
    'exoplanets':'exoplanets',
    'hydrodynamics':'hydrodynamic simulations',
    'radiative':'radiative transfer spectra simulation',
    'transfer':'radiative transfer spectra simulation',
    'inference':'statistical inference',
    'galaxies':'galaxies'}
pos_override = {
    (1, 'exoplanets'): (0.9, 0.9),
    (1, 'radiative transfer spectra simulation'): (0.8, 0.8),
    (1, 'galaxies'): (0.2, 0.7),
    (1, 'cosmology'): (0.1, 0.4),
    (1, 'statistical inference'): (0.8, 0.15),
    
    (3, 'exoplanets'): (0.8, 0.9),
    (3, 'radiative transfer spectra simulation'): (0.15, 0.9),
    (3, 'galaxies'): (0.1, 0.5),
    (3, 'cosmology'): (0.4, 0.2),
    (3, 'statistical inference'): (0.8, 0.15),
}
cluster_names = []

for topic_idx, topic in enumerate(nmf.components_):
    top_features_ind = topic.argsort()[-n_top_words:]
    top_features = feature_names[top_features_ind]
    component_words.append(top_features)
    cluster_name = ''
    for k, v in chosen_names_mapping.items():
        if k in top_features:
            cluster_name = v
            break
    cluster_names.append(cluster_name)
    print(' - ' + ' '.join(top_features))

cluster_ids = np.arange(len(nmf.components_))
# assign to a "cluster" (component) based on which axis is mostly aligns with
cluster = tfidf_reduced.argmax(axis=1)

"""
print("K-Means:")
kmeans = KMeans(
    n_clusters=n_components,
    max_iter=1000,
    random_state=2,
)
cluster = kmeans.fit_predict(tfidf_reduced)
for ctr in kmeans.cluster_centers_:
    top_features_ind = ctr.argsort()[-n_top_words:]
    top_features = feature_names[top_features_ind]
    component_words.append(top_features)
    print(' - ' + ' '.join(top_features))
cluster_ids, cluster_sizes = np.unique(kmeans.labels_, return_counts=True)
print(cluster_ids, cluster_sizes)
"""
"""
print("NMF-KL:")
nmf = NMF(
    n_components=n_components,
    random_state=1,
    init=init,
    beta_loss="kullback-leibler",
    solver="mu",
    max_iter=1000,
    alpha_W=0.00005,
    alpha_H=0.00005,
    l1_ratio=0.5,
).fit(tfidf)

for topic_idx, topic in enumerate(nmf.components_):
    top_features_ind = topic.argsort()[-n_top_words:]
    top_features = feature_names[top_features_ind]
    weights = topic[top_features_ind]
    print(' - ' + ' '.join(top_features))

print("LDA:")
lda = LatentDirichletAllocation(
    n_components=n_components,
    max_iter=5,
    learning_method="online",
    learning_offset=50.0,
    random_state=0,
)
for topic_idx, topic in enumerate(nmf.components_):
    top_features_ind = topic.argsort()[-n_top_words:]
    top_features = feature_names[top_features_ind]
    weights = topic[top_features_ind]
    print(' - ' + ' '.join(top_features))

#for word in vectorizer.get_feature_names_out():
#    print(word)
"""

print("running umap...")
u = umap.UMAP(metric='cosine', random_state=seed + 1, min_dist=0.1).fit_transform(tfidf)
print("running umap... done")
u1lo = np.nanmin(u[:,0])
u1hi = np.nanmax(u[:,0])
u2lo = np.nanmin(u[:,1])
u2hi = np.nanmax(u[:,1])
#nbins = 10
u1 = np.linspace(u1lo, u1hi, 12)
u2 = np.linspace(u2lo, u2hi, 70)

#nmf_class = np.argmax(nmf.transform(tfidf), axis=1)
classes_colors = plt.cm.tab10.colors
plt.figure(figsize=(12, 12))
#rng = np.random.RandomState(seed + 2)
texts = []
for i in range(1):
    #plt.subplot(2, 1, 1 + i)
    for class_i in cluster_ids:
        color = classes_colors[class_i]
        member0 = u[cluster==class_i,0]
        member1 = u[cluster==class_i,1]
        print(class_i, ' '.join(component_words[class_i]))
        corner.hist2d(
            member0, member1,
            levels=[0.68], ax=plt.gca(),
            quiet=False,
            plot_datapoints=False, plot_density=False, smooth=1,
            plot_contours=True, fill_contours=False,
            contour_kwargs=dict(alpha=0.3, colors=[color]),
            #contourf_kwargs=None, data_kwargs=None, pcolor_kwargs=None,
            new_fig=False)
        if i == 0:
            plt.plot(
                member0, member1, 'x ',
                mec=color, mew=0.5, mfc='none', ms=4, alpha=0.3)
        
        if i == 0:
            text_here = ""
            max_length_per_line = len(' '.join(component_words[class_i])) // 4
            current_line = ""
            for nextword in component_words[class_i]:
                if len(current_line) > max_length_per_line:
                    text_here += current_line + "\n"
                    current_line = nextword
                else:
                    current_line += " " + nextword
            text_here = text_here.strip() + "\n" + current_line
            posx = np.median(member0)
            posy = np.median(member1)
            if (seed, cluster_names[class_i]) in pos_override:
                posx, posy = pos_override[(seed, cluster_names[class_i])]
                posx = u1lo + posx * (u1hi - u1lo)
                posy = u2lo + posy * (u2hi - u2lo)
            texts.append(plt.text(
                posx,
                posy,
                r'\textbf{``' + cluster_names[class_i] + "''}\n" + text_here,
                va='center', ha='center', size=8,
                color=color, zorder=6, bbox=dict(facecolor='white', alpha=0.8, edgecolor=color)))

    #plt.title(['Classes', 'Projects'][i])
    plt.xticks([])
    plt.yticks([])
    plt.subplots_adjust(hspace=0, wspace=0)

    if i == 0:
        print("running adjustText...")
        # adjustText.adjust_text(texts, objects=texts)
        print("running adjustText... done")

#u1lo = u[u[:,0] > 0,0].min()
for k in np.where(~np.isfinite(u[:,0]))[0]:
    print("bad:", data[k]['project_name'], data[k]['bib_urls'])
print("printing most important project name...")
texts = []
for i, (u1ilo, u1ihi) in enumerate(zip(tqdm.tqdm(u1[:-1]), u1[1:])):
    for j, (u2ilo, u2ihi) in enumerate(zip(u2[:-1], u2[1:])):
        #print(u1ilo, u1ihi, u2ilo, u2ihi)
        mask_members = np.logical_and(
            np.logical_and(u[:,0] > u1ilo, u[:,0] < u1ihi),
            np.logical_and(u[:,1] > u2ilo, u[:,1] < u2ihi))

        if not mask_members.any():
            continue

        #print(mask_members.shape, mask_members, np.where(mask_members)[0])
        member_indices = np.where(mask_members)[0]
        weights = [data[i]['project_impact'] for i in member_indices]
        k = member_indices[np.argmax(weights)]
        #k = rng.choice(member_indices, p=np.array(weights)/np.sum(weights))
        #k = member_indices[np.argsort(weights)[-2:][0]]
        #print(data[k]['project_name'])
        texts.append(plt.text(
            #u[k,0],
            #u[k,1],
            (u1ilo + u1ihi) / 2,
            (u2ilo + u2ihi) / 2,
            #get_title(data[k]['bib_urls'][0]),
            data[k]['project_name'], va='center', ha='center',
            color=classes_colors[cluster[k]],
            size=8 if len(data[k]['project_name']) < 10 else 6,
            ))

#adjustText.adjust_text(texts, max_move=(100, 100), time_lim=10)
#plt.xlim(u[u[:,0] > 0,0].min(), u[:,0].max())
print("saving plot...")
plt.savefig('abstractumap%d.pdf' % seed)
plt.savefig('abstractumap%d.png' % seed)
