Key Architects of modern astrophysics
=====================================

Software is concrete scientific methodology

Open source software is reproducible scientific methodology.

Astronomy research and outreach to the public prospers thanks to open data access and
tools that make the insights accessible, reproducible, and interpretable for
learning about the physical processes.

However, despite underpinning modern astronomy, software development is still 
under-appreciated, in part because it is largely invisible
This project tries to change this, and show the hard work and its impact on astronomy.

**Who are the most important scientists in this area, connecting observational data to physics?**

Method
--------

**Parent sample**:

* ASCL.net projects

  * with papers listed and linked to ADS
  * with code repository listed, which is either a git repository or a website containing a link to a git repository

A limitation is that non-git projects are excluded.

**Visualisation**:

Treemap with names sized proportional to contribution to astronomy.

Make groups in simulation codes, statistics tools, visualisations, ...?

**Contribution**:

We measure the contribution of a scientist by the product of two factors,
one accounting for the importance and impact of the software project,
and one accounting for the time invested on the development.

* Git contribution = number of days where commits where made.

  * This is better than number of commits
  * This is better than lines added or lines changed, because the latter

* Impact = number of citations to paper

Results
-------

.. image:: https://github.com/deepthought-initiative/architects-of-modern-astronomy/blob/main/outputs/weighted-flamegraph-days_active.txt_withouttiny.png?raw=true

Dropping the top 10 largest projects to see the smaller ones better...

.. image:: https://github.com/deepthought-initiative/architects-of-modern-astronomy/blob/main/outputs/weighted-flamegraph-days_active.txt_withouttiny_withoutmajor.png?raw=true

`open as PDF <https://github.com/deepthought-initiative/architects-of-modern-astronomy/blob/main/outputs/weighted-flamegraph-days_active.txt_withouttiny_withoutmajor.pdf?raw=true>`_

Dependency tree analysis
------------------------

* (currently from https://github.com/JohannesBuchner/space-of-inference-spaces/) from some conda tree with a few astronomy packages.

  * from there, obtain github URL, and make a treemap by contributions

`--> dependency tree as PDF <https://github.com/deepthought-initiative/architects-of-modern-astronomy/blob/main/outputs/tree.pdf?raw=true>`_

A future work would be to use the ASCL above and  

* identify pip dependencies

  * how? trying to pip install, somehow finding pypi name

    * in git repo README find "pip install" or "-m pip install" command or pypi link (badge)
    * guess pypi name from git repository name

* or identify conda dependencies

  * how? trying to conda install, somehow finding conda-forge name

    * in git repo README find "conda install" or "mamba install" command or conda-forge link (badge)
    * guess pypi name from git repository name

From these dependencies, using pypi or conda feedstock, identify github link to project repository.

For each github repo, identify paper:

* ideally from github repo citation standard CITATION.cff
* if already identified on ASCL, link to that
* paper linked in the start page (arxiv or ads)
* otherwise, give up.

GDPR-related privacy notice
===========================
Please open an issue or pull request to contact me.
Please find the data protection contact information at https://www.mpe.mpg.de/data-protection-d

What this project does
- Purpose: We study public software development in astronomy and related fields by analyzing public git repositories and publication metadata to produce aggregate statistics and figures about projects, contributors, institutions, countries, and topics.
- Outputs: We publish aggregate/anonymized findings in papers and in this repository. We do not publish raw personal data.

Personal data we process
- Identifiers and commit metadata from public git logs: names, email addresses, usernames/handles, commit timestamps, commit counts and derived statistics.
- Publication/registry metadata used to map affiliations: author names, ORCID iDs, affiliations, institution names, countries, and paper identifiers (e.g., from ADS/DOI metadata).
- We do not intentionally process special-category data and do not perform profiling for decisions affecting individuals.

Sources
- Public version-control hosting services and mirrors (e.g., GitHub, GitLab, Bitbucket, institutional GitLab instances).
- Public bibliographic/identifier services (e.g., ADS, Crossref/DOI metadata, ORCID records, publisher sites).
- Project websites and READMEs that link to the above.

How we process and minimize personal data
- We read public git logs to compute project- and institution-level statistics.
- Email addresses from git logs may be used transiently as unique keys for deduplication and linkage, then are discarded. They are not published or shared. The exceptions are rare cases where commits lack author name, in which case the email addresses are used as names.
- We do not attempt to re-identify individuals beyond what is necessary to link public author identities across sources.
- Public outputs contain only aggregated or anonymized data. We do not release person-level datasets.

Lawful basis for processing:
- Legitimate interests (GDPR Art. 6(1)(f)): Our interest is to advance scientific understanding of research software and its ecosystem using data that individuals have made public. We apply data minimization, do not use data for marketing, and publish only aggregated results. Individuals can object and opt out (see below).

Transparency and Article 14
- We obtain personal data indirectly from public sources. Direct notification of every affected developer would involve disproportionate effort given the large scale. We rely on Art. 14(5)(b) GDPR and provide this public notice, accept objections/opt-outs, and apply strong safeguards.

Recipients and sharing
- We do not share raw personal data with third parties.
- We publish aggregated/anonymized statistics, figures, and code in scientific venues and this repository.
- If you open an issue or pull request to opt out, your GitHub username and any information you include will be visible publicly per GitHub’s terms.

International transfers
- Processing is performed locally on a MPE institute laptop in Germany. If any service providers outside the EEA are used (e.g., GitHub issues), transfers occur under the applicable mechanism (e.g., adequacy decision, EU–US Data Privacy Framework, or Standard Contractual Clauses).

Retention
- Transient identifiers from git logs (e.g., raw email strings) are not retained beyond the processing needed for linkage.
- Working datasets with person-level rows (without raw emails) are retained only for as long as necessary to complete analysis and peer review and are then deleted or irreversibly anonymized.
- Aggregated/anonymized outputs may be retained indefinitely for research transparency.

Security
- Access-controlled storage, least-privilege access, encrypted storage/transit where applicable, and separation of identifiers from analytical variables. Public outputs exclude personal identifiers.

Your rights
- You can request access, rectification, erasure, restriction, or object to processing of your personal data. Where applicable, you can exercise data portability. We do not use your data for automated decision-making producing legal or similarly significant effects.
- How to object/opt out:
  - Preferred: open an issue or pull request in this repository with the repository URL(s) to exclude and the scope (e.g., exclude my person-level record, exclude my project, or both).
  - Alternatively: email jbuchner@mpe.mpg.de with “Opt-out: [Project name]” in the subject and include the repository URL(s) and the email/name/handle that appears in the git log so we can locate the records. The project will be removed from the analysis. This project will then list the project repository URL as a URL to skip in analysis.
- We will honor reasonable requests prospectively and, where feasible, remove your records from future analyses and from working datasets not yet published.

Children
- This research is not directed at children.

Changes to this notice
- We may update this notice and will timestamp changes. Material changes will be reflected in the repository README.

