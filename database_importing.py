import json
import sqlite3
import sys
from sqlite3 import Error

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
            for key, value in dest.items():
                pref = int(value.get('preference'))
                metric = int(value.get('metric'))
                age = value.get('age')
                interface = value.get('via')
                cursor.execute(
                    f"""INSERT INTO destination (destination, preference, metric, age, interface) 
                    VALUES ('{key}','{pref}','{metric}','{age}','{interface}')""")
        connection.commit()
        for row in cursor.execute("SELECT * FROM next_hop"):
            print(row)

        connection.close()
    print(1)
