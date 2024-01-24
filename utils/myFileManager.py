import json
from time import gmtime

class FileManager:
    
    def to_dict(self):
        return self.__dict__

    @classmethod
    def from_dict(cls, data):
        return cls(**data)
    
    @classmethod
    def from_json(cls):
        try:
            with open("data/"+str(cls).split("'")[1]+".json", "r") as file:
                data = json.load(file)
                return [cls.from_dict(item) for item in data]
        except:
            return []

    @classmethod
    def to_json(cls, lst):
        data = [item.to_dict() for item in lst]
        file_name = "data/" + str(cls).split("'")[1] + ".json"
        try:
            with open(file_name, 'w') as file:
                json.dump(data, file)
        except OSError:
            # If the file doesn't exist, create it and then write the data
            with open(file_name, 'x') as file:
                json.dump(data, file)

    def __str__(self):
        return ', '.join([f"{key}: {value}" for key, value in self.__dict__.items()])

def log(typ, string):
    log_entry = "[{:02}:{:02}:{:02}] [{}] {}".format(gmtime()[3], gmtime()[4], gmtime()[5], typ, string)
    print(log_entry)
    if typ == "DEBUG": return
    with open('events.log', 'a') as file:
        print(log_entry, file=file)