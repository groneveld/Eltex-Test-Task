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


def parse_by_markers(markers, line, is_onebyone):
    start_index = 0
    result = []
    addition = 0
    for start, end in markers:
        value_start = start_index
        if start:
            value_start = line.find(start, start_index)
        if end:
            value_end = line.find(end, value_start + len(start))
        else:
            value_end = len(line)
        result.append(line[value_start + len(start):value_end])
        if is_onebyone:
            addition = len(end)
        start_index = value_end + addition
    return result


def start_reading(file):
    block = []
    sub_dictionary = {}
    route_table = {'route_table': {'next_hop': {}}}
    first_line_markers = [('', ' '), ('/', ']'), (' ', ','), ('c ', '')]
    other_lines_markers = [('to ', ' '), ('via ', '')]
    for line in file:
        line = line.replace('\n', '')
        if line[0] != ' ':
            result = parse_by_markers(first_line_markers, line, True)
            if len(block) > 0:
                sub_dictionary = blocks_to_dictionary(block, sub_dictionary)
                block.clear()
        else:
            result = parse_by_markers(other_lines_markers, line, True)
        block.append(result)
    sub_dictionary = blocks_to_dictionary(block, sub_dictionary)
    route_table['route_table']['next_hop'] = sub_dictionary
    return route_table


def file_writing(file_name, route_table):
    try:
        with open(file_name, "x") as write_file:
            json.dump(route_table, write_file)
    except FileExistsError:
        with open(file_name, "w") as write_file:
            json.dump(route_table, write_file)
    except PermissionError:
        print("No access for writing in file %s" % file_name)


if __name__ == '__main__':
    log_file_name = ""
    json_file_name = ""
    for param in sys.argv:
        if param.find('.log') != -1:
            log_file_name = param
        if param.find('.json') != -1:
            json_file_name = param
    if log_file_name == "" or json_file_name == "":
        print("Wrong arguments. There are should be *.log and *.json files")
    else:
        try:
            log_file = open(log_file_name)
        except FileNotFoundError:
            print("File with name %s was not found" % log_file_name)
        except PermissionError:
            print("No access for reading file %s" % log_file_name)
        else:
            route_table = start_reading(log_file)
            log_file.close()
            file_writing(json_file_name, route_table)
