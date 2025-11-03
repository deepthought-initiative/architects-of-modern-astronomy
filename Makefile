all: outputs/weighted-flamegraph-days_active.txt.png
all: outputs/weighted-flamegraph-days_active-institutes.txt.png
all: outputs/weighted-flamegraph-days_active.txt_withouttiny.png
all: outputs/weighted-flamegraph-days_active-institutes.txt_withouttiny.png
all: outputs/weighted-flamegraph-days_active.txt_withoutmajor.png
all: outputs/weighted-flamegraph-days_active-institutes.txt_institutes.png
all: countries_withouttiny.pdf withoutmajor.pdf withouttiny.pdf abstractumap1.pdf

countries_withouttiny.pdf: outputs/weighted-flamegraph-days_active-institutes.txt_countries_withouttiny.pdf
	cp $^ $@
withoutmajor.pdf: outputs/weighted-flamegraph-days_active.txt_withoutmajor.pdf
	cp $^ $@
withouttiny.pdf: outputs/weighted-flamegraph-days_active.txt_withouttiny.pdf
	cp $^ $@

abstractumap%.pdf: abstractumap.py outputs/scientific-software-contributions-days_active.json
	python3 $< $*
#all: outputs/flamegraph-days_active.txt.png 

outputs/flamegraph-%.txt: fetchgit.py
	QUANTIFIER=$* python3 $^

%-institutes.txt_institutes.png %-institutes.txt_institutes.pdf:  treemapviz.py %-institutes.txt
	python3 $^ --cut-tiny --countries

%_withouttiny.png %_withouttiny.pdf: treemapviz.py %
	python3 $^ --cut-tiny

%_withoutmajor.png %_withoutmajor.pdf: treemapviz.py %
	python3 $^ --cut-major

%_withouttiny_withoutmajor.png %_withouttiny_withoutmajor.pdf: treemapviz.py %
	python3 $^ --cut-tiny --cut-major

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
