import sys
import requests
import pandas as pd
import re
cached_responses = {}
baseURL = "http://pokeapi.co/api/v2/"

def getAPIResponse(endNode):
    if(endNode not in cached_responses.keys()):
        response = requests.get(baseURL + endNode)
        if response.status_code != 200:
            print('Response Error Code:',response.status_code)
            return None
        else:
            cached_responses[endNode] = response.json()
    return cached_responses[endNode]
    
def extractID(url):
    return re.findall(r'-?/\d+/', url)[0].split("/")[1]

def getRootData(rootNode):
    root_df = pd.DataFrame(getAPIResponse(rootNode)['results'])
    root_df["id"] = root_df["url"].apply(lambda url: extractID(url))
    root_df = root_df.drop(["url"], axis=1)
    return root_df

def searchKeyInJSON(responseDict, searchKey):
    for key,value in responseDict.items():
        if(key == searchKey):
            yield value
        elif(isinstance(value, dict)):
            for val in searchKeyInJSON(value, searchKey):
                yield val
        elif(isinstance(value, list)):
            for listval in value:
                for val in searchKeyInJSON(listval, searchKey):
                    yield val
    
def getTypeIDs(jsonResponse):
    entity_types = []
    types_list = searchKeyInJSON(jsonResponse, "type")
    for types in types_list:
        entity_types.append(extractID(types["url"]))
    return entity_types

def getBaseStats(jsonResponse):
    base_stats = []
    stats = searchKeyInJSON(jsonResponse, "base_stat")
    for stat in stats:
        base_stats.append(stat)
    return sum(base_stats)

def getDamageSummary(jsonResponse):
    damage_dict = {}
    damages = jsonResponse['damage_relations']
    for damage, types in damages.items():
        types_list = []
        for typ in types:
            types_list.append(extractID(typ["url"]))
        damage_dict[damage] = types_list
    return damage_dict

def getAdvantageValue(damage):
    value = 0
    if 'half' in damage:
        value = 0.5
    if 'double' in damage:
        value = 2.0;
    if 'from' in damage:
        value = value*(-1)
    return value

def comparePokemons(id1, id2):
    winner = ''
    advantages = []
    pokemon1_types = getTypeIDs(getAPIResponse("pokemon/" + id1))
    pokemon2_types = getTypeIDs(getAPIResponse("pokemon/" + id2))
    pokemon1_types = list(set(pokemon1_types) - (set(pokemon1_types) & set(pokemon2_types)))
    pokemon2_types = list(set(pokemon2_types) - (set(pokemon1_types) & set(pokemon2_types)))
    for t1 in pokemon1_types:
        damages = getDamageSummary(getAPIResponse("type/" + t1))
        for damage, types in damages.items():
            if bool(set(types).intersection(set(pokemon2_types))):
                advantages.append(damage)
    
    net_advantage = 0
    for e in advantages:
        net_advantage += getAdvantageValue(e)
    
    if(net_advantage > 0):
        winner = id1
    elif(net_advantage < 0):
        winner = id2
    else:
        if(getBaseStats(getAPIResponse("pokemon/" + id1)) >= getBaseStats(getAPIResponse("pokemon/" + id2))):
            winner = id1
        else:
            winner = id2
        
    return winner 

def parseArgs(argv, pokemons_df):
   id1= ''
   id2 = ''
   if(argv[0] != '-id' and argv[0] != '-name'):
       print("Enter Arguments as: -id id1, id2 / -name name1, name2")
       exit()   
   if(argv[0] == '-id'):
       if(argv[1] in list(pokemons_df["id"])):
           id1 = argv[1]
       if(argv[2] in list(pokemons_df["id"])):
           id2 = argv[2]
   elif(argv[0] == '-name'):
       if(argv[1] in list(pokemons_df["name"])):
           id1 = pokemons_df[pokemons_df["name"] == argv[1]]["id"].item()
       if(argv[2] in list(pokemons_df["name"])):
           id2 = pokemons_df[pokemons_df["name"] == argv[2]]["id"].item()
   if(len(id1) == 0 or len(id2) == 0):
       print("Invalid Entry ")
       exit()
   return id1, id2

if __name__ == "__main__":
   pokemons_df = getRootData("pokemon")
   pokemon_id1, pokemon_id2 = parseArgs(sys.argv[1:],pokemons_df)
   pokemon_better = comparePokemons(pokemon_id1, pokemon_id2)
   print('id:'+pokemon_better, 'name:' + pokemons_df[pokemons_df["id"] ==pokemon_better]["name"].item())