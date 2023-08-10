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

Dependency tree analysis
------------------------

* (currently from https://github.com/JohannesBuchner/space-of-inference-spaces/) from some conda tree with a few astronomy packages.
  * from there, obtain github URL, and make a treemap by contributions

--> output/fig2.png

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

For each github repo, identify paper.
* ideally from github repo citation standard CITATION.cff
* if already identified on ASCL, link to that
* paper linked in the start page (arxiv or ads)
* otherwise, give up.
