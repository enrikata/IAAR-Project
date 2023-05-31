import yaml
from ServerClass import ServerClass

with open('conf/configuration.yml') as conf_file:
    params = yaml.safe_load(conf_file)

server = ServerClass(params)
server.start()
