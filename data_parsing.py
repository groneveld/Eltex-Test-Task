import json
import sys


def blocks_to_dictionary(block, dictionary):
    destination = block[0][0]
    preference = block[0][1]
    age = block[0][2]
    metric = block[0][3]
    sub_dictionary = {'preference': preference, 'metric': metric, 'age': age, 'via': None}
    for i in range(1, len(block)):
        hop = block[i][0]
        via = block[i][1]
        sub_dictionary['via'] = via
        if hop not in dictionary.keys():
            dictionary[hop] = {destination: sub_dictionary}
        else:
            dictionary[hop][destination] = sub_dictionary
    return dictionary


def parse_by_markers(markers, line):
    start_index = 0
    result = []
    for start, end in markers:
        value_start = start_index
        if start:
            value_start = line.find(start, start_index)
        if end:
            value_end = line.find(end, value_start + len(start))
        else:
            value_end = len(line)
        result.append(line[value_start + len(start):value_end])
        start_index = value_end + len(end)
    return result


if __name__ == '__main__':
    for param in sys.argv:
        if param.find('.log') != -1:
            log_file = param
        if param.find('.json') != -1:
            json_file = param
    route_table = {'route_table': {'next_hop': {}}}
    block = []
    sub_dictionary = {}
    with open(log_file) as reader:
        for line in reader:
            line = line.replace('\n', '')
            if line[0] != ' ':
                new_block = True
                markers = [('', ' '), ('/', ']'), (' ', ','), ('c ', '')]
                result = parse_by_markers(markers, line)
            else:
                new_block = False
                markers = [('to ', ' '), ('via ', '')]
                result = parse_by_markers(markers, line)
            if new_block:
                if len(block) > 0:
                    sub_dictionary = blocks_to_dictionary(block, sub_dictionary)
                block.clear()
            block.append(result)
    route_table['route_table']['next_hop'] = sub_dictionary
    with open(json_file, "w") as write_file:
        json.dump(route_table, write_file)