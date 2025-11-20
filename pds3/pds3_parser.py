import regex as re

def add_kv(kvd, k, v):
    if isinstance(v, str):
        if re.match(r'(\((.*)?\))|(\{(.*)?\})', v.strip()): #string enclosed in parantheses or curly brackets
            #separate parenthetical lists into lists
            listv = [e.strip() for e in v.strip()[1:-1].split(',')]
            #send each element through add_kv individually
            v = [add_kv({}, n, elem)[n] for n, elem in enumerate(listv)]
        elif not v.startswith('"') and re.search(r'<\w+>', v): #1+ alphanumeric characters enclosed in angle brackets
            #turn values of the form "VALUE <UNIT>" into dictionaries with value and unit keys
            try:
                v = {'value': re.search(r'^(.*?)\s*<.*?>', v).group(1), 'unit': re.search(r'<\w+>', v).group(0)[1:-1]} #the string before whitespace and characters enclosed in angle brackets, plus 1+ alphanumeric characters enclosed in angle brackets
            except:
                pass
        else:
            #reserved XML character replacement
            xml_dict = {'&': 'amp', '<': 'lt', '>': 'gt'}
            for c in xml_dict:
                pattern = r'\%s(?!.*;)' % c #reserved character not followed by 0+ other characters and then a semi-colon
                v = re.sub(pattern, '&%s;' % xml_dict[c], v)

    if k in kvd:
        #if a keyword is already in the dictionary, either turn the value into a list or add to the value list already there
        if not isinstance(kvd[k], list):
            kvd[k] = [kvd[k]]
        kvd[k].append(v)
    else:
        kvd[k] = v

    return kvd

def parse(label):
    kv_dict = {}
    ostack = []
    mchar = {'(': ')', '{': '}', '"': '"'}

    with open(label) as f:
        lbl_lines = [line for line in f]

    for n, line in enumerate(lbl_lines):
        #split each line into tidy keyword=value pairs
        k, v = ([p.strip() for p in line.split('=')][:2] + [None]*2)[:2]

        if v is not None:
            #multi-line values will start with (, {, or "
            if v.startswith(tuple(mchar.keys())):
                mstop = mchar[v[0]] #multi-line ends with closing version of what it opened with
                ml_count = n
                current_line = v
                while mstop not in current_line or (ml_count == n and v == '"'):
                    #iterate through lines until you get to the stop character, but make sure you keep going if the first line is just a "
                    ml_count += 1
                    current_line = lbl_lines[ml_count]
                    v += ' %s' % current_line
                    #and add each successive line to the multi-line value
            elif k == 'OBJECT':
                #at the start of a new object, add to the object stack and return to the top of the loop
                ostack.append([v, {}])
                continue
            elif k == 'END_OBJECT':
                k, v, = ostack.pop()
                #at the end of an object, remove the most recent object from the stack and assign it to the kw=val pair
            elif v == '':
                v = lbl_lines[n+1]

            if ostack:
                ostack[-1][-1] = add_kv(ostack[-1][-1], k, v)
                #if we're in an object, this line's kw=val pair is added to the object instead of the label dictionary
            else:
                kv_dict = add_kv(kv_dict, k, v)

    return kv_dict
