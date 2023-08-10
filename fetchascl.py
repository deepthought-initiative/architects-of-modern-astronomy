import requests_cache
import requests
from bs4 import BeautifulSoup
from fetchgit import mem, get_significant_contributors, extract_github_url_from_pypi
import subprocess
import tqdm
import os
from collections import Counter
import ads
from urllib.parse import unquote
from namematch import same_author

#import fetchgit
#fetchgit.requests = requests.Session(timeout=5, )

requests_cache.install_cache('demo_cache', allowable_methods=('GET', 'POST'), expire_after=3600 * 24 * 7)

@mem.cache
def get_ascl_list():
    """Get list of astronomy software packages"""
    urls = []
    response = requests.get('https://ascl.net/code/all/limit/3294/listmode/compact')
    soup = BeautifulSoup(response.content, "html.parser")
    for title_span in soup.find_all('span', class_='title'):
        urls.append('https://ascl.net/' + title_span.find('a')['href'])
    return urls

@mem.cache
def get_code_info(url):
    """Get code website and list of papers"""
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    
    # Extract Code site
    code_site_element = soup.find('dt', text='Code site:')
    code_sites = [a.get('href') for a in code_site_element.find_next('dd').find_all('a', href=True)] if code_site_element else []

    # Extract Described in
    described_in_element = soup.find('dt', text='Described in:')
    return code_sites, [a.get('href') for a in described_in_element.find_next('dd').find_all('a')] if described_in_element else []

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
        response = requests.get(code_site)
        soup = BeautifulSoup(response.content, "html.parser")
        links = soup.find_all("a", href=True)
        for link in links:
            if link.text == 'theme': # footer text
                continue
            link_url = link["href"]
            if not link_url or '?' in link_url or link_url.count('/') < 3:
                continue
            link_url = '/'.join(link_url.split('/')[:5])
            if link_url.startswith('http://github.com/'):
                return link_url.replace('http://github.com/', 'https://github.com/')
            if link_url.startswith('https://github.com/'):
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

@mem.cache
def get_authors(bib_urls):
    """Get paper authors and ORCID"""
    fields = ['bibcode', 'author', 'orcid_user', 'orcid_pub', 'orcid_other', 'title', 'eid', 'identifier']
    authors = {}
    for bib_url in bib_urls:
        if 'adsabs.harvard.edu' in bib_url:
            query = bibcode_query(bib_url)
            for p in ads.SearchQuery(q=query, fl=fields, sort="date"):
                print(p.author, p.orcid_user, p.orcid_pub, p.orcid_other)
                for author, orcid_user, orcid_pub, orcid_other in zip(p.author, p.orcid_user if p.orcid_user is not None else ['-']*1000, p.orcid_pub if p.orcid_pub is not None else ['-']*1000, p.orcid_other if p.orcid_other is not None else ['-']*1000):
                    orcid = None
                    if orcid_user != '-':
                        orcid = orcid_user
                    if orcid_pub != '-':
                        orcid = orcid_pub
                    if orcid_other != '-':
                        orcid = orcid_other
                    
                    if authors.get(author) is None:
                        authors[author] = orcid
    return authors
            

@mem.cache
def get_impact(bib_urls):
    """Get project impact (citations of papers using it)"""
    fields = ['bibcode', 'author', 'year', 'citation_count', 'doi', 'title', 'eid', 'identifier']
    query = ' OR '.join(['citations(%s)' % bibcode_query(bib_url) for bib_url in bib_urls if 'adsabs.harvard.edu' in bib_url])
    print(query)
    if query == '':
        return 0
    papers = [p for p in ads.SearchQuery(q=query, fl=fields, sort="date", max_pages=100)]
    total_citations = sum((p.citation_count for p in papers if p.citation_count))
    return total_citations


def deduplicate_authors(authors, contributors):
    """Reduce authors."""
    author_map = {}
    values = {}
    
    for author, value in contributors:
        for author2 in authors:
            # print("CMP(", author, "||", author2,")")
            if same_author(author, author2):
                author_map[author] = author2
                # print("==", author, author2)
                break
        newauthor = author_map.get(author, author)
        values[newauthor] = values.get(newauthor, 0) + value

    authors_done = {}
    deduplicated_contributors = []
    for author, value in contributors:
        newauthor = author_map.get(author, author)
        if newauthor not in authors_done:
            authors_done[newauthor] = True
            deduplicated_contributors.append((newauthor, values[newauthor]))
    
    return deduplicated_contributors

if __name__ == '__main__':
    #for url in sorted(get_ascl_list()):
    #    print(url)
    #    code_site, bib_urls = get_code_info(url)
    #    time.sleep(0.1)
    
    #c = Counter([get_code_info(url)[0].split('://')[1].strip('/').split('/')[0] for url in get_ascl_list()])
    #print(c.most_common(20))

    parameter = os.environ['QUANTIFIER']  # "commits", "lines_changed" or "days_active"
    fout = open('outputs/weighted-flamegraph-%s.txt' % parameter, 'w')
    for url in tqdm.tqdm(sorted(get_ascl_list())[::int(os.environ.get('DIR', '1'))]):
        # print(url)
        code_sites, bib_urls = get_code_info(url)
        if len(bib_urls) == 0:
            print("no papers found for", code_sites)
            continue

        for code_site in code_sites:
            # print(url, "info", code_site, bib_urls)
            repo_url = None
            if 'github.com/' in code_site or 'gitlab.com/' in code_site or 'bitbucket.com/' in code_site:
                repo_url = code_site
            elif 'pypi.org/' in code_site:
                repo_url = extract_github_url_from_pypi(code_site)
            elif code_site.startswith('https://dx.doi.org'):
                pass
            elif code_site.startswith('https://doi.org'):
                pass
            elif code_site.startswith('http') and code_site.split('.')[-1] not in ('.zip', '.tar.gz', '.tar.bz2'):
                try:
                    repo_url = get_git_url2(code_site)
                except requests.exceptions.ConnectTimeout:
                    pass
                except requests.exceptions.ConnectionError:
                    pass
                except AssertionError:
                    pass
            # print(url, "repo", repo_url, len(bib_urls))
            if repo_url is None:
                print("no repo found for", code_sites)
                continue

            # query citations of paper(s) (impact)
            try:
                project_impact = get_impact(bib_urls)
            except IndexError:
                project_impact = 0
            if project_impact == 0:
                print("no impact found for", code_sites)
                continue
            # get people's names & ORCID
            authors = get_authors(bib_urls)
            print(url, "impact", project_impact, "by", authors.keys())
            # print(url, "authors", authors)

            project_name = repo_url.strip('/').split('/')[-1]
            significant_contributors, top_contributor_contributions = [], None
            try:
                significant_contributors, top_contributor_contributions = get_significant_contributors(repo_url, parameter)
                if top_contributor_contributions is not None:
                    significant_contributors_deduplicated = deduplicate_authors(authors, significant_contributors)
                    #significant_contributors_deduplicated = significant_contributors
                    # write out person's contribution proportional to impact of the software and days invested
                    for contributor, ncontributions in significant_contributors_deduplicated:
                        fout.write('%s;%s %d\n' % (contributor, project_name, ncontributions * project_impact))
                    fout.flush()
                break
            except subprocess.CalledProcessError as e:
                print("failure:", repo_url, e)
