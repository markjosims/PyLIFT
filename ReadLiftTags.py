# -*- coding: utf-8 -*-
"""
Created on Tue Nov  5 21:10:45 2019

@author: Mark
"""

import re

re_span = re.compile(r"</?span( lang='(en|pt|mbj)')?>")
re_form = re.compile(r"</?form( lang='(en|pt|mbj)')?>")
re_text = re.compile(r'</?text[^>]*?>')
re_gloss = re.compile(r"</?gloss( lang='(en|pt|mbj)')?>")
re_rev = re.compile(r"</?reversal type='(en|pt|mbj)'>")

        
def tag_globals():
    global entry_tags, entry_keys, sense_tags, sense_keys
    entry_tags = {'<pronunciation':read_pronunciation,
                  '<note':read_note,
                  '<relation type':read_variant,
                  '<lexical-unit>':read_lu,
                  '<sense':read_sense_wrapper,
                  "<trait  name='morph-type'":read_morph_type,
                  '<field type="':read_custom_field
                  }
    entry_keys =   {'dateModified':'date',
                    '<pronunciation':'pronunciation',
                    '<note':'note',
                    '<relation type':'variant_of',
                    '<lexical-unit>':'headword',
                    '<sense':'sense',
                    "<trait  name='morph-type'":'morph_type',
                    '<field type="':'other_forms'
                    }
    sense_tags = {'<definition>':read_definition,
                  '<grammatical-info':read_pos,
                  '<note':read_note,
                  '<gloss':read_gloss,
                  '<reversal type':read_reversal
                  }
    sense_keys = {'<definition>':'def',
                  '<grammatical-info':'pos',
                  '<note':'note',
                  '<gloss':'gloss',
                  '<reversal type':'reverse'
                  }

def skip_head(r):
    line, line_bytes = r_d_bytes(r)
    if line.startswith('<?xml'):
        while line != '</header>':
            line = read_decode(r)
    else:
        assert line.startswith('<entry')
        step_back(r, line_bytes)
        
def read_entry(r, id_only=False):
    open_tag = read_decode(r)
    assert open_tag.startswith('<entry')
    
    entry_id = get_xml_attr(open_tag, 'id')
    if entry_id.startswith('='):
        entry_id = ' ' + entry_id
    if not id_only:
        entry_data = {k:None for k in entry_keys.values()}
        entry_data['note'] = {}
        entry_data['sense'] = []
        entry_data['variant_of'] = {}
        entry_data['other_forms'] = {}
        entry_data['entry_id'] = entry_id
        entry_data['date'] = get_xml_attr(open_tag, 'dateCreated')
        entry_data['date_modified'] = get_xml_attr(open_tag, 'dateModified')
    
    line, line_bytes = r_d_bytes(r)
    while True:
        for tag, funct in entry_tags.items():
            if line.startswith(tag):
                step_back(r, line_bytes)
                key = entry_keys[tag]
                data = funct(r)
                if not id_only:
                    if key == 'sense':
                        entry_data[key].append(data)
                    elif not data:
                        pass
                    else:
                        assert not entry_data[key]
                        entry_data[key] = data
                break
        else:
            assert line == '</entry>', entry_data
            break
        
        line, line_bytes = r_d_bytes(r)
    if id_only:
        return entry_id
    entry_data = {k:(v if v else None) for k, v in entry_data.items()}
    headword = entry_data['headword']
    headword = ' '+headword if (type(headword) is str and headword.startswith('=')) else headword
    entry_data['headword'] = headword
    return entry_data

def read_sense(r, id_only=False):
    open_tag = read_decode(r)
    assert open_tag.startswith('<sense')
    
    sense_id = get_xml_attr(open_tag, 'id')
    if not id_only:
        sense_data = {k:None for k in sense_keys.values()}
        sense_data['sense_id'] = sense_id
    line, line_bytes = r_d_bytes(r)
    while True:
        for tag, funct in sense_tags.items():
            if line.startswith(tag):
                step_back(r, line_bytes)
                key = sense_keys[tag]
                data = funct(r)
                if not id_only:
                    assert not sense_data[key]
                    sense_data[key] = data
                break
        else:
            # if current line did not match any tags
            # end of sense
            assert line == '</sense>', line
            break
        
        line, line_bytes = r_d_bytes(r)
        
    if id_only:
        return sense_id
    sense_data = {k:(v if v else None) for k, v in sense_data.items()}
    return sense_data

def read_sense_wrapper(r):
    return read_sense(r, id_only=True)

def read_pronunciation(r):
    open_tag = read_decode(r)
    assert open_tag == '<pronunciation>'
    s = read_decode(r)
    s = read_form(s)
    end_tag = read_decode(r)
    assert end_tag == '</pronunciation>', end_tag
    return s

def read_definition(r):
    open_tag = read_decode(r)
    assert open_tag == '<definition>'
    # definition can frame multiple arguments
    # for multiple languages
    # save all to dict
    this_def = {}
    s = read_decode(r)
    while s != '</definition>':
        lang = get_xml_attr(s, 'lang')
        assert lang not in this_def.keys(), lang
        def_str = read_form(s)
        this_def[lang] = def_str
        s = read_decode(r)
    return this_def

def read_variant(r):
    variants = {}
    line, line_bytes = r_d_bytes(r)
    while line.startswith('<relation'):
        ref, data = get_variant(line, r)
        i=1
        while ref=='null' and ref in variants:
            tmp = ref + '_' + str(i)
            if tmp not in variants:
                ref = tmp
                break
            i+=1
        assert ref not in variants
        variants[ref] = data
        line, line_bytes = r_d_bytes(r)
    step_back(r, line_bytes)
    return variants

def get_variant(s, r):
    ref = get_xml_attr(s, 'ref')
    ref = ref if ref else 'null'
    var_type = get_xml_attr(s, 'type')
    data = {'type': var_type}
    s = read_decode(r)
    while s.startswith('<trait '):
        name = get_xml_attr(s, 'name')
        value = get_xml_attr(s, 'value')
        assert name in ('variant-type', 'complex-form-type', 'is-primary', 'hide-minor-entry'), name
        if name in data and type(data[name]) is tuple:
            data[name] = (*data[name], value)
        elif name in data:
            data[name] = (data[name], value)
        else:
            data[name] = value
        s = read_decode(r)
    summ = None
    if s == "<field type='summary'>":
       summ = read_decode(r)
       summ = read_form(summ)
       data['summary'] = summ
       end_tag = read_decode(r)
       assert end_tag == '</field>'
       s = read_decode(r)
    assert s == '</relation>', s + ' ' + str(data)
    return ref, data

def read_note(r):
    notes = {}
    line, line_bytes = r_d_bytes(r)
    while line.startswith('<note'):
        note_type, this_note = get_note(line, r)
        i=1
        while note_type in notes:
            tmp = note_type + '_' + str(i)
            if tmp not in notes:
                note_type = tmp
                break
            i+=1
        notes[note_type] = this_note
        line, line_bytes = r_d_bytes(r)
    step_back(r, line_bytes)
    return notes

def get_note(s, r):
    if s == '<note>':
        note_type = 'Note'
    else:
        note_type = get_xml_attr(s, 'type')
    s = read_decode(r)
    notes = []
    while s.startswith('<form '):
        notes.append(read_form(s))
        s = read_decode(r)
    end_tag = s
    assert end_tag == '</note>', end_tag
    notes = ', '.join(notes)
    return note_type, notes
        
def read_span(s):
    s = re_span.sub("", s)
    assert 'span>' not in s, s
    return s

def read_form(s):
    s = read_span(s)
    s = re_form.sub("", s)
    s = read_text(s)
    assert 'form>' not in s, s
    return s.strip()

def read_gloss(r):
    glosses = {}
    line, line_bytes = r_d_bytes(r)
    while line.startswith('<gloss'):
        this_gloss, lang = get_gloss(line)
        assert lang not in glosses
        glosses[lang] = this_gloss
        
        line, line_bytes = r_d_bytes(r)
    step_back(r, line_bytes)
    return glosses
    
def get_gloss(s):
    lang = get_xml_attr(s, 'lang')
    assert lang in ('pt', 'en'), lang
    s = read_span(s)
    s = re_gloss.sub("", s)
    s = read_text(s)
    assert 'gloss>' not in s
    return (s.strip(), lang)

def read_custom_field(r):
    data = {}
    line, line_bytes = r_d_bytes(r)
    while line.startswith('<field'):
        datum_type = get_xml_attr(line, 'type')
        line = read_decode(r)
        datum = read_form(line)
        assert datum_type not in data
        data[datum_type] = datum
        line = read_decode(r)
        assert line.startswith('</field>')
        line, line_bytes = r_d_bytes(r)
    step_back(r, line_bytes)
    return data

def read_reversal(r):
    revs = {}
    line, line_bytes = r_d_bytes(r)
    while line.startswith('<reversal'):
        this_rev, lang = get_reversal(line, r)
        assert lang not in revs
        revs[lang] = this_rev
        
        line, line_bytes = r_d_bytes(r)
    step_back(r, line_bytes)
    return revs

def get_reversal(s, r):
    lang = get_xml_attr(s, 'lang')
    assert lang in ('pt', 'en'), lang
    s = read_span(s)
    s = re_rev.sub("", s)
    s = read_form(s)
    assert '<reversal' not in s
    end_tag = read_decode(r)
    assert end_tag == '</reversal>'
    return (s.strip(), lang)

def read_text(s):
    s = re_text.sub("", s)
    assert 'text>' not in s
    return s.strip()

def read_lu(r):
    open_tag = read_decode(r)
    assert open_tag == '<lexical-unit>', open_tag
    s = read_decode(r)
    lang = get_xml_attr(s, 'lang')
    assert lang == 'mbj', lang
    s = read_form(s)
    end_tag = read_decode(r)
    assert end_tag == '</lexical-unit>', end_tag
    return s.strip()
    
def read_morph_type(r):
    s = read_decode(r)
    assert get_xml_attr(s, 'name') == 'morph-type'
    return get_xml_attr(s, 'value')

def read_pos(r):
    s = read_decode(r)
    end_tag = read_decode(r)
    assert end_tag == '</grammatical-info>', end_tag
    return get_xml_attr(s, 'value')

def read_decode(r):
    line = r.readline()
    line = line.decode('utf8')
    line = line.replace(',',';')
    line = line.replace('"', "'")
    line = line.strip()
    return line

def r_d_bytes(r):
    these_bytes = r.readline()
    line = these_bytes.decode('utf8')
    line = line.replace(',',';')
    line = line.replace('"', "'")
    line = line.strip()
    return line, these_bytes

def step_back(r, line_bytes):
    offset = len(line_bytes) * -1
    r.seek(offset, 1)

def get_xml_attr(s, label):
    split = s.split(sep="'")
    kwarg_found = False
    for chunk in split:
        if kwarg_found:
            return chunk
        elif chunk.endswith(label+'='):
            kwarg_found = True
    else:
        raise ValueError(f'No kwarg matching label {label} in string {s}.')

tag_globals()