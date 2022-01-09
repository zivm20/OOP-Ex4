"""
@author AchiyaZigi
OOP - Ex4
Very simple GUI example for python client to communicates with the server and "play the game!"
"""
from types import SimpleNamespace
from client import Client
from typing import List
from GraphAlgo import GraphAlgo
from DiGraph import DiGraph
import numpy as np
import json
from Agent import Agent
from pygame import gfxdraw
import pygame
from pygame import *
import glob
# init pygame
WIDTH, HEIGHT = 1080, 720

# default port
PORT = 6666
# server host (default localhost 127.0.0.1)
HOST = '127.0.0.1'
pygame.init()

screen = display.set_mode((WIDTH, HEIGHT), depth=32, flags=RESIZABLE)
clock = pygame.time.Clock()
pygame.font.init()

client = Client()
client.start_connection(HOST, PORT)
#client.log_in("209904606")
pokemons = client.get_pokemons()
pokemons_obj = json.loads(pokemons, object_hook=lambda d: SimpleNamespace(**d))
graph_json = client.get_graph()

#pre load resources
FONT = pygame.font.SysFont('Arial', 20, bold=True)
FONT2 = pygame.font.SysFont('Arial', 12, bold=True)
TIMER_FONT = pygame.font.SysFont('Arial', 24, bold=True)
SCORE_FONT = pygame.font.SysFont('Arial', 30, bold=True)
images_normal = [pygame.image.load(img_path).convert_alpha() for img_path in glob.glob("sprites/normal/*.png")]
images_shiny = [pygame.image.load(img_path).convert_alpha() for img_path in glob.glob("sprites/shiny/*.png")]



# load the json string into SimpleNamespace Object

graph = json.loads(
    graph_json, object_hook=lambda json_dict: SimpleNamespace(**json_dict))

for n in graph.Nodes:
    x, y, _ = n.pos.split(',')
    n.pos = SimpleNamespace(x=float(x), y=float(y))

 # get data proportions
min_x = min(list(graph.Nodes), key=lambda n: n.pos.x).pos.x
min_y = min(list(graph.Nodes), key=lambda n: n.pos.y).pos.y
max_x = max(list(graph.Nodes), key=lambda n: n.pos.x).pos.x
max_y = max(list(graph.Nodes), key=lambda n: n.pos.y).pos.y


def scale(data, min_screen, max_screen, min_data, max_data):
    """
    get the scaled data with proportions min_data, max_data
    relative to min and max screen dimentions
    """
    return ((data - min_data) / (max_data-min_data)) * (max_screen - min_screen) + min_screen


# decorate scale with the correct values

def my_scale(data, x=False, y=False):
    if x:
        return scale(data, 50, screen.get_width() - 50, min_x, max_x)
    if y:
        return scale(data, 50, screen.get_height()-50, min_y, max_y)


radius = 15


#choose starting point of nodes based on graph center point
pokemon_graph = GraphAlgo()
pokemon_graph.load_from_json(json_string=graph_json)
distanceMat = pokemon_graph.all_pairs_shortest_path()
distances = { i: max(nodes.values())  for i,nodes in  distanceMat.items()}

while len(distances)>0:
    best_id = min(distances.items(), key=lambda x: x[1])[0]
    if len(distances)==1:
        while len(distances)==1:
            if client.add_agent("{\"id\":"+str(best_id)+"}") == "false":
                break
            else:
                print("added agent on",best_id)
                
    else:
        if client.add_agent("{\"id\":"+str(best_id)+"}") == "false":
            break
        else:
            print("added agent on",best_id)
    del distances[best_id]





# this commnad starts the server - the game is running now
client.start()
agents = json.loads(client.get_agents())["Agents"]
agents = [agent["Agent"] for agent in agents]





agents_obj = [ Agent(int(a["id"]),float(a["speed"]),pokemon_graph.get_graph().get_all_v()[int(a["src"] )], int(a["dest"]) ) for a in agents   ]

pokemon_dict = []
current_size = pokemon_graph.get_graph().v_size()


def load_pokemon_graph(pokemon_dict,pokemons,current_size,pokemon_graph:GraphAlgo):
    out = []
    for p in pokemons:
        isIn = False
        x, y, _ = p["pos"].split(',')
        
        p["pos"] = (float(x),float(y))
        p["_pos"] = (my_scale(float(x), x=True), my_scale(float(y), y=True))
        
        for p_dict in pokemon_dict:
            if p["_pos"][0] == p_dict["_pos"][0] and p["_pos"][1] == p_dict["_pos"][1] and p["type"] == p_dict["type"] and p["value"]==p_dict["value"]:
                isIn = True
                out.append(p_dict)
        if isIn != True:
            out.append(p)
            out[-1]["id"] = current_size
            current_size+=1
            min_distance = float('inf')
            real_src = 0
            real_dest = 0
            
            for src in pokemon_graph.get_graph().get_all_v().values():
                
                for _, weight in pokemon_graph.get_graph().all_out_edges_of_node(src.getId()).items():
                    dest = pokemon_graph.get_graph().get_all_v()[_]

                    distance = abs(  (dest.getPos()[0] - src.getPos()[0])*(src.getPos()[1] - out[-1]["pos"][1]) - (src.getPos()[0] - out[-1]["pos"][0])*(dest.getPos()[1] - src.getPos()[1]))
                    distance = distance/(  ( (dest.getPos()[0] - src.getPos()[0])**2 + (dest.getPos()[1] - src.getPos()[1])**2 ) **0.5   )
                    
                    if(distance < min_distance):
                        min_distance = distance
                        
                        if(out[-1]["type"]<0):
                            real_src = max(dest.getId(), src.getId())
                            real_dest = min(dest.getId(), src.getId())
                        else:
                            real_src = min(dest.getId(), src.getId())
                            real_dest = max(dest.getId(), src.getId())
            out[-1]["src"] = int(real_src)
            out[-1]["dest"] = int(real_dest)
            
            
    
    return out, current_size



def assign_pokemon(pokemons_dict:List[dict], agents:List[Agent],pokemon_graph:GraphAlgo):
    stack = [i for i in agents]
    assignments = {}
    pokemons = {agent.getId() : [p for p in pokemons_dict] for agent in agents}
    while len(stack)>0:
        agent = stack.pop(0)
        score = agent.set_pokemon_target(pokemon_graph,pokemons[agent.getId()])
        if agent.get_target()["id"] in assignments and len(pokemons[agent.getId()])>0:
            if(assignments[agent.get_target()["id"]]["score"] < score ):
                pokemons[agent.getId()].remove(agent.get_target())
                agent.remove_target()
                stack.append(agent)
            elif assignments[agent.get_target()["id"]]["score"] > score:
                a2 = assignments[agent.get_target()["id"]]["Agent"]
                pokemons[a2.getId()].remove(agent.get_target())
                a2.remove_target()
                stack.append(a2)
                assignments[agent.get_target()["id"]]["Agent"] = agent
                assignments[agent.get_target()["id"]]["score"] = score
        elif len(pokemons[agent.getId()])>0:
            assignments[agent.get_target()["id"]] = {}
            assignments[agent.get_target()["id"]]["Agent"] = agent
            assignments[agent.get_target()["id"]]["score"] = score

    
    

        
        

"""
The code below should be improved significantly:
The GUI and the "algo" are mixed - refactoring using MVC design pattern is required.
"""
ttl2=0
j=0

#first init
pokemons = json.loads(client.get_pokemons())["Pokemons"]
pokemons = [p["Pokemon"] for p in pokemons]
pokemon_dict,current_size = load_pokemon_graph(pokemon_dict,pokemons,current_size,pokemon_graph)        
assign_pokemon(pokemon_dict,agents_obj,pokemon_graph)



client_info = ""
startTime = int(round(time.get_ticks() * 1000))
endTime = int(client.time_to_end())
run = True
while startTime - int(round(time.get_ticks() * 1000)) <= endTime and run:
    try:
        client.is_running() == 'true'
    except:
        break
    


    pokemons = json.loads(client.get_pokemons(),
                        object_hook=lambda d: SimpleNamespace(**d)).Pokemons
    pokemons = [p.Pokemon for p in pokemons]
    for p in pokemons:
        x, y, _ = p.pos.split(',')
        p.pos = SimpleNamespace(x=my_scale(
            float(x), x=True), y=my_scale(float(y), y=True))
    agents = json.loads(client.get_agents(),
                        object_hook=lambda d: SimpleNamespace(**d)).Agents
    agents = [agent.Agent for agent in agents]
    for a in agents:
        x, y, _ = a.pos.split(',')
        a.pos = SimpleNamespace(x=my_scale(
            float(x), x=True), y=my_scale(float(y), y=True))

    # refresh surface
    screen.fill(Color(0, 0, 0))

    # draw nodes
    for n in graph.Nodes:
        x = my_scale(n.pos.x, x=True)
        y = my_scale(n.pos.y, y=True)

        # its just to get a nice antialiased circle
        gfxdraw.filled_circle(screen, int(x), int(y),
                              radius, Color(64, 80, 174))
        gfxdraw.aacircle(screen, int(x), int(y),
                         radius, Color(255, 255, 255))

        # draw the node id
        id_srf = FONT.render(str(n.id), True, Color(255, 255, 255))
        rect = id_srf.get_rect(center=(x, y))
        screen.blit(id_srf, rect)

    # draw edges
    for e in graph.Edges:
        # find the edge nodes
        src = next(n for n in graph.Nodes if n.id == e.src)
        dest = next(n for n in graph.Nodes if n.id == e.dest)

        # scaled positions
        src_x = my_scale(src.pos.x, x=True)
        src_y = my_scale(src.pos.y, y=True)
        dest_x = my_scale(dest.pos.x, x=True)
        dest_y = my_scale(dest.pos.y, y=True)

        # draw the line
        pygame.draw.line(screen, Color(61, 72, 126),
                         (src_x, src_y), (dest_x, dest_y))

    # draw agents
    for agent in agents:
        pygame.draw.circle(screen, Color(122, 61, 23),
                           (int(agent.pos.x), int(agent.pos.y)), 10)
    # draw pokemons (note: should differ (GUI wise) between the up and the down pokemons (currently they are marked in the same way).
    for i in range(len(pokemons)):
        
        id = None
        src = 0
        dest = 0
        for p_dict in pokemon_dict:
            if pokemons[i].pos.x == p_dict["_pos"][0] and pokemons[i].pos.y == p_dict["_pos"][1] and pokemons[i].type == p_dict["type"] and pokemons[i].value==p_dict["value"]:
                #render pokemon value
                id_srf = FONT2.render(str(pokemons[i].value), True, Color(255,255,255))
                id = p_dict["id"]
                src = p_dict["src"]
                dest = p_dict["dest"]
        #if type is negative, the pookemon won't be shiny
        if pokemons[i].type < 0:
            idx = ( (src+id)**2 + src*dest*id+5- id*src + dest*int(pokemons[i].value)) % len(images_normal)
            rect = images_normal[idx].get_rect(center=(int(pokemons[i].pos.x), int(pokemons[i].pos.y)))
            screen.blit(images_normal[idx], rect)
        else:
            idx = ( id**2 + src*dest-id+5- id*src +dest*int(pokemons[i].value)) % len(images_shiny)
            rect = images_shiny[idx ].get_rect(center=(int(pokemons[i].pos.x), int(pokemons[i].pos.y)))
            screen.blit(images_shiny[idx], rect)

        rect = id_srf.get_rect(center=(int(pokemons[i].pos.x), int(pokemons[i].pos.y+40)))
        screen.blit(id_srf, rect)
        
    #timer
    time_left = int(client.time_to_end())/1000

    timer = TIMER_FONT.render(str(int(time_left/60))+":"+str(int(time_left%60)), True, Color(255,255,255))
    rect = timer.get_rect(center=(screen.get_size()[0]*0.5, screen.get_size()[1]*0.05 ))
    screen.blit(timer, rect)

    #scoring
    c_info = json.loads(client.get_info())["GameServer"]
    moves_done = SCORE_FONT.render("Moves: "+str(c_info["moves"]), True, Color(255,255,255))
    rect = moves_done.get_rect(topleft=(0,0))
    screen.blit(moves_done, rect)

    current_score = SCORE_FONT.render("Grade: "+str(c_info["grade"]), True, Color(255,255,255))
    rect = current_score.get_rect(topleft=(0,SCORE_FONT.get_height()+10))
    screen.blit(current_score, rect)




    # update screen changes
    display.update()
    # refresh rate
    clock.tick(100)
  
    
    found_pokemon = []
    move = False

    route_update_req = {}
    client_info = client.get_info()
    for i in range(len(agents_obj)):
        agents_obj[i]
        flg, temp = agents_obj[i].update(pokemon_graph,client,pokemon_dict)
        found_pokemon = found_pokemon + temp
        if flg or len(temp)>0:
            move = flg or len(temp)>0
        
    if move:
        
        if(client.is_running() == "true"):
            agent_states = client.move()
            for agent in agents_obj:
                agent.server_update(agent_states,client.time_to_end(),pokemon_graph)

            if len(found_pokemon)>0:
                pokemons = json.loads(client.get_pokemons())["Pokemons"]
                pokemons = [p["Pokemon"] for p in pokemons]
                pokemon_dict,current_size = load_pokemon_graph(pokemon_dict,pokemons,current_size,pokemon_graph)        
                assign_pokemon(pokemon_dict,agents_obj,pokemon_graph)
            if(client.is_running() == "true"):
                for agent in agents_obj:
                    id,dest = agent.update_route()
                    if(dest != -1):
                        client.choose_next_edge('{"agent_id":'+str(id)+', "next_node_id":'+str(dest)+'}')
    
    # check events
    for event in pygame.event.get():
        if event.type == pygame.KEYUP:
            if pygame.key.name(event.key)=="p":
                client.stop_connection()
        elif event.type == pygame.QUIT:
            pygame.quit()
            exit(0)
                
print(client_info)
        
        
        
       
    


    
    
    
        
            

        




# game over:

