import requests_cache
import requests
from bs4 import BeautifulSoup
from fetchgit import mem, get_significant_contributors, extract_github_url_from_pypi
import subprocess
import tqdm
import os
from collections import defaultdict
import ads
from urllib.parse import unquote
from namematch import same_author
from affilmatch import is_affil_same, split_affil_string, shorten_affil
import kvstore

requests_cache.install_cache('demo_cache', allowable_methods=('GET', 'POST'), expire_after=3600 * 24 * 30)

@mem.cache
def get_ascl_list():
    """Get list of astronomy software packages"""
    urls = []
    response = requests.get('https://ascl.net/code/all/limit/10000/listmode/compact')
    soup = BeautifulSoup(response.content, "html.parser")
    for title_span in soup.find_all('span', class_='title'):
        urls.append('https://ascl.net/' + title_span.find('a')['href'])
    return urls

@mem.cache
def get_code_info(url):
    """Get code website and list of papers"""
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    title = soup.find('title').string.strip()[len('ASCL.net'):].strip().strip('-').strip()
    # Extract Code site
    code_site_element = soup.find('dt', string='Code site:')
    code_sites = [a.get('href') for a in code_site_element.find_next('dd').find_all('a', href=True)] if code_site_element else []

    # Extract Described in
    described_in_element = soup.find('dt', string='Described in:')
    return title, code_sites, [a.get('href') for a in described_in_element.find_next('dd').find_all('a')] if described_in_element else []


def iterate_ascl():
    for url in tqdm.tqdm(sorted(get_ascl_list()), desc='fetching ASCL repository URLs'):
        yield get_code_info(url)

@mem.cache
def get_joss_repo_urls(url):
    urls = []
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    for link_href in soup.find_all('a', class_='paper-btn'):
        if link_href.text.strip() == 'Software repository':
            urls.append(link_href['href'])
    return urls

def iterate_joss_list():
    """Get list of JOSS articles"""
    fields = ['bibcode', 'author', 'year', 'citation_count', 'doi', 'title', 'eid', 'identifier', 'authors']
    query = 'bibstem:"joss"  citation_count:[2 TO 1000000]'
    results = list(ads.SearchQuery(q=query, fl=fields, sort="date", max_pages=100))
    for p in tqdm.tqdm(results, desc='fetching JOSS repository URLs'):
        repo_urls = get_joss_repo_urls(url='https://ui.adsabs.harvard.edu/link_gateway/%s/PUB_HTML' % p.bibcode)
        # print(p.bibcode, p.author, repo_urls, p.id)
        yield p.title[0], repo_urls, ['https://ui.adsabs.harvard.edu/abs/%s' % p.bibcode]


@mem.cache
def get_git_url(code_site):
    """Get code git repository"""
    try:
        response = requests.get(code_site)
        soup = BeautifulSoup(response.content, "html.parser")
        links = soup.find_all("a", href=True)
        for link in links:
            link_url = link["href"]
            if not link_url or '?' in link_url or link_url.count('/') > 5 or link_url.count('/') < 3:
                continue
            if link_url.startswith('http://github.com/'):
                return link_url.replace('http://github.com/', 'https://github.com/')
            if link_url.startswith('https://github.com/'):
                return link_url
    except requests.exceptions.SSLError:
        pass

@mem.cache
def get_git_url2(code_site):
    """Get code git repository"""
    try:
        response = requests.get(code_site, timeout=(10, 10))
        soup = BeautifulSoup(response.content, "html.parser")
        links = soup.find_all("a", href=True)
        for link in links:
            if link.text == 'theme': # footer text
                continue
            link_url = link["href"]
            if 'just-the-docs' in link_url: # theme link
                continue
            if not link_url or '?' in link_url or link_url.count('/') < 3:
                continue
            link_url = '/'.join(link_url.split('/')[:5])
            if link_url.startswith('http://github.com/'):
                return link_url.replace('http://github.com/', 'https://github.com/')
            if link_url.startswith('https://phab.hepforge.org/source/'):
                return link_url
            if link_url.startswith('https://github.com/'):
                return link_url
            if link_url.startswith('https://gitlab.com/'):
                return link_url
            if link_url.startswith('http://bitbucket.org/'):
                return link_url.replace('http://bitbucket.org/', 'https://bitbucket.org/')
            if link_url.startswith('https://bitbucket.org/'):
                return link_url
            #if 'install' in link.text.lower() or 'start' in link.text.lower():
            #    deep_link_url = get_git_url(link_url)
            #    if deep_link_url is not None:
            #        return deep_link_url

    except requests.exceptions.SSLError:
        pass

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

def get_best_orcid(p):
    for orcid_user, orcid_pub, orcid_other in zip(p.orcid_user if p.orcid_user is not None else ['-']*1000, p.orcid_pub if p.orcid_pub is not None else ['-']*1000, p.orcid_other if p.orcid_other is not None else ['-']*1000):
        orcid = None
        if orcid_user != '-':
            orcid = orcid_user
        if orcid_pub != '-':
            orcid = orcid_pub
        if orcid_other != '-':
            orcid = orcid_other

        yield orcid

@mem.cache
def get_authors(bib_urls):
    """Get paper authors and ORCID"""
    fields = ['bibcode', 'author', 'orcid_user', 'orcid_pub', 'orcid_other', 'title', 'eid', 'identifier']
    authors = {}
    for bib_url in bib_urls:
        if 'adsabs.harvard.edu' in bib_url:
            query = bibcode_query(bib_url)
            for p in ads.SearchQuery(q=query, fl=fields, sort="date"):
                # print(p.author, p.orcid_user, p.orcid_pub, p.orcid_other)
                for author, orcid in zip(p.author, get_best_orcid(p)):
                    if authors.get(author) is None:
                        authors[author] = orcid
    return authors

@mem.cache
def get_person_affil_history(orcid, author, verbose=False):
    """Get affiliation of a person over time"""
    fields = ['author', 'aff', 'year', 'orcid_user', 'orcid_pub', 'orcid_other']
    query = 'orcid:%s' % orcid
    results = list(ads.SearchQuery(q=query, fl=fields, sort="date", max_pages=100)) #[::-1]
    known_affils = []
    years = defaultdict(list)
    for p in (tqdm.tqdm(results, desc='fetching affil history') if verbose else results):
        for author_i, affils_i, orcid_i in zip(p.author, p.aff, get_best_orcid(p)):
            for affil_i in split_affil_string(affils_i):
                if ',' not in affil_i:
                    continue
                affil_i = affil_i.split('<ORCID>')[0]
                if orcid == orcid_i and affil_i != '-':
                    # print('::', p.year, author_i, affil_i)
                    # print(p.year, list(zip(p.aff, p.author)), p.orcid)
                    if not any(is_affil_same(affil, affil_i, verbose=False) for affil in years[p.year]):
                        for affil_j in known_affils:
                            if is_affil_same(affil_j, affil_i, verbose=False):
                                years[p.year].append(affil_j)
                                break
                        else:
                            years[p.year].append(affil_i)
                            known_affils.append(affil_i)
                        #years[p.year].append(affil_i)
                        #print(p.year, affil_i)
    if verbose:
        for y, affil in years.items():
            print(' *', y, affil)
    return years


def get_affil_set(startyear, endyear, years):
    full_affil_set = set()
    for year in range(startyear - 1, endyear + 1):
        full_affil_set = full_affil_set.union(years[year])
    return full_affil_set

def translate_to_institutional_contributors(contributors, authors):
    contributors_with_orcid = []
    for contributor, ncontributions, startdate, enddate in contributors:
        orcid = authors.get(contributor, '-')
        if orcid != '-':
            contributors_with_orcid.append((contributor, orcid, ncontributions, startdate, enddate))

    full_affil_set = set()
    for contributor, orcid, ncontributions, startdate, enddate in contributors_with_orcid:
        print("    history of %s [%s] (%d-%d)" % (contributor, orcid, startdate, enddate))
        years = get_person_affil_history(orcid, contributor)
        # print(years)
        for year in range(startdate - 1, enddate + 1):
            full_affil_set = full_affil_set.union(years[str(year)])
            # print('  ', year, years.get(str(year), []), full_affil_set)
    # print("    all relevant affils:", full_affil_set)

    # deduplicate affiliations, keep longest name
    dedup_affil_set = []
    for affil_i in sorted(full_affil_set, key=lambda s: len(s), reverse=True):
        if not any(is_affil_same(affil_j, affil_i, verbose=False) for affil_j in dedup_affil_set):
            dedup_affil_set.append(affil_i)
    #print("    affils: ", dedup_affil_set)

    # get all affiliations falling between years of startdate and enddate+1 years
    for affil_k in dedup_affil_set:
        # print("affil", affil_k)
        if affil_k.startswith('Now at'): continue
        ncontributions_k = 0
        startdates = []
        enddates = []
        for contributor, orcid, ncontributions, startdate, enddate in contributors_with_orcid:
            is_relevant_affiliation = False
            years = get_person_affil_history(orcid, contributor)
            for year in range(startdate - 1, enddate + 1):
                for affil_i in years[str(year)]:
                    if is_affil_same(affil_k, affil_i, verbose=False):
                        is_relevant_affiliation = True
            if not is_relevant_affiliation:
                continue
            ncontributions_k += ncontributions
            startdates.append(startdate)
            enddates.append(enddate)
        yield shorten_affil(affil_k), ncontributions_k, min(startdates) if startdates else None, max(enddates) if enddates else None


@mem.cache
def get_impact(bib_urls):
    """Get project impact (citations of papers using it)"""
    fields = ['bibcode', 'author', 'year', 'citation_count', 'doi', 'title', 'eid', 'identifier']
    query = ' OR '.join(['citations(%s)' % bibcode_query(bib_url) for bib_url in bib_urls if 'adsabs.harvard.edu' in bib_url])
    # print('   ', query)
    if query == '':
        return 0
    papers = [p for p in ads.SearchQuery(q=query + ' collection:astronomy', fl=fields, sort="date", max_pages=100)]
    # print('      ', len(papers))
    total_citations = sum((p.citation_count for p in papers if p.citation_count))
    return total_citations


def deduplicate_authors(authors, contributors):
    """Reduce authors."""
    author_map = {
        'Berry, D. S.': 'Berry, David S.',
        'Rob Farmer': 'Robert Farmer',
        'evbauer': 'Evan Bauer',
        'Peter Teuben': 'Teuben, Peter',
        'Teuben, P.': 'Teuben, Peter',
        'Sergey, Koposov': 'Sergey, E. Koposov',
        'gregory.ashton': 'Gregory Ashton',
        'Rodrigo-Tenorio': 'Rodrigo Tenorio',
        'sibirrer': 'Simon Birrer',
        #'Dan F-M': 'Dan Foreman-Mackey',
    }
    values = {}
    startdates = {}
    enddates = {}

    # find contributor in paper author list, store in author_map
    for author, value, startdate, enddate in contributors:
        for author2 in authors:
            # see if we know this contributor as a paper co-author
            # print("CMP(", author, "||", author2,")")
            if same_author(author, author2):
                # map of (code editor) -> (co-author)
                author_map[author] = author2
                # print("==", author, author2)
                break
        # use canonical name from author list, if available, otherwise from git log
        newauthor = author_map.get(author, author)
        # sum up contribution values
        values[newauthor] = values.get(newauthor, 0) + value
        startdates[newauthor] = min(startdate, startdates[newauthor]) if newauthor in startdates else startdate
        enddates[newauthor] = max(enddate, enddates[newauthor]) if newauthor in enddates else enddate
        del author, value, startdate, enddate

    # build deduplicated list of all contributors
    authors_done = {}
    deduplicated_contributors = []
    for author, _, _, _ in contributors:
        newauthor = author_map.get(author, author)
        if newauthor not in authors_done:
            authors_done[newauthor] = True
            deduplicated_contributors.append((newauthor, values[newauthor], startdates[newauthor], enddates[newauthor]))

    return deduplicated_contributors

def get_software_list(parent_sample):
    repos = dict()
    for i, (title, code_sites, bib_urls) in enumerate(parent_sample):
        print("[%d/%d] ###" % (i+1, len(parent_sample)), code_sites, bib_urls, title)
        if len(bib_urls) == 0:
            print("  no papers found for", code_sites)
            continue

        for code_site in code_sites:
            # print(url, "info", code_site, bib_urls)
            print("  identifying repo url for ", code_site)
            repo_url = None
            if 'github.com/' in code_site or 'gitlab.com/' in code_site or 'bitbucket.com/' in code_site:
                repo_url = code_site
            elif 'pypi.org/' in code_site:
                repo_url = extract_github_url_from_pypi(code_site)
            elif code_site.startswith('https://dx.doi.org'):
                pass
            elif code_site.startswith('https://doi.org'):
                pass
            elif code_site.startswith('http') and code_site.split('.')[-1] not in ('zip', 'gz', 'bz2'):
                domain = code_site.split('://')[1].split('/')[0]
                if not kvstore.is_stored('badurls', domain):
                    try:
                        repo_url = get_git_url2(code_site)
                    except requests.exceptions.ConnectTimeout:
                        kvstore.store('badurls', domain)
                    except requests.exceptions.ConnectionError:
                        kvstore.store('badurls', domain)
                    except requests.exceptions.ReadTimeout:
                        kvstore.store('badurls', domain)
                    except AssertionError:
                        kvstore.store('badurls', domain)
            # print(url, "repo", repo_url, len(bib_urls))
            if repo_url is None:
                print("    no repo found for", code_sites)
                continue
            _, other_code_sites, other_bib_urls = repos.get(repo_url, (None, [], []))
            repos[repo_url] = title, sorted(set(code_sites).union(other_code_sites)), sorted(set(bib_urls).union(other_bib_urls))

    return repos

if __name__ == '__main__':
    os.environ['GIT_TERMINAL_PROMPT'] = '0'

    parameter = os.environ['QUANTIFIER']  # "commits", "lines_changed" or "days_active"
    use_institutes = os.environ.get('INSTITUTES', '') != ''
    fout = open('outputs/weighted-flamegraph-%s%s.txt' % (parameter, '-institutes' if use_institutes else ''), 'w')
    parent_sample = list(iterate_joss_list()) + list(iterate_ascl())
    repos = get_software_list(parent_sample)
    fout2 = open('outputs/scientific-software.txt', 'w')
    fout3 = open('outputs/scientific-software-contributions-%s%s.txt' % (parameter, '-institutes' if use_institutes else ''), 'w')
    print()
    print("checking impact...")
    for i, (repo_url, (title, code_sites, bib_urls)) in enumerate(repos.items()):
        print("[%d/%d] ***" % (i+1, len(repos)), repo_url, [bibcode_query(b).replace('bibcode:','') for b in bib_urls])
        try:
            project_impact = get_impact(bib_urls)
        except IndexError as e:
            print("    IndexError:", e)
            continue
        except ads.exceptions.APIResponseError as e:
            print("    APIResponseError:", e)
            break
        fout2.write("%s;%s;%d;%s\n" % (repo_url, bib_urls[0], project_impact, title))
        fout2.flush()
        if project_impact == 0:
            print("    no impact found for", bib_urls)
            continue
        if project_impact < 10:
            print("    low impact, skipping")
            continue
        # get people's names & ORCID
        print("  getting authors for %s" % ([bibcode_query(b).replace('bibcode:','') for b in bib_urls]))
        authors = get_authors(bib_urls)
        print("    %s impact %d by %s" % (repo_url, project_impact, list(authors.keys())))
        # print(url, "authors", authors)

        project_name = repo_url.strip('/').split('/')[-1]
        significant_contributors, top_contributor_contributions = [], None
        try:
            significant_contributors, top_contributor_contributions = get_significant_contributors(repo_url, parameter)
            if top_contributor_contributions is not None:
                significant_contributors_deduplicated = deduplicate_authors(authors, significant_contributors)
                #significant_contributors_deduplicated = significant_contributors
                # write out person's contribution proportional to impact of the software and days invested
                if use_institutes:
                    significant_contributors_deduplicated = translate_to_institutional_contributors(
                        significant_contributors_deduplicated, authors)
                for contributor, ncontributions, _, _ in significant_contributors_deduplicated:
                    fout.write('%s;%s %d\n' % (contributor.replace(';', ','), project_name.replace(';', ','), ncontributions * project_impact))
                    fout3.write('%s;%s;%d;%d\n' % (contributor.replace(';', ','), project_name.replace(';', ','), ncontributions, project_impact))
                fout.flush()
                fout3.flush()
        except subprocess.CalledProcessError as e:
            print("    failure:", repo_url, e)
