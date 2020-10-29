"""
Process a collection of XML dumps looking for the introduction and removal of {{Beginnetje}} templates
and assume the introduction represents a quality label ("E") and the removal represents the quality 
label "D". Note: This script does not yet handle reverts (e.g. vandalism).  To do that, look into 
the mwreverts libraray

USAGE:
    nlwiki_template_extractor (-h|--help)
    nlwiki_template_extractor <xml-dump>... 
        [--namespace=<num>...] [--processes=<num>]
        [--output=<path>]

OPTIONS
    -h --help   Print this documentation
    <xml-dump>  Path to an XML dump to process (could be compressed gzip, bz2, etc.)
    --namespace=<num>  MediaWiki namespaces to include in processing [default: <all_namespaces>]
    --processes=<num>  Number of parallel processes to use for extraction [default: <cpu_count>]
    --output=<path>    Where to write the output file [default: <stdout>]

"""
import sys
import docopt
import mwxml
import json
import re
import multiprocessing

STUB_TEMPLATE_NAME = "beginnetje"
TEMPLATE_RE = re.compile(r'{{\s*{0}'.format(STUB_TEMPLATE_NAME))  #TODO: Make sure this actually works

def main():
    args = docopt.docopt(__doc__)
    
    paths = args['<xml-dump>']
    if args['--processes'] == "<cpu_count>":
        threads = multiprocessing.cpu_count()
    else:
        threads = int(args['--processes'])
    
    if args['--namespaces'] == "<all_namespaces>":
        namespaces = None
    else:
        namespaces = set(int(v) for v in args['--namespaces'])
    
    if args['--output'] == "<stdout>":
        output = sys.stdout
    else:
        output = open(args['--output'], "w")
    
    run(paths, threads, namespaces, output)

def run(paths, threads, namespaces, output):
    
    def process_template_changes(dump, path):
        for page in dump:
            if namespaces is not None and page.namespace not in namespaces:
                continue
            template_appeared = False
            for revision in page:
                if not template_appeared and TEMPLATE_RE.search(revision.text): #TODO: Make sure this evaluated to False when we don't find anything
                    template_appeared = True
                    yield revision.id, "E"
                elif template_appeared and not TEMPLATE_RE.search(revision.text):
                    yield revision.id, "D"
                    break
    
    for rev_id, label in mwxml.map(process_template_changes, paths, threads):
        # Write the label to the output
        output.write(json.dumps({'rev_id': rev_id, 'label': label}) + "\n")
        
if __name__ == "__main__":
    main()
