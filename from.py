#!/usr/bin/env python
#-----------------------------------------
# Google translate fix for LaTeX documents
# Copyright (c) Dmitry R. Gulevich 2020
# GNU General Public License v3.0
#-----------------------------------------
import re
import regex
import sys
import pickle
import argparse

def make_spaces(text):
    return regex.sub(r'(\\[a-zA-Z0-9]+)([\p{Script=Hiragana}\p{Script=Katakana}\p{Script=Han}])', r'\1 \2', text)

def convert_from(filename):
    if(re.search('.txt$',filename)==None):
        sys.exit('The input should be .txt file. Exit.')

    print('Input file:',filename)

    ### Load LaTeX data from binary files
    with open(filename, 'r') as fin:
        source = fin.read()
    with open ('gtexfix_comments', 'rb') as fp:
        comments = {token_id: v for token_id, v in enumerate(pickle.load(fp))}
    with open ('gtexfix_commands', 'rb') as fp:
        # [2.x]
        commands = {token_id: v for token_id, v in enumerate(pickle.load(fp))}
    with open ('gtexfix_latex', 'rb') as fp:
        # [1.x]
        latex = {token_id: v for token_id, v in enumerate(pickle.load(fp))}

    ### Replace weird characters introduced by translation
    trtext=re.sub('\u200B',' ',source)

    ### Fix spacing
    trtext = re.sub(r'\\ ',r'\\',trtext)
    trtext = re.sub(' ~ ','~',trtext)
    # This process will be executed later -> [Adjust space before parenthesis]
    #trtext = re.sub(' {','{',trtext)

    ### Restore LaTeX and formulas
    here=0
    newtext=''
    nl=0
    nc=0
    corrupted=[]
    for m in re.finditer(r'\[ *[012][\.][0-9]+\]',trtext):
        t=int( re.search(r'(?<=[\[ ])[012](?=[\.])',m.group()).group() )
        n=int( re.search(r'(?<=[\.])[0-9]+(?=\])',m.group()).group() )
        if(t==1):
            #if(n<nl):
            #    print('Token ',m.group(),'found in place of [%d.%d]. Edit manually and run again.'%(t,nl))
            #    break
            #while(nl!=n):
            #    corrupted.append('[%d.%d]'%(t,nl))
            #    nl+=1
            newtext += trtext[here:m.start()] + latex[n]
            del latex[n]
            nl+=1
        elif(t==2):
            #if(n<nc):
            #    print('Token ',m.group(),'found in place of [%d.%d]. Edit manually and run again.'%(t,nc))
            #    break
            #while(nc!=n):
            #    corrupted.append('[%d.%d]'%(t,nc))
            #    nc+=1
            partial_text = trtext[here:m.start()] + commands[n]
            # [Adjust space before parenthesis]
            partial_text = re.sub(r' {([^\\])',r'{\1',partial_text)
            newtext += partial_text
            del commands[n]
            nc+=1
        here=m.end()
    newtext += trtext[here:]
    trtext=make_spaces(newtext)

    ### Restore comments
    here=0
    ncomment=0
    newtext=''
    for m in re.finditer('___GTEXFIXCOMMENT[0-9]*___',trtext):
        n=int( re.search('[0-9]+',m.group()).group() )
        #if(n!=ncomment):
        #    print('Comment token ',m.group(),'is broken. Stopping.')
        #    break
        newtext += trtext[here:m.start()] + comments[n]
        del comments[n]
        ncomment+=1
        here=m.end()
    newtext += trtext[here:]
    trtext=newtext

    ### Save the processed output to .tex file
    output_filename = re.sub('.txt$','.tex',filename)
    with open(output_filename, 'w') as translation_file:
        translation_file.write(trtext)
    print('Output file:',output_filename)

    ### Report the corrupted tokens
    #if(corrupted==[]):
    if not comments and not commands and not latex:
        print('No corrupted tokens. The translation is ready.')
    else:
        print('Corrupted tokens detected:',end=' ')
        #for c in corrupted:
        #    print(c,end=' ')
        for c in sorted(latex):
            print(f'[1.{c}]', end= ' ')
        for c in sorted(commands):
            print(f'[2.{c}]', end= ' ')
        for c in sorted(comments):
            print(f'___GTEXFIXCOMMENT{c}___', end= ' ')
        print()
        print('To improve the output manually change the corrupted tokens in file',filename,'and run   from.py again.')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('filename')
    args = parser.parse_args()
    convert_from(args.filename)

if __name__ == '__main__':
    main()
