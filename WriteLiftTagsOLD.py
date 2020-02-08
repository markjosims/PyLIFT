# -*- coding: utf-8 -*-
"""
Created on Wed Jan  8 20:18:55 2020

@author: marks
"""

import xml.etree.cElementTree as ET
import pandas as pd

# global variables

doc_lang = ''
analys_lang = ('',)
sense_df = pd.DataFrame()

def tag_globals():
    global entry_tags, sense_tags
    entry_tags = {
                  'lexical-unit':write_lu,
                  'pronunciation':write_pronunc,
                  'note':write_note,
                  'variant_of':write_var,
                  'sense':write_sense,
                  'other_sources':write_custom
                 }
    sense_tags = {
                  'grammatical-info':write_pos,
                  'gloss':write_gloss,
                  'definition':write_def,
                  'reversal':write_rev,
                  'note':write_note
                 }

def write_entry(row, root):
    attrib = {
              'dateCreated': row['date'],
              'dateModified': row['date'],
              'id' : row['entry_id'],
              'guid' : '_'.join( row['entry_id'].split(sep='_')[1:] )
             }
    entry = ET.SubElement(root, 'entry', attrib)
    
    for tag, funct in entry_tags.items():
        funct(row, entry)

def write_lu(row, entry):
    hdwrd = row['headword']
    lu = ET.SubElement(entry, 'lexical-unit')
    form = ET.SubElement(lu, 'form', lang=doc_lang)
    ET.SubElement(form, 'text').text = hdwrd
    
def write_pronunc(row, entry):
    phonet = row['pronunciation']
    pronunc = ET.SubElement(entry, 'pronunciation')
    form = ET.SubElement(pronunc, 'form', lang=doc_lang)
    ET.SubElement(form, 'text').text = phonet
    
def write_note(row, entry):
    note_dict = row['note']
    if not note_dict:
        return
    for k, v in note_dict.items():
        if type(v) is str:
            pass
        elif len(v) == 1:
            v = v[0]
        else:
            v = ' ,'.join(v)
        
        if k.startswith('Note'):
            note = ET.SubElement(entry, 'note')
        else:
            note = ET.SubElement(entry, 'note', type=k)
        form = ET.SubElement(note, 'form', lang=analys_lang[0])
        ET.SubElement(form, 'text').text = v
        
def write_var(row, entry):
    var_dict = row['variant_of']
    if not var_dict:
        return
    
    for k, v in var_dict.items():
        assert type(v) is dict
        
        attr = {'ref':k}
        v_type = v.pop('type')
        if not v_type.startswith('null'):
            attr['type'] = v_type
        relation = ET.SubElement(entry, 'relation')
        summ = v.pop('summary') if 'summary' in v else None
        
        for sub_k, sub_v in v.items():
            ET.SubElement(relation, 'trait', name=sub_k, value=sub_v)
            
        if summ:
            field = ET.SubElement(relation, 'field', type='summary')
            form = ET.SubElement(field, 'form', lang=analys_lang[0])
            ET.SubElement(form, 'text').text = summ

def write_custom(row, entry):
    custom_fields = row['other_sources']
    if not custom_fields:
        return

    for k, v in custom_fields.items():
        assert k, k
        field = ET.SubElement(entry, 'field', type=k)
        form = ET.SubElement(field, 'form', lang=analys_lang[0])
        ET.SubElement(form, 'text').text = v
            
def write_sense(row, entry):
    senses = row['sense']
    if not senses:
        return
    for sense_id in senses:
        sense = ET.SubElement(entry, 'sense', id=sense_id)
        sense_row = senses_df.loc[sense_id]
        
        for tag, funct in sense_tags.items():
            funct(sense_row, sense)
            
def write_pos(row, sense):
    pos = row['pos']
    ET.SubElement(sense, 'grammatical-info', value=pos)
    
def write_gloss(row, sense):
    glosses = row['gloss']
    if not glosses:
        return
    for k, v in glosses.items():
        this_gloss = ET.SubElement(sense, 'gloss', lang=k)
        ET.SubElement(this_gloss, 'text').text = v
        
def write_def(row, sense):
    defs = row['def']
    if not defs:
        return
    definition = ET.SubElement(sense, 'definition')
    for k, v in defs.items():
        form = ET.SubElement(definition, 'form', lang=k)
        ET.SubElement(form, 'text').text = v
        
def write_rev(row, sense):
    revs = row['reverse']
    if not revs:
        return
    for k, v in revs.items():
        reversal = ET.SubElement(sense, 'reversal', type=k)
        form = ET.SubElement(reversal, 'form', lang=k)
        ET.SubElement(form, 'text').text = v

def set_doc_lang(s):
    global doc_lang
    assert type(s) is str
    doc_lang = s
    
def set_analys_lang(*t):
    global analys_lang
    assert all( type(x) is str for x in t ), t
    analys_lang = (*t,)
    
def set_senses_df(df):
    global senses_df
    senses_df = df

tag_globals()