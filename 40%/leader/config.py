from configparser import ConfigParser

def get_configurations(filename = "config.ini"):
    parser = ConfigParser()
    parser.read(filename)
    config_dict = dict()
    for section in parser.sections():
        config = dict()
        params = parser.items(section)
        for param in params:
            config[param[0]] = param[1]
        config_dict[section] = config
    
    return config_dict
