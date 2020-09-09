import json
import sqlite3
import sys
from sqlite3 import Error


def print_db(data):
    string = "|{0:^20}|{1:^10}|{2:^10}|{3:^20}|{4:^15}|{5:^15}|"
    print("_" * 97)
    print(string.format("Destination", "Preference", "Metric", "Next Hop", "Interface", "Age"))
    print("-" * 97)
    prev = ""
    for line in data:
        print(string.format(line[1] if line[1] != prev else "", line[2], line[3], line[0], line[5], line[4]))
        prev = line[1]


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
        json_file = open(json_file_name)
        data = json.load(json_file)
        cursor = connection.cursor()
        cursor.execute("DROP TABLE IF EXISTS next_hop")
        cursor.execute("DROP TABLE IF EXISTS destination")
        cursor.execute("DROP TABLE IF EXISTS hop_to_destination")
        cursor.execute("""CREATE TABLE IF NOT EXISTS next_hop
                          (hop_id INTEGER PRIMARY KEY, 
                          hop text)
                       """)
        cursor.execute("""CREATE TABLE IF NOT EXISTS destination
                                          (dest_id INTEGER PRIMARY KEY, 
                                          destination text,
                                          preference integer,
                                          metric integer,
                                          age text,
                                          interface text)
                                       """)
        cursor.execute("""CREATE TABLE IF NOT EXISTS hop_to_destination
                                  (id INTEGER PRIMARY KEY, 
                                  hop_id integer REFERENCES next_hop(hop_id),
                                  dest_id integer REFERENCES destination(dest_id))
                               """)
        for hop, dest in data['route_table']['next_hop'].items():
            cursor.execute("INSERT INTO next_hop (hop) VALUES ('{0}')".format(hop))
            hop_id = cursor.lastrowid
            for key, value in dest.items():
                pref = int(value.get('preference'))
                metric = int(value.get('metric'))
                age = value.get('age')
                interface = value.get('via')
                cursor.execute(
                    f"""INSERT INTO destination (destination, preference, metric, age, interface) 
                    VALUES ('{key}','{pref}','{metric}','{age}','{interface}')""")
                dest_id = cursor.lastrowid
                cursor.execute(f"INSERT INTO hop_to_destination (hop_id, dest_id) VALUES ('{hop_id}', '{dest_id}')")
        connection.commit()
        cursor.execute("""select next_hop.hop, 
            destination.destination, destination.preference, destination.metric, destination.age, destination.interface
            from hop_to_destination 
            inner join destination on destination.dest_id = hop_to_destination.dest_id 
            inner join next_hop on next_hop.hop_id = hop_to_destination.hop_id
            group by hop_to_destination.id 
            order by destination.destination""")
        table = cursor.fetchall()
        print_db(table)
        connection.close()
