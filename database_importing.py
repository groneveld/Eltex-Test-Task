import json
import sqlite3
import sys
from data_parsing import parse_by_markers
from sqlite3 import Error


def age_convertation_to_str(int_age):
    weeks = int_age // 604800
    days = (int_age - weeks * 604800) // 86400
    hours = (int_age - weeks * 604800 - days * 86400) // 3600
    minutes = (int_age - weeks * 604800 - days * 86400 - hours * 3600) // 60
    seconds = (int_age - weeks * 604800 - days * 86400 - hours * 3600 - minutes * 60)
    string_age = ""
    if weeks > 0:
        string_age += str(weeks) + 'w'
    if days == 0 and weeks > 0:
        string_age += str(days) + 'd '
    if days > 0:
        string_age += str(days) + 'd '
    if hours < 10:
        string_age += '0' + str(hours) + ':'
    else:
        string_age += str(hours) + ':'
    if minutes < 10:
        string_age += '0' + str(minutes) + ':'
    else:
        string_age += str(minutes) + ':'
    if seconds < 10:
        string_age += '0' + str(seconds)
    else:
        string_age += str(seconds)
    return string_age


def print_db(data):
    string = "|{0:^20}|{1:^10}|{2:^10}|{3:^20}|{4:^15}|{5:^15}|"
    print("_" * 97)
    print(string.format("Destination", "Preference", "Metric", "Next Hop", "Interface", "Age"))
    print("-" * 97)
    prev = ""
    for line in data:
        age = age_convertation_to_str(line[4])
        print(string.format(line[1] if line[1] != prev else "", line[2], line[3], line[0], line[5], age))
        prev = line[1]


def db_execute(cursor, query):
    try:
        cursor.execute(query)
    except Error:
        print(Error)
        sys.exit()


def create_tables(cursor):
    db_execute(cursor, "DROP TABLE IF EXISTS next_hop")
    db_execute(cursor, "DROP TABLE IF EXISTS destination")
    db_execute(cursor, "DROP TABLE IF EXISTS hop_to_destination")
    db_execute(cursor, """CREATE TABLE IF NOT EXISTS next_hop
                                  (hop_id INTEGER PRIMARY KEY, 
                                  hop text)
                               """)
    db_execute(cursor, """CREATE TABLE IF NOT EXISTS destination
                                                  (dest_id INTEGER PRIMARY KEY, 
                                                  destination text,
                                                  preference integer,
                                                  metric integer,
                                                  age integer,
                                                  interface text)
                                               """)
    db_execute(cursor, """CREATE TABLE IF NOT EXISTS hop_to_destination
                                          (id INTEGER PRIMARY KEY, 
                                          hop_id integer REFERENCES next_hop(hop_id),
                                          dest_id integer REFERENCES destination(dest_id))
                                       """)


def age_convertation_to_int(string_age):
    length = 5
    if string_age.find('w') != -1:
        markers = [('', 'w'), ('w', 'd'), (' ', ':'), (':', ':'), (':', '')]
    elif string_age.find('d') != -1:
        markers = [('', 'd'), (' ', ':'), (':', ':'), (':', '')]
        length -= 1
    else:
        markers = [('', ':'), (':', ':'), (':', '')]
        length -= 2
    age = parse_by_markers(markers, string_age, False)
    age = list(reversed(age))
    int_age = int(age[0]) + 60 * int(age[1]) + 3600 * int(age[2])
    if length >= 4:
        int_age += 86400 * int(age[3])
    if length == 5:
        int_age += 604800 * int(age[4])
    return int_age


def db_writing(data, cursor):
    for hop, dest in data['route_table']['next_hop'].items():
        db_execute(cursor, "INSERT INTO next_hop (hop) VALUES ('{0}')".format(hop))
        hop_id = cursor.lastrowid
        for key, value in dest.items():
            pref = int(value.get('preference'))
            metric = int(value.get('metric'))
            string_age = value.get('age')
            age = age_convertation_to_int(string_age)
            interface = value.get('via')
            db_execute(cursor,
                       f"""INSERT INTO destination (destination, preference, metric, age, interface) 
                VALUES ('{key}','{pref}','{metric}','{age}','{interface}')""")
            dest_id = cursor.lastrowid
            db_execute(cursor, f"INSERT INTO hop_to_destination (hop_id, dest_id) VALUES ('{hop_id}', '{dest_id}')")


def db_reading(cursor):
    db_execute(cursor, """select next_hop.hop, 
                    destination.destination, destination.preference, destination.metric, destination.age, destination.interface
                    from hop_to_destination 
                    inner join destination on destination.dest_id = hop_to_destination.dest_id 
                    inner join next_hop on next_hop.hop_id = hop_to_destination.hop_id
                    group by hop_to_destination.id 
                    order by destination.destination""")
    table = cursor.fetchall()
    print_db(table)


if __name__ == '__main__':
    database_name = ""
    json_file_name = ""
    for param in sys.argv:
        if param.find('.db') != -1:
            database_name = param
        if param.find('.json') != -1:
            json_file_name = param
    if database_name == "" or json_file_name == "":
        print("Wrong arguments. There are should be *.db and *.json files")
    try:
        connection = sqlite3.connect(database_name)
    except Error:
        print(Error)
    else:
        try:
            json_file = open(json_file_name)
        except FileNotFoundError:
            print("File with name %s was not found" % json_file_name)
        except PermissionError:
            print("No access for reading file %s" % json_file_name)
        else:
            try:
                data = json.load(json_file)
            except TypeError:
                print(TypeError)
                sys.exit()
            except ValueError:
                print(ValueError)
                sys.exit()
            cursor = connection.cursor()
            create_tables(cursor)
            db_writing(data, cursor)
            connection.commit()
            db_reading(cursor)
            connection.close()
