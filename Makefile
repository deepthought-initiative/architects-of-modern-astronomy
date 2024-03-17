all: outputs/flamegraph-days_active.txt.png outputs/weighted-flamegraph-days_active.txt.png

outputs/flamegraph-%.txt: fetchgit.py
	QUANTIFIER=$* python3 $^

%.png %.pdf: treemapviz.py %
	python3 $^

outputs/weighted-flamegraph-days_active.txt: fetchascl.py
	QUANTIFIER=days_active python3 $^

outputs/weighted-flamegraph-days_active-institutes.txt: fetchascl.py
	INSTITUTES=1 QUANTIFIER=days_active python3 $^

.PHONY: all # rules that do not correspond to a output file
.SUFFIXES: # disable built-in rules
.SECONDARY: # do not delete intermediate products
.PRECIOUS: # keep all products
