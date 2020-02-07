# -*- coding: utf-8 -*-
"""
Created on Sun Nov 17 17:36:07 2019

@author: Mark
"""

from ReadLiftTags import skip_head, read_entry, read_sense, step_back
from GenerateLexDir import generate_lex_dir
from time import time
import pandas as pd

in_file = 'export.lift'
out_file = 'flexicon.csv'
senses_file = 'flex_senses.csv'

global run_lex_dir
run_lex_dir = False

# decorator
def time_exec(f):
    def g(*args, **kwargs):
        start = time()
        out = f(*args, **kwargs)
        end = time()
        print(str(f), end-start)
        return out
    return g

@time_exec
def main():
    entries_df = get_entries_df()
    get_these_vars(entries_df, entries_df)
    entries_df = entries_df.loc[:,['headword', 'entry_id', 'morph_type',
                                 'pronunciation', 'variant_of', 'these_vars', 'other_forms',
                                 'note', 'sense', 'date', 'date_modified']]

    senses_df = get_senses_df()
    get_these_vars(senses_df, entries_df)
    
    entries_df.to_csv(out_file, encoding='utf8', index=False)   
    senses_df.to_csv(senses_file, encoding='utf8', index=False)
    if run_lex_dir:
        generate_lex_dir(entries_df, senses_df)
  
@time_exec
def get_entries_df():
    entries_df = pd.DataFrame(columns = ['headword', 'entry_id', 'morph_type',
                                 'pronunciation', 'variant_of', 'note', 'sense', 'other_forms',
                                 'date', 'date_modified'])
    with open(in_file, 'rb') as f:
        skip_head(f)
        
        line_bytes = f.readline()
        while line_bytes:
            line_str = line_bytes.decode('utf8').strip()
            
            if line_str == '</lift>':
                break
            
            assert line_str.startswith('<entry'), line_str
            step_back(f, line_bytes)
            this_entry = read_entry(f)
            entries_df.loc[len(entries_df)] = this_entry
            
            line_bytes = f.readline()
    return entries_df

@time_exec
def get_senses_df():
    senses_df = pd.DataFrame(columns = ['sense_id', 'pos', 'gloss', 'def',\
                                       'reverse', 'note'])
    with open(in_file, 'rb') as f:
        line_bytes = f.readline()
        while line_bytes:
            line_str = line_bytes.decode('utf8').strip()
            
            if line_str == '</lift>':
                break
            
            if line_str.startswith('<sense'):
                step_back(f, line_bytes)
                this_sense = read_sense(f)
                senses_df.loc[len(senses_df)] = this_sense
                
            line_bytes = f.readline()
    return senses_df

@time_exec
def get_these_vars(parent_df, entries_df):
    if 'entry_id' in parent_df.columns:
        id_col = 'entry_id'
    else:
        assert 'sense_id' in parent_df.columns
        id_col = 'sense_id'
    these_vars_col = []
    
    for index, row in parent_df.iterrows():
        these_vars = get_vars_for_id(row[id_col], entries_df)
        if these_vars:
            these_vars_col.append(these_vars)
        else:
            these_vars_col.append(None)
        
    parent_df.at[:, 'these_vars'] = these_vars_col
    
def get_vars_for_id(entry_id, entries_df):
    has_var = entries_df[[bool(row) and entry_id in row for row in entries_df['variant_of']]]
    
    these_vars = {}
    for index, row in has_var.iterrows(): 
        var_id = row['entry_id']
        assert entry_id != var_id
        
        var_type = row['variant_of'][entry_id]
        these_vars[var_id] = var_type
    
    return these_vars

def return_dfs():
    return get_entries_df(), get_senses_df()

def set_filenames(in_name=in_file, out_name=out_file, senses_name=senses_file):
    global in_file, out_file, senses_file
    in_file = in_name
    out_file = out_name
    senses_file = senses_name
          
if __name__ == '__main__':
    main()
    run_lex_dir=True