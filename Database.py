import json
import os

# opens the db json
def open_db():
    print(os.getcwd())
    with open("db.json", "r") as infile:
        db = json.load(infile)
        return db

# writes to db json
def write_db(db):
    with open("db.json", "w") as outfile:
        json.dump(db, outfile)

#inserts into db json some value
def insert_db_value(value, location):
    db = open_db()
    location_values = db[f"{location}"]
    location_values.append(value)
    write_db(db)

#extracts db to some location
def extract_db_values(location):
    db = open_db()
    location_values = db[f"{location}"]
    return location_values