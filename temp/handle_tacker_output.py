import demjson


def decode_tabular_output(t, none_value=None):
    if t[-1] != '\n': t += '\n'
    lines = unicode(t).split('\n')
    first = 0
    message = ''
    decode_entry = lambda x, y: (x, demjson.decode(y.replace("u'", "'"))) if (len(y) > 0 and y[0] == '{') else (x, y)
    ret = None

    try:
        # Get first tabular line
        for line in lines:
            if line[0] == '+':
                break
            else:
                message += line
                first += 1

        # Get headers
        headers = [k.strip() for k in lines[first + 1].split('|')[1:-1]]

        # For Field/Value yield dictionary {field:value}
        if headers[0] == 'Field' and headers[1] == 'Value':
            ret = {u'message': message[:-1]}
            last_field = None
            for line in lines[first + 3:-2]:
                entry = tuple(k.strip() for k in line.split('|')[1:-1])
                if entry[0] != '':
                    last_field = entry[0]
                    ret.update([decode_entry(*entry)])
                else:
                    if not isinstance(ret[last_field], list): ret[last_field] = [ret[last_field]]
                    ret[last_field].append(entry[1])

        # For other cases yield dictionary list[{column-0:value-0},...,{column-n:value-n}]
        else:
            ret = []
            for line in lines[first + 3:-2]:
                ret.append(dict(map(decode_entry, headers, [k.strip() for k in line.split('|')[1:-1]])))

        return ret
    except:
        raise

import pprint
pprint.PrettyPrinter(indent=4).pprint(decode_tabular_output(open('vnf-list.txt').read()))
pprint.PrettyPrinter(indent=4).pprint(decode_tabular_output(open('sfc-classifier-list.txt').read()))
pprint.PrettyPrinter(indent=4).pprint(decode_tabular_output(open('vnf-create.txt').read()))
pprint.PrettyPrinter(indent=4).pprint(decode_tabular_output(open('sfc-show.txt').read()))
