#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb  7 21:16:54 2020

Reads a given .LIFT file
Dumps to JSON.

First system arg is name of LIFT file
Second system arg is name of file to output to,
or empty to return a JSON string instead.

@author: markjosims
"""

import sys
import xml.etree.cElementTree as ET

def main():
    if len(sys.argv) == 1:
        raise TypeError("Please specify LIFT filepath in system arguments.")
    
    lift_file = sys.argv[1]
    
    if len(sys.argv) > 2:
        out_file = sys.argv[2]
        return lift_to_json(lift_file, out_file)
    else:
        return lift_to_json(lift_file)

# reads lift file from given filepath and saves to a .json file
# if out_file is None (or Falsey), returns JSON string instead
def lift_to_json(lift_file, out_file=None):
    lift = ET.parse(lift_file).getroot()
    entries = {}
    
    # [1:] b/c we're skipping the header
    for element in lift[1:]:
        id = element.get('id')
        entries[id] = read_entry(element)
        
def read_entry(entry_element):
    pass

def read_form(form):
    lang = form.get('lang')
    text = form.findall('text')
    text = [get_elem_text(x) for x in text]
    text = text[0] if len(text) == 1 else text
    
    return lang, text

def get_elem_text(elem):
    out = elem.text if elem.text else ''
    for span in elem.findall('span'):
        if span.text:
            out += span.text
        if span.tail:
            out += span.tail
    return out

if __name__ == '__main__':
    main()