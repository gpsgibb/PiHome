import yaml
import sys

#Gets the config from the config file 'file', If 'key' is provided, we return the config data belonging to key
def GetConfig(key=None,file="config.yaml"):
    try:
        f = open(file,"r")
    except FileNotFoundError:
            msg = ("ERROR: Config file '%s' not found. \nThis should be placed in the directory of the top level script being called.")
            raise Exception(msg)

    try:
        config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise Exception("ERROR: Unable to parse '%s'"%file)

    f.close()
    
    if key == None:
        return config
    else:
        try:
            return config[key]
        except KeyError as e:
            print("Error. Key '%s' not found in the config file '%s'"%(key,file))
            raise e





    