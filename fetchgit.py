from datetime import datetime
import os
import joblib
import requests
import subprocess
from bs4 import BeautifulSoup
from collections import defaultdict, Counter


mem = joblib.Memory('.', verbose=False)
@mem.cache
def get_repo_url(project_name):
    """
    From a conda project name, find the github repository
    """
    for branch in 'master', 'main':
        readme_url = f"https://raw.githubusercontent.com/conda-forge/{project_name}-feedstock/{branch}/README.md"
        readme_response = requests.get(readme_url)
        readme_content = readme_response.text

        for readme_line in readme_content.splitlines()[:20]:
            if readme_line.startswith("Home: "):
                return readme_line[6:].strip()
    print(readme_url, readme_response.text[:100])


@mem.cache
def _get_github_significant_contributors(repository_url):
    """
    Return the git authors, sorted by contributions
    """
    contributors_url = f"{repository_url}/contributors?q=contributions&order=desc"
    response = requests.get(contributors_url)
    if response.status_code != 200:
        return [], None
    print('  ', contributors_url, ":", response.text[:200])
    contributors_data = response.json()

    top_contributor_contributions = contributors_data[0]["contributions"]
    significant_contributors = []

    for contributor in contributors_data:
        contributions = contributor["contributions"]
        contribution_percentage = contributions / top_contributor_contributions * 100

        if contribution_percentage >= 10:
            significant_contributors.append(contributor["html_url"])

    print(significant_contributors, top_contributor_contributions)
    return significant_contributors, top_contributor_contributions

@mem.cache
def get_git_first_commit_log(repo_url, logargs, full=False):
    """Fetch a commit log"""
    # Clone the repository locally
    subprocess.check_call(["rm", "-rf", "temp-git-repo"])
    subprocess.check_call(["git", "clone", "--bare"] + ([] if full else ["--filter=blob:none"]) + [repo_url, "temp-git-repo"])

    # Get the commit authors and their statistics
    git_log_command = ["git", "--git-dir=temp-git-repo/", "rev-list", "--max-parents=0", "HEAD"]
    result = subprocess.run(git_log_command, stdout=subprocess.PIPE, text=True, errors='ignore')
    log_output = ''
    for commit_id in result.stdout.strip().split('\n'):
        # Get the commit authors and their statistics
        git_log_command = ["git", "--git-dir=temp-git-repo/", "log"] + list(logargs) + [commit_id]
        result = subprocess.run(git_log_command, stdout=subprocess.PIPE, text=True, errors='ignore')
        log_output += result.stdout
    return log_output

@mem.cache
def get_git_commit_log(repo_url, logargs, full=False):
    """Fetch a commit log"""
    # Clone the repository locally
    subprocess.check_call(["rm", "-rf", "temp-git-repo"])
    subprocess.check_call(["git", "clone", "--bare"] + ([] if full else ["--filter=blob:none"]) + [repo_url, "temp-git-repo"])

    # Get the commit authors and their statistics
    git_log_command = ["git", "--git-dir=temp-git-repo/", "log"] + list(logargs)
    result = subprocess.run(git_log_command, stdout=subprocess.PIPE, text=True, errors='ignore')
    log_output = result.stdout
    return log_output


def count_active_days(commit_dates):
    """Count unique commit dates, using a 1 day window."""
    active_days = 0
    if commit_dates:
        sorted_dates = sorted(commit_dates)
        start_date = sorted_dates[0]

        for i in range(1, len(sorted_dates)):
            current_date = sorted_dates[i]
            if (current_date - start_date).total_seconds() >= 86400:
                active_days += 1
                start_date = current_date

        active_days += 1  # Count the last interval

    return active_days

#@mem.cache
def get_git_commit_authors(log_output):
    """Get statistics of contributing authors to git repositories"""
    commit_authors = defaultdict(lambda : dict(commits=0, lines_changed=0, days_active=set()))

    # Process the log output to extract commit authors and statistics
    current_author = None
    current_date = None
    for line in log_output.splitlines():
        if line.startswith(' '):
            assert current_author is not None
            parts = line.strip().split(", ")
            commit_authors[current_author]["commits"] += 1
            for part in parts[1:]:
                commit_authors[current_author]["lines_changed"] += int(part.split()[0])
            commit_authors[current_author]["days_active"].add(current_date)
        elif line.strip() != '':
            parts = line.strip().split(' | ')
            current_author, current_date_string = parts[0], parts[-1]
            current_date = datetime.fromisoformat(current_date_string)
            commit_authors[current_author]["commits"] = 0
            commit_authors[current_author]["days_active"].add(current_date)

    for author_stats in commit_authors.values():
        author_stats["first_contribution_date"] = min(author_stats["days_active"]).year
        author_stats["last_contribution_date"] = max(author_stats["days_active"]).year
        author_stats["days_active"] = count_active_days(author_stats["days_active"])
    return dict(commit_authors)


@mem.cache
def get_git_filelist(repo_url):
    """Get list of current files in git repository"""
    # set bits grouped by year, day of year, and email address
    """Fetch a commit log"""
    # Clone the repository locally
    subprocess.check_call(["rm", "-rf", "temp-git-repo"])
    subprocess.check_call(["git", "clone", "--depth", "1", "--bare"] + [repo_url, "temp-git-repo"])

    # Get the commit authors and their statistics
    git_ls_command = ["git", "--git-dir=temp-git-repo/", "ls-tree", "-r", "HEAD"]
    result = subprocess.run(git_ls_command, stdout=subprocess.PIPE, text=True, errors='ignore')
    ls_output = result.stdout
    return ls_output


def get_git_commit_by_year(repository_url, parameter):
    """Get statistics of contributing authors to git repositories"""
    # set bits grouped by year, day of year, and email address
    log_output = get_git_commit_log(repository_url, ["--format=%ae | %aI"], full=parameter == 'lines_changed')

    current_year = None
    # split log by calendar year
    year_logs = defaultdict(list)
    for line in log_output.splitlines():
        if line.startswith(' '):
            year_logs[current_year].append(line)
        elif line.strip() != '':
            parts = line.strip().split(' | ')
            current_author, current_date_string = parts[0], parts[-1]
            current_year = datetime.fromisoformat(current_date_string).year
            year_logs[current_year].append(line)

    year_stats = Counter()
    # count total number of active days, summing over all authors
    for year, year_log in year_logs.items():
        for author, stats in get_git_commit_authors('\n'.join(year_log)).items():
            year_stats[year] += int(stats["days_active"])
    return year_stats

def get_git_startdate(repository_url):
    """Get statistics of contributing authors to git repositories"""
    # set bits grouped by year, day of year, and email address
    log_output = get_git_commit_log(repository_url, ["--format=%ae | %aI"], full=False)

    for line in log_output.splitlines()[::-1]:
        if line.startswith(' '):
            pass
        elif line.strip() != '':
            parts = line.strip().split(' | ')
            current_author, current_date_string = parts[0], parts[-1]
            return datetime.fromisoformat(current_date_string).date()
    return None

def get_git_startsize(repository_url):
    """Get statistics of contributing authors to git repositories"""
    # set bits grouped by year, day of year, and email address
    log_output = get_git_first_commit_log(repository_url, ["--format=[X] %H | %aI | %ae", "--numstat", "--shortstat"], full=False)
    #log_output = get_git_commit_log(repository_url, ["--format=[X] %H | %aI | %ae", "--numstat", "--shortstat", "--reverse", "-n1"], full=False)
    current_date_string = None

    nfiles = 0
    for line in log_output.splitlines():
        if line.startswith('[X] ') and ' | ' in line:
            parts = line[4:].strip().split(' | ')
            if len(parts) >= 3:
                current_commit, current_date_string, current_author = parts[0], parts[1], parts[2]
        elif ' changed,' in line:
            numbers = [int(part.strip().split()[0]) for part in line.split(',')]
            nchanged = numbers[0]
            nadded = numbers[1] if len(numbers) > 1 else 0
            ndel = numbers[2] if len(numbers) > 2 else 0
            print("-->", nchanged, nadded, ndel, nfiles)
            return datetime.fromisoformat(current_date_string).date(), nchanged, nadded, ndel, nfiles
        elif line.startswith(' ') or line.strip() == '':
            pass
        else:
            nfiles += 1
    return datetime.fromisoformat(current_date_string).date() if current_date_string is not None else current_date_string, None, None, None, None

#@mem.cache
def get_significant_contributors(repository_url, parameter):
    """Get author statistics for a git repository"""
    log_output = get_git_commit_log(repository_url, ["--format=%aN | %aI"], full=parameter == 'lines_changed')
    commit_authors = get_git_commit_authors(log_output)
    # print('  ', commit_authors)
    top_contributor_commits = max((v[parameter] for v in commit_authors.values()))

    significant_contributors = []

    for contributor, contributions in commit_authors.items():
        commits = contributions[parameter]
        commits_percentage = commits / top_contributor_commits * 100

        if commits_percentage >= 10:
            significant_contributors.append((contributor, contributions[parameter], contributions["first_contribution_date"], contributions["last_contribution_date"]))

    print('  significant_contributors: ', significant_contributors, top_contributor_commits)
    return significant_contributors, top_contributor_commits


@mem.cache
def extract_github_url_from_pypi(pypi_url):
    """Get a github URL from a pypi URL."""
    response = requests.get(pypi_url)
    soup = BeautifulSoup(response.content, "html.parser")

    links = []
    # Find the project links section
    for project_links_section in soup.find_all("ul", class_="vertical-tabs__list"):
        links += project_links_section.find_all("a", href=True)

    # Fallback: Look for links inside the project description
    project_description = soup.find("div", class_="project-description")
    if project_description:
        links += project_description.find_all("a", href=True)

    for link in links:
        link_url = link["href"]
        if not link_url or '?' in link_url or link_url.count('/') > 5 or link_url.count('/') < 3:
            continue
        print('  ', link_url)
        if link_url.startswith('http://github.com/'):
            return link_url.replace('http://github.com/', 'https://github.com/')
        if link_url.startswith('https://github.com/'):
            return link_url
    return None

def build_flamegraph(fout, project_names, parameter):
    for project_name in project_names:
        print(project_name)
        home_url = get_repo_url(project_name)
        if not home_url or home_url == "":
            print("  fall-back to pypi lookup")
            home_url = 'https://pypi.org/project/%s/' % project_name
        if home_url.startswith('https://pypi.org/project/'):
            print("  getting repo from pypi ...")
            repo_url = extract_github_url_from_pypi(home_url)
        else:
            repo_url = home_url

        if repo_url is None:
            print("  no git URL found:", project_name, home_url)
            continue
        if not repo_url.startswith("https://github.com/"):
            print("  non-github URL:", repo_url)

        #api_url1 = repo_url.replace("https://github.com/", "https://api.github.com/repos/")
        #api_url = api_url1.replace("http://github.com/", "https://api.github.com/repos/")
        significant_contributors, top_contributor_contributions = [], None
        try:
            significant_contributors, top_contributor_contributions = get_significant_contributors(repo_url, parameter)
            if top_contributor_contributions is not None:
                print(f"Project: {project_name}, {top_contributor_contributions} {significant_contributors}")
                for contributor, ncontributions in significant_contributors:
                    fout.write('%s;%s %d\n' % (contributor, project_name, ncontributions))
                fout.flush()
        except subprocess.CalledProcessError as e:
            print(repo_url, e)

if __name__ == '__main__':
    # go through dependency tree
    dot_file_path = "pipdeps-light.dot"

    project_names = []
    with open(dot_file_path, "r") as dot_file:
        for line in dot_file:
            if "->" not in line and line.startswith('\t'):
                project_name = line.strip().strip('"')
                if project_name:
                    project_names.append(project_name)

    parameter = os.environ['QUANTIFIER']  # "commits", "lines_changed" or "days_active"
    fout = open('outputs/flamegraph-%s.txt' % parameter, 'w')
    build_flamegraph(fout, project_names, parameter)
