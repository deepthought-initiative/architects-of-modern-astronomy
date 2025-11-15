import json
import requests_cache
import requests
import urllib3
from bs4 import BeautifulSoup
import fetchgit
import subprocess
import tqdm
import os
from collections import defaultdict, Counter
import ads
from urllib.parse import unquote
from namematch import same_author
from affilmatch import is_affil_same, split_affil_string, shorten_affil
import kvstore
from datetime import date, datetime, timedelta


# reuse same cache
mem = fetchgit.mem
requests_cache.install_cache('demo_cache', allowable_methods=('GET', 'POST'))

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
            if link_url.startswith('https://gitlab.'):
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
def get_pubdate(bib_urls):
    """Get paper authors and ORCID"""
    #fields = ['pubdate']
    fields = ['pubdate']
    pubdates = []
    for bib_url in bib_urls:
        if 'adsabs.harvard.edu' in bib_url:
            query = bibcode_query(bib_url)
            for p in ads.SearchQuery(q=query, fl=fields):
                if p.pubdate is not None:
                    pubdates.append(date.fromisoformat(p.pubdate.replace('-00', '-01')))
    if len(pubdates) == 0:
        return None
    return min(pubdates)

@mem.cache
def get_authors(bib_urls):
    """Get paper authors and ORCID"""
    fields = ['bibcode', 'author', 'orcid_user', 'orcid_pub', 'orcid_other', 'title', 'eid', 'identifier', 'aff']
    authors = {}
    for bib_url in bib_urls:
        if 'adsabs.harvard.edu' in bib_url:
            query = bibcode_query(bib_url)
            for p in ads.SearchQuery(q=query, fl=fields, sort="date"):
                # print(p.author, p.orcid_user, p.orcid_pub, p.orcid_other)
                for author, orcid, affil in zip(p.author, get_best_orcid(p), p.aff):
                    if author not in authors or authors.get(author, ('-', None))[0] == '-':
                        authors[author] = orcid, affil
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
        for author_i, orcid_i, affils_i in zip(p.author, get_best_orcid(p), p.aff):
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
        orcid, affils = authors.get(contributor, ('-', None))
        if orcid != '-':
            contributors_with_orcid.append((contributor, orcid, ncontributions, startdate, enddate))
        elif affils is not None:
            for affil_i in split_affil_string(affils):
                if ',' not in affil_i:
                    continue
                affil_i = affil_i.split('<ORCID>')[0]
                if affil_i != '-':
                    yield shorten_affil(affil_i.strip()), ncontributions, startdate, enddate

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
    for i, ((title, code_sites, bib_urls), parent_db) in enumerate(parent_sample):
        print("[%d/%d] ###" % (i+1, len(parent_sample)), parent_db, code_sites, bib_urls, title)
        if len(bib_urls) == 0:
            print("  no papers found for", code_sites)
            continue

        for code_site in code_sites:
            # print(url, "info", code_site, bib_urls)
            print("  identifying repo url for ", code_site)
            repo_url = None
            if code_site == 'https://www.star.bristol.ac.uk/mbt/topcat/':
                repo_url = 'https://github.com/Starlink/starjava/'
            elif 'github.com/' in code_site:
                # remove /issues, /releases/, /tree subpointers
                parts = code_site.split('github.com/')[1].replace('//', '/').replace('//', '/').split()
                if len(parts) >= 2:
                    repo_url = 'https://github.com/' + parts[0] + '/' + parts[1] + '/'
                else:
                    repo_url = code_site
            elif 'gitlab.com/' in code_site:
                # remove /issues, /releases/, /tree subpointers
                parts = code_site.split('gitlab.com/')[1].replace('//', '/').replace('//', '/').split()
                if len(parts) >= 2:
                    repo_url = 'https://gitlab.com/' + parts[0] + '/' + parts[1] + '/'
                else:
                    repo_url = code_site
            elif 'github.com/' in code_site or 'gitlab.com/' in code_site or 'bitbucket.com/' in code_site:
                repo_url = code_site
            elif 'https://gitlab.' in code_site:
                repo_url = code_site
            elif 'pypi.org/' in code_site:
                repo_url = fetchgit.extract_github_url_from_pypi(code_site)
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
                    except (urllib3.exceptions.DecodeError, requests.exceptions.ContentDecodingError):
                        kvstore.store('badurls', domain)
                    except AssertionError:
                        kvstore.store('badurls', domain)
            # print(url, "repo", repo_url, len(bib_urls))
            if repo_url is None:
                print("    no repo found for", code_sites)
                continue
            _, other_code_sites, other_bib_urls, _ = repos.get(repo_url, (None, [], [], ''))
            repos[repo_url] = title, sorted(set(code_sites).union(other_code_sites)), sorted(set(bib_urls).union(other_bib_urls)), parent_db

    return repos

if __name__ == '__main__':
    os.environ['GIT_TERMINAL_PROMPT'] = '0'

    parameter = os.environ['QUANTIFIER']  # "commits", "lines_changed" or "days_active"
    use_institutes = os.environ.get('INSTITUTES', '') != ''
    fout = open('outputs/weighted-flamegraph-%s%s.txt' % (parameter, '-institutes' if use_institutes else ''), 'w')
    parent_sample = [(i, 'JOSS') for i in iterate_joss_list()] + [(i, 'ASCL') for i in iterate_ascl()]
    repos = get_software_list(parent_sample)

    years_stats = Counter()
    num_with_citation_file = 0
    num_repos = 0
    
    reference_date = datetime.fromisoformat('2025-01-01T00:00:00+00:00')
    activities = set()
    bib_urls_seen = set()
    all_results = []
    project_durations = []
    fout2 = open('outputs/scientific-software.txt', 'w')
    fout3 = open('outputs/scientific-software-contributions-%s%s.txt' % (parameter, '-institutes' if use_institutes else ''), 'w')
    print()
    print("checking impact...")
    ndismissed_dups = 0
    ndismissed_impact_error = 0
    ndismissed_impact_low = 0
    ndismissed_impact_zero = 0
    ndismissed_git_nocontrib = 0
    ndismissed_git_error = 0
    njoss = 0
    nascl = 0
    for i, (repo_url, (title, code_sites, bib_urls, parent_db)) in enumerate(repos.items()):
        if ' '.join(bib_urls) in bib_urls_seen:
            ndismissed_dups += 0
            continue
        bib_urls_seen.add(' '.join(bib_urls))
        print("[%d/%d] ***" % (i+1, len(repos)), parent_db, repo_url, [bibcode_query(b).replace('bibcode:','') for b in bib_urls])
        try:
            project_impact = get_impact(bib_urls)
        except IndexError as e:
            print("    IndexError:", e)
            ndismissed_impact_error += 1
            continue
        except ads.exceptions.APIResponseError as e:
            print("    APIResponseError:", e)
            ndismissed_impact_error += 1
            break
        if parent_db == 'JOSS':
            njoss += 1
        if parent_db == 'ASCL':
            nascl += 1
        fout2.write("%s;%s;%d;%s\n" % (repo_url, bib_urls[0], project_impact, title))
        fout2.flush()
        if project_impact == 0:
            print("    no impact found for", bib_urls)
            ndismissed_impact_low += 1
            continue
        if project_impact < 10:
            print("    low impact, skipping")
            ndismissed_impact_zero += 1
            continue
        # get people's names & ORCID
        print("  getting authors for %s" % ([bibcode_query(b).replace('bibcode:','') for b in bib_urls]))
        authors = get_authors(bib_urls)
        print("    %s impact %d by %s" % (repo_url, project_impact, list(authors.keys())))
        print("  authors:", authors)

        project_name = repo_url.strip('/').split('/')[-1]
        significant_contributors, top_contributor_contributions = [], None
        results_here = {}
        try:
            filelist = fetchgit.get_git_filelist(repo_url).split()
            if 'CITATION.cff' in filelist:
                num_with_citation_file += 1
            results_here['has_CITATION.cff'] = 'CITATION.cff' in filelist
            results_here['has_github_tests'] = any(f.startswith('.github/workflows/') and f.endswith('.yml') for f in filelist)
            results_here['has_circleci_tests'] = '.circleci/workflows/config.yml' in filelist
            results_here['has_travis_tests'] = '.travis.yml' in filelist
            results_here['has_gitlab_tests'] = '.gitlab-ci.yml' in filelist
            results_here['has_jenkins_tests'] = 'Jenkinsfile' in filelist
            results_here['parent_db'] = parent_db
            num_repos += 1
            fetchgit.add_git_activity(repo_url, reference_date, activities)
            significant_contributors, top_contributor_contributions = fetchgit.get_significant_contributors(repo_url, parameter)
            if top_contributor_contributions is not None:
                significant_contributors_deduplicated = deduplicate_authors(authors, significant_contributors)
                results_here['contributors'] = significant_contributors_deduplicated
                #significant_contributors_deduplicated = significant_contributors
                # write out person's contribution proportional to impact of the software and days invested
                significant_insitutes_deduplicated = list(translate_to_institutional_contributors(
                    significant_contributors_deduplicated, authors))
                results_here['institutes'] = significant_insitutes_deduplicated
                if use_institutes:
                    significant_contributors_deduplicated = significant_insitutes_deduplicated
                for contributor, ncontributions, _, _ in significant_contributors_deduplicated:
                    fout.write('%s;%s %d\n' % (contributor.replace(';', ','), project_name.replace(';', ','), ncontributions * project_impact))
                    fout3.write('%s;%s;%d;%d\n' % (contributor.replace(';', ','), project_name.replace(';', ','), ncontributions, project_impact))
                fout.flush()
                fout3.flush()
                
                commit_activity = fetchgit.get_git_commit_by_year(repo_url, 'days_active')
                years_stats.update(commit_activity)

                pubdate = get_pubdate(bib_urls)
                project_start_date = fetchgit.get_git_startdate(repo_url)
                _, nchanged, nadded, ndel, nfiles = fetchgit.get_git_startsize(repo_url)
                results_here['commit_activity'] = dict(commit_activity)
                results_here['bib_urls'] = bib_urls
                results_here['pubdate'] = (pubdate.year, pubdate.month, pubdate.day)
                results_here['repo_start_date'] = (project_start_date.year, project_start_date.month, project_start_date.day)
                results_here['repo_start_commit_stats'] = (nchanged, nadded, ndel, nfiles)
                results_here['repo_url'] = repo_url
                results_here['code_sites'] = code_sites
                results_here['paper_title'] = title
                results_here['paper_authors'] = authors
                results_here['project_impact'] = project_impact
                results_here['project_name'] = project_name
                
                # add to project duration
                if project_start_date is not None and pubdate is not None:
                    results_here['project_duration'] = (pubdate - project_start_date).days
                    project_durations.append((pubdate.year, project_impact, (pubdate - project_start_date).days))
                all_results.append(results_here)
            else:
                ndismissed_git_nocontrib += 1

        except subprocess.CalledProcessError as e:
            print("    failure:", repo_url, e)
            ndismissed_git_error += 1
    print()
    print("completed:", num_repos, num_with_citation_file, '%.2f%%' % (num_with_citation_file * 100 / num_repos))
    print(all_results[0])
    print("writing result database")
    
    with open('outputs/scientific-software-contributions-%s.json' % (parameter), 'w') as jsonout:
        json.dump(all_results, jsonout, indent=2)

    # iterate through days
    #active_days = {day for day, _ in activities}
    developers_active = set()
    num_developers_active = defaultdict(set)
    for day, email in activities:
        num_developers_active[day].add(email)
        developers_active.add(email)
    print(f"# of developers tracked: {len(developers_active)}")
    with open('outputs/active_developers.txt', 'w') as fdevout:
        for day_i in tqdm.trange(min(num_developers_active.keys()), max(num_developers_active.keys()) + 1):
            fdevout.write('%d\t%d\t%s\n' % (
                day_i, len(num_developers_active[day_i]), (reference_date + timedelta(days=day_i)).date().isoformat()))

    with open('outputs/basicstats.tex', 'w') as fstatsout:
        fstatsout.write(f'''
        \\newcommand{{\\ndismisseddups}}[0]{{{ndismissed_dups}}}
        \\newcommand{{\\ndismissedimpacterr}}[0]{{{ndismissed_impact_error}}}
        \\newcommand{{\\numASCL}}[0]{{{nascl}}}
        \\newcommand{{\\numJOSS}}[0]{{{njoss}}}
        \\newcommand{{\\nsample}}[0]{{{nascl+njoss}}}
        \\newcommand{{\\ndismissedimpactlow}}[0]{{{ndismissed_impact_low}}}
        \\newcommand{{\\ndismissedimpactzero}}[0]{{{ndismissed_impact_zero}}}
        \\newcommand{{\\nrepos}}[0]{{{num_repos}}}
        \\newcommand{{\\ndismissedgiterror}}[0]{{{ndismissed_git_error}}}
        \\newcommand{{\\ndismissedgitnocontrib}}[0]{{{ndismissed_git_nocontrib}}}
        \\newcommand{{\\nreposcontrib}}[0]{{{len(all_results)}}}
        \\newcommand{{\\ndevs}}[0]{{{len(developers_active)}}}
        ''')
    
"""
    with open('outputs/scientific-software-year.txt', 'w') as fout:
        for year, year_stat in years_stats.items():
            fout.write('%d %d\n' % (year, year_stat))
    years = sorted(years_stats.keys())
    plt.plot(years, [years_stats[current_year] / 300 for current_year in years], 'o-')
    plt.xlabel('Year')
    plt.ylabel('# of developer person-years')
    plt.savefig('outputs/active_number.pdf')
    plt.close()

    # plot mean project durations over time
    avg_durations = []
    for current_year in sorted({year for year, impact, duration in project_durations}):
        impacts_here, durations_here = zip(*[(impact, duration) for year, impact, duration in project_durations if year == current_year])
        number_of_projects_published = len(impacts_here)
        mean_duration = np.average(durations_here, weights=impacts_here)
        avg_durations.append((current_year, mean_duration))
        plt.scatter(durations_here, impacts_here, label=current_year)
    plt.savefig('outputs/project_impact_duration.pdf')
    plt.close()
    plt.plot(
        [year for year, duration in avg_durations],
        [duration for year, duration in avg_durations],
        'o-', color='k')
    plt.savefig('outputs/project_durations.pdf')
    plt.close()
"""

