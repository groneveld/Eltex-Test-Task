import json
import re
import sqlite3
import sys
from sqlite3 import Error


def age_convertation_to_str(int_age):
    def format_age(digit, char):
        if char == 'w' and digit == 0:
            return ''
        elif char == ':' or char == '':
            return f"{digit:02d}{char}"
        return f"{digit}{char}"

    digits = []
    for div in [604800, 86400, 3600, 60, 1]:
        digit = int_age // div
        int_age = int_age % div
        digits.append(digit)
    return "".join([format_age(digit, char) for digit, char in zip(digits, ['w', 'd ', ':', ':', ''])])


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
    db_execute(cursor, """CREATE TABLE IF NOT EXISTS next_hop (hop_id INTEGER PRIMARY KEY, hop text)""")
    db_execute(cursor, """CREATE TABLE IF NOT EXISTS destination (dest_id INTEGER PRIMARY KEY, 
                        destination text, preference integer, metric integer, age integer, interface text)""")
    db_execute(cursor, """CREATE TABLE IF NOT EXISTS hop_to_destination (id INTEGER PRIMARY KEY, 
                        hop_id integer REFERENCES next_hop(hop_id), dest_id integer REFERENCES destination(dest_id))""")


def age_convertation_to_int(string_age):
    length = 5
    if string_age.find('w') == -1:
        length -= 1
    if string_age.find('d') == -1:
        length -= 1
    age = re.findall(r'\d+', string_age)
    age = [int(i) for i in age]
    age = list(reversed(age))
    muls = [1, 60, 3600, 24 * 3600, 7 * 3600 * 24]
    int_age = sum(mul * value for mul, value in zip(muls, age))
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
    db_execute(cursor, """select next_hop.hop, destination.destination, destination.preference, destination.metric, 
                    destination.age, destination.interface from hop_to_destination 
                    inner join destination on destination.dest_id = hop_to_destination.dest_id 
                    inner join next_hop on next_hop.hop_id = hop_to_destination.hop_id 
                    group by hop_to_destination.id order by destination.destination""")
    table = cursor.fetchall()
    print_db(table)


def connect_to_database(database_name, json_file):
    try:
        connection = sqlite3.connect(database_name)
        return connection
    except Error:
        print(Error)
        sys.exit()


def reading_json(json_file_name):
    try:
        json_file = open(json_file_name)
        return json_file
    except FileNotFoundError:
        print("File with name %s was not found" % json_file_name)
        sys.exit()
    except PermissionError:
        print("No access for reading file %s" % json_file_name)
        sys.exit()


def upload_json_to_dict(json_file):
    try:
        data = json.load(json_file)
        return data
    except TypeError:
        print(TypeError)
        sys.exit()
    except ValueError:
        print(ValueError)
        sys.exit()


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
    connection = connect_to_database(database_name)
    json_file = reading_json(json_file_name)
    data = upload_json_to_dict(json_file)
    cursor = connection.cursor()
    create_tables(cursor)
    db_writing(data, cursor)
    connection.commit()
    db_reading(cursor)
    connection.close()
