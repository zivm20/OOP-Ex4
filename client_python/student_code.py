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

pokemons = client.get_pokemons()
pokemons_obj = json.loads(pokemons, object_hook=lambda d: SimpleNamespace(**d))

print(pokemons)

graph_json = client.get_graph()

FONT = pygame.font.SysFont('Arial', 20, bold=True)
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

client.add_agent("{\"id\":0}")
# client.add_agent("{\"id\":1}")
# client.add_agent("{\"id\":2}")
# client.add_agent("{\"id\":3}")

# this commnad starts the server - the game is running now
client.start()
endTime = int(client.time_to_end())

agents = json.loads(client.get_agents())["Agents"]
agents = [agent["Agent"] for agent in agents]
agents_obj = [Agent(a["id"],a["speed"]/1000,a["src"],a["dest"]) for a in agents]


pokemon_graph = GraphAlgo()
pokemon_graph.load_from_json(graph_json)

pokemon_dict = []
current_size = pokemon_graph.get_graph().v_size()


def load_pokemon_graph(pokemon_dict,pokemons,current_size,pokemon_graph:GraphAlgo):
    out = []
    for p in pokemons:
        isIn = False
        x, y, _ = p["pos"].split(',')
        p["_pos"] = (x,y)
        p["pos"] = (my_scale(float(x), x=True), my_scale(float(y), y=True)) 
        
        for p_dict in pokemon_dict:
            if p["pos"][0] == p_dict["pos"][0] and p["pos"][1] == p_dict["pos"][1] and p["type"] == p_dict["type"] and p["value"]==p_dict["value"]:
                isIn = True
        if isIn != True:
            out.append(p)
            out[-1]["id"] = current_size
            current_size+=1
            min_distance = float('inf')
            real_src = 0
            real_dest = 0
            real_weight = 0
            for src in pokemon_graph.get_graph().get_all_v().values():
                if src.isPokemon() == False:
                    for _, weight in pokemon_graph.get_graph().all_out_edges_of_node(src.getId()).items():
                        if dest.isPokemon() == False:
                            dest = pokemon_graph.get_graph().get_all_v()[_]
                            distance = abs(  (dest.getPos()[0] - src.getPos()[0])*(src.getPos()[1] - out[-1]["_pos"][1]) - (src.getPos()[0] - out[-1]["_pos"][0])*(dest.getPos()[1] - src.getPos()[1]))
                            distance = distance/(  ( (dest.getPos()[0] - src.getPos()[0])**2 + (dest.getPos()[1] - src.getPos()[1])**2 ) **0.5   )
                            #line from src point to p
                            src_p = ( (src.getPos()[0] - out[-1]["_pos"][0])**2 + (src.getPos()[1] - out[-1]["_pos"][1])**2 ) **0.5
                            #line from dest to src
                            dest_src = ( (dest.getPos()[0] - src.getPos()[0])**2 + (dest.getPos()[1] - src.getPos()[1])**2 ) **0.5
                            #angle dest-src-p
                            angle = np.arcsin(distance/src_p)
                            #get the weight from src to p by scaling the length of the line
                            p_weight = (src_p*np.cos(angle)/dest_src)*weight
                            
                            if(distance < min_distance):
                                min_distance = distance
                                real_weight = p_weight
                                if(out[-1]["type"]<0):
                                    real_src = max(dest.getId(), src.getId())
                                    real_dest = min(dest.getId(), src.getId())
                                else:
                                    real_src = min(dest.getId(), src.getId())
                                    real_dest = max(dest.getId(), src.getId())
            out[-1]["src"] = real_src
            out[-1]["dest"] = real_dest
            out[-1]["weight"] = real_weight
            pokemon_graph.get_graph().add_node(out[-1]["id"],(out[-1]["_pos"][0],out[-1]["_pos"][1],0))
            pokemon_graph.get_graph().get_all_v()[out[-1]["id"]].setPokemon(True)
            pokemon_graph.get_graph().add_edge(out[-1]["src"],out[-1]["id"],out[-1]["weight"])
            w = pokemon_graph.get_graph().all_out_edges_of_node(out[-1]["src"])[out[-1]["dest"]]
            pokemon_graph.get_graph().add_edge(out[-1]["id"],out[-1]["dest"],w - out[-1]["weight"])
    
    return out



def assign_pokemon(pokemon, agents:List[Agent],pokemon_graph:GraphAlgo):
    #update routes
    for agent in agents:
        agent.updateRoute(pokemon_graph,pokemon["src"],pokemon["id"],pokemon["dest"])

    #redistribute pokemon to agents
    minChange = float('inf')
    best_pokemon_distrib = {}
    for agent in agents:
        distrib = {}
        change = agent.simulate_change(pokemon_graph,p_to_add=pokemon["id"],best_p_found=distrib)
        if(change!=0):
            for agent2 in agents:
                if agent != agent2:
                    change+=agent2.simulate_change(best_p_found=distrib)
            if change < minChange:
                minChange = change
                best_pokemon_distrib = distrib
    pokemon_assign = { agent.getId():[] for agent in agents}
    #get the best destribution
    for key, value in best_pokemon_distrib:
        if pokemon_graph.get_graph().get_all_v()[key].isPokemon():
            pokemon_assign[value["id"]].append(key)

    #build from that distribution
    for agent in agents:
        agent.build_route_from_pokemons(pokemon_graph,pokemon_assign[agent.getId()])



"""
The code below should be improved significantly:
The GUI and the "algo" are mixed - refactoring using MVC design pattern is required.
"""
j=0
while client.is_running() == 'true':

    pokemons = json.loads(client.get_pokemons())["Pokemons"]
    pokemons = [p["Pokemon"] for p in pokemons]
    
    new_pokemons = load_pokemon_graph(pokemon_dict,pokemons,current_size,pokemon_graph)
    for pokemon in new_pokemons:
        assign_pokemon(pokemon,agents_obj,pokemon_graph)
    pokemon_dict = pokemon_dict+new_pokemons
    
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
    # check events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit(0)

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
    for p in pokemons:
        pygame.draw.circle(screen, Color(0, 255, 255), (int(p.pos.x), int(p.pos.y)), 10)

    # update screen changes
    display.update()

    # refresh rate
    clock.tick(100)
    """
    # choose next edge
    for agent in agents:
        if agent.dest == -1:
            next_node = (agent.src - 1) % len(graph.Nodes)
            client.choose_next_edge(
                '{"agent_id":'+str(agent.id)+', "next_node_id":'+str(next_node)+'}')
            ttl = client.time_to_end()
            print(ttl, client.get_info())
            #print(pokemons)

    if j%1==0:
        client.move()
    j+=1
    """

    for agent in agents_obj:
        if(agent.update(pokemon_graph,client, endTime-int(client.time_to_end()))):
            client.move()
# game over:
