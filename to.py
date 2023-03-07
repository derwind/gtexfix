#!/usr/bin/env python
#-----------------------------------------
# Google translate fix for LaTeX documents
# Copyright (c) Dmitry R. Gulevich 2020
# GNU General Public License v3.0
#-----------------------------------------
import re
import sys
import pickle
import argparse

# It's usually difficult to process nested begin-end such as '\begin{subequations}\begin{align}...\end{align}\end{subequations}'.
ignore_subequations = True

def search_right_curly_bracket(text, start):
    bracket_count = 0
    for i, c in enumerate(text[start:]):
        if c == '{':
            bracket_count += 1
        if c == '}':
            bracket_count -= 1
            if bracket_count <= 0:
                return start + i + 1
    return start + 1

def convert_to(filename, ignore_no_end_patterns=False):
    if(re.search('.tex$',filename)==None):
        sys.exit('The input should be .tex file. Exit.')

    print('LaTeX file:',filename)

    with open(filename, 'r') as source_file:
        source = source_file.read()

    ### Search for possible token conflicts
    conflicts=re.findall(r'\\[ *[012][\\.][0-9]+\\]',source)
    if(conflicts!=[]):
        print('Token conflicts detected: ',conflicts)
        sys.exit('Tokens may overlap with the content. Change tokens or remove the source of conflict.')
    else:
        print('No token conflicts detected. Proceeding.')

    ### Hide everything that is beyond \begin{document} ... \end{document}
    latex=[]
    bdoc=re.search(r'\\begin{document}',source)
    edoc=re.search(r'\\end{document}',source)
    if(bdoc!=None):
        preamble=source[:bdoc.end()]
        latex.append(preamble)
        if(edoc!=None):
            text = '[1.0]' + source[bdoc.end():edoc.start()]
            postamble=source[edoc.start():]
        else:
            text = '[1.0]' + source[bdoc.end():]
            postamble=[]
    else:
        text=source
        postamble=[]

    ### Hide all comments
    recomment = re.compile(r'(?<!\\)[%].*')
    comments=[]
    for m in recomment.finditer(text):
        comments.append(m.group())
    global ncomment
    ncomment=0
    def repl_comment(obj):
        global ncomment
        ncomment += 1
        return '___GTEXFIXCOMMENT%d___'%(ncomment-1)
    text=recomment.sub(repl_comment,text)
    with open('gtexfix_comments', 'wb') as fp:
        pickle.dump(comments, fp)

    ### Hide LaTeX constructs \begin{...} ... \end{...}
    start_values=[]
    end_values=[]

    begin_patterns = r'\\begin{ *(equation)\** *}|\\begin{ *(align)\** *}|\\begin{ *(alignat)\** *}|\\begin{ *(figure)\** *}|\\begin{ *(eqnarray)\** *}|\\begin{ *(multline)\** *}' \
        +r'|\\begin{ *(thebibliography) *}|\\begin{ *(verbatim)\** *}|\\begin{ *(table)\** *}|\\begin{ *(align)\** *}' \
        +r'|\\begin{ *(displaymath)\** *}|\\begin{ *(gather)\** *}'
    if not ignore_subequations:
        begin_patterns += r'|\\begin{ *(subequations)\** *}'
    if not ignore_no_end_patterns:
        begin_patterns += r'|\\[a-z]*(ref) *{.*?}|\\(cite)\S* *{.*?}|\\(footnote) *{.*?}|\\(index) *{.*?}'
        # XXX: detect end of figure
        begin_patterns += r'|(\\end{ *figure\** *})|(\\end{ *table\** *})'
    end_patterns = r'\\end{ *equation\** *}|\\end{ *align\** *}|\\end{ *alignat\** *}|\\end{ *figure\** *}|\\end{ *eqnarray\** *}|\\end{ *multline\** *}' \
        +r'|\\end{ *thebibliography *}|\\end{ *verbatim\** *}|\\end{ *table\** *}|\\end{ *align\** *}' \
        +r'|\\end{ *displaymath\** *}|\\end{ *gather\** *}'
    if not ignore_subequations:
        end_patterns += r'|\\end{ *subequations\** *}'

    no_end_patterns = {}
    in_figure = False
    in_table = False
    i = 0
    for m in re.finditer(begin_patterns,text):
        # equation, align, alignat, etc.
        key = next((item for item in m.groups() if item), None)
        if in_figure and 'end' in key and 'figure' in key:
            in_figure = False
            continue
        if in_table and 'end' in key and 'table' in key:
            in_table = False
            continue

        if not ignore_no_end_patterns:
            # ignore \ref, \cite etc. inside figure blocks
            if in_figure or in_table:
                continue

            if key in ['ref', 'cite', 'footnote', 'index']:
                no_end_patterns[i] = m.start()

        start_values.append(m.start())
        in_figure = key == 'figure'
        in_table = key == 'table'
        i += 1

    nitems=len(start_values)
    iter = re.finditer(end_patterns,text)
    for i in range(nitems):
        # if next pattern has no end pattern
        if not ignore_no_end_patterns and i in no_end_patterns:
            start = no_end_patterns[i]
            end = search_right_curly_bracket(text, start)
            end_values.append(end)
        else:
            m = next(iter)
            end_values.append(m.end())

    ### report problems if any exists
    if len(end_values) != nitems:
        min_len = min(len(start_values), len(end_values))
        for start, end in zip(start_values[:min_len], end_values[:min_len]):
            print(start, text[start:start+70])
            print('...')
            print(text[end-70:end], end)
            assert start <= end, f'{len(end_values)=}, {nitems=}'
            print('-'*20)
    assert len(end_values)==nitems, [len(end_values), nitems]

    if(nitems>0):
        newtext=text[:start_values[0]]
        for neq in range(nitems-1):
            latex.append(text[start_values[neq]:end_values[neq]])
            newtext += '[1.%d]'%(len(latex)-1) + text[end_values[neq]:start_values[neq+1]]
        latex.append(text[start_values[nitems-1]:end_values[nitems-1]])
        newtext += '[1.%d]'%(len(latex)-1) + text[end_values[nitems-1]:]
        text=newtext

    if(postamble!=[]):
        latex.append(postamble)
        text += '[1.%d]'%(len(latex)-1)
    with open('gtexfix_latex', 'wb') as fp:
        pickle.dump(latex, fp)

    ### Replace LaTeX commands, formulas and comments by tokens
    # Regular expression r'(\$+)(?:(?!\1)[\s\S])*\1' for treatment of $...$ and $$...$$ from:
    # https://stackoverflow.com/questions/54663900/ how-to-use-regular-expression-to-remove-all-math-expression-in-latex-file
    recommand = re.compile(r'___GTEXFIXCOMMENT[0-9]*___|\\title|\\chapter\**|\\section\**|\\subsection\**|  \\subsubsection\**|~*\\footnote[0-9]*|(\$+)(?:(?!\1)[\s\S])*\1|~*\\\w*\s*{[^}]*}\s*{[^}]*}|~*\\\w*\s*{[^}]    *}|~*\\\w*')
    commands=[]
    for m in recommand.finditer(text):
        commands.append(m.group())
    global nc
    nc=0
    def repl_f(obj):
        global nc
        nc += 1
        return '[2.%d]'%(nc-1)
    text=recommand.sub(repl_f,text)
    with open('gtexfix_commands', 'wb') as fp:
        pickle.dump(commands, fp)

    ### Save the processed output to .txt file
    #limit=30000 # Estimated Google Translate character limit
    limit=200000
    filebase = re.sub('.tex$','',filename)
    start=0
    npart=0
    for m in re.finditer(r'\.\n',text):
        if(m.end()-start<limit):
            end=m.end()
        else:
            output_filename = filebase+'_%d.txt'%npart
            npart+=1
            with open(output_filename, 'w') as txt_file:
                txt_file.write(text[start:end])
            print('Output file:',output_filename)
            start=end
            end=m.end()
    output_filename = filebase+'_%d.txt'%npart
    with open(output_filename, 'w') as txt_file:
        txt_file.write(text[start:])
    print('Output file:',output_filename)
    print('Supply the output file(s) to Google Translate')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ignore-no-end-patterns', action='store_true', help=r'\ref{...} or \cite{...} or \footnote{...} etc. are ignored and are not processed.')
    parser.add_argument('filename')
    args = parser.parse_args()
    convert_to(args.filename, args.ignore_no_end_patterns)

if __name__ == '__main__':
    main()
