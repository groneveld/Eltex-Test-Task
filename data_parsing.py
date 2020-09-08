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
    route_table = {'route_table': {'next_hop': {}}}
    with open('dump.log') as reader:
        for line in reader:
            line = line.replace('\n', '')
            if line[0] != ' ':
                markers = [('', ' '), ('/', ']'), (' ', ','), ('c ', '')]
                result = parse_by_markers(markers, line)
                print(result)
            else:
                markers = [('to ', ' '), ('via ', '')]
                result = parse_by_markers(markers, line)
                print(result)