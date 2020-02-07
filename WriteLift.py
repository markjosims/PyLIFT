# -*- coding: utf-8 -*-
"""
Created on Wed Jan  8 08:27:37 2020

@author: marks
"""

import pandas as pd
import xml.etree.cElementTree as ET
import lxml.etree as etree
import WriteLiftTags as wlt
from ast import literal_eval

in_file = 'flexiconHDWRDS.csv'
senses_file = 'flex_senses.csv'
lit_cols_flexicon = (
                     'variant_of',
                     'these_vars',
                     'note',
                     'sense',
                     'other_sources'
                    )
lit_cols_senses = (
                   'gloss',
                   'def',
                   'reverse',
                   'note'
                  )

out_file = 'NewExport.lift'

def main():
    flexicon = pd.read_csv(in_file, keep_default_na=False)
    senses_df = pd.read_csv(senses_file, keep_default_na=False, index_col='sense_id')
    for c in lit_cols_flexicon:
        literal_eval_col(flexicon, c)
    for c in lit_cols_senses:
        literal_eval_col(senses_df, c)
    
    wlt.set_doc_lang('mbj')
    wlt.set_analys_lang('en', 'pt')
    wlt.set_senses_df(senses_df)
    root = ET.Element("lift", producer="SIL.FLEx 8.3.12.43172", version="0.13")
    header = ET.parse('header.xml').getroot()
    root.append(header)
    
    for index, row in flexicon.iterrows():
        wlt.write_entry(row, root)
    
    tree = ET.ElementTree(root)
    tree.write(out_file, encoding='utf8')
    
    
    file = etree.parse(out_file)
    out = etree.tostring(file, pretty_print=True, encoding='unicode')
    with open(out_file, 'w', encoding='utf8') as f:
        f.write('<?xml version="1.0" encoding="UTF-8" ?>\n')
        f.write(out)
    
def literal_eval_col(df, col):
    df.at[:, col] = [literal_eval(row) if row else None for row in df[col]]




if __name__ == '__main__':
    main()