from GraphAlgo import GraphAlgo
from DiGraph import DiGraph
import json
from Node import Node
from client import Client
from typing import List

EPS = 0.001
class Agent:

    def __init__(self,id:int,speed:float,src:Node,dest:int):
        self.id = id
        self.speed = speed/1000
        self.position = src.getPos()
        self.dest = dest
        self.src = src
        self.weight = 0
        self.interval = 20
        self.target = None
        self.route = []
        self.time = 0

               
    def found_pokemon(self,graph_algo,pokemons):
        #return colided pokemon
        found_pokemon = []
        for pokemon in pokemons:
            if pokemon["src"] == self.src.getId() and self.dest == pokemon["dest"]:
                if self.collide(graph_algo,pokemon["pos"]):
                    found_pokemon.append(pokemon)
                    if pokemon == self.target:
                        self.remove_target()
                    
        return found_pokemon
    
    #check if we need to alert the server to move
    def update(self,graph_algo:GraphAlgo,client:Client,pokemons:List[dict]):
        time = int(client.time_to_end())
        ellapsed_time = self.time-time
        move = False
        self.time = time
        


        #route has nodes yet dest is -1
        if len(self.route)>0 and (self.dest == -1):
            move = True
        
        #dest isn't -1 yet the agent's position is on the dest node
        if self.dest != -1:
            self.position = self.calcPos(ellapsed_time*self.speed,graph_algo)
            self.weight += ellapsed_time*self.speed
            if(self.weight >= self.src.getChildren()[self.dest]):
                move = True
                self.dest = -1

        
        found_pokemon = self.found_pokemon(graph_algo,pokemons)

        return move, found_pokemon
    def debug(self):
        if self.target != None:
            if self.dest != -1:
                print(self.src.getId(),self.dest,self.position,"{:.4f}".format(self.weight),"{:.2f}%".format(100*(self.weight/self.src.getChildren()[self.dest])),self.target["id"],self.route)
            else:
                print(self.src.getId(),self.dest,self.position,"{:.4f}".format(self.weight),str(0)+"%",self.target["id"],self.route)
        else:
            if self.dest != -1:
                print(self.src.getId(),self.dest,self.position,"{:.4f}".format(self.weight),"{:.2f}%".format(100*(self.weight/self.src.getChildren()[self.dest])),self.target,self.route)
            else:
                print(self.src.getId(),self.dest,self.position,"{:.4f}".format(self.weight),str(0)+"%",self.target,self.route)

    #called right after move, will update all the variables to match the server
    def server_update(self,json_str:str,time:str,graph_algo:GraphAlgo):
        agent = [a["Agent"] for a in json.loads(json_str)["Agents"] if a["Agent"]["id"]==self.id ][0]
        temp = agent["pos"].split(",")[:-1]
        x,y = (float(temp[0]),float(temp[1]))
        params = {"src":graph_algo.get_graph().get_all_v()[int(agent["src"])],"dest":int(agent["dest"]),"pos":(x,y),"time":int(time),"speed":float(agent["speed"]/1000)}
        self.src = params["src"]
        self.dest = params["dest"]
        if self.dest == -1:
            self.weight = 0
        self.speed = params["speed"]
        self.position = params["pos"]
        self.time = params["time"]

    def update_route(self):
        if len(self.route)>0 and (self.dest == -1):
            self.dest = self.route.pop(0)
            self.weight=0
            return self.id, self.dest
        return self.id, -1
        
        


    def distance(self,p1:list,p2:list):
        
        return (( (p1[0] - p2[0])**2 + (p1[1] - p2[1])**2 ) **0.5)

    def collide(self,graph_algo:GraphAlgo,obj:list):
        p1 = self.position

        #check if 
        #last distance to obj >=curr distance to obj < next distance to obj
        d1 = self.distance(obj,self.calcPos(-self.speed*self.interval,graph_algo))
        d2 = self.distance(obj,p1)
        d3 = self.distance(obj,self.calcPos(self.speed*self.interval,graph_algo))
        
        flg = d1>=d2 and d2 < d3

        return flg
        
    def calcPos(self,distance:float,graph_algo:GraphAlgo):
        #scale distance with edge weight
        p1 = self.src.getPos()
        p2 = graph_algo.get_graph().get_all_v()[self.dest].getPos()
        X = (p2[0]-p1[0])/self.src.getChildren()[self.dest]
        Y = (p2[1]-p1[1])/self.src.getChildren()[self.dest]
        distance = distance + self.weight

        return (p1[0] + X*distance,  p1[1] + Y*distance)


    def set_pokemon_target(self,graph_algo:GraphAlgo,pokemons):
        edge_bonuses = {}
        for pokemon in pokemons:
            if pokemon["src"] not in edge_bonuses:
                edge_bonuses[pokemon["src"]] = {}
            if pokemon["dest"] not in edge_bonuses[pokemon["src"]]:
                edge_bonuses[pokemon["src"]][pokemon["dest"]]=0
            edge_bonuses[pokemon["src"]][pokemon["dest"]] += pokemon["value"]
        
        for src in edge_bonuses:
            for dest in edge_bonuses[src]:
                print(src,dest,edge_bonuses[src][dest])

        print("")
        print("")

        #set target as the closest pokemon
        min_dist = float('inf')
        for pokemon in pokemons:     
            

            curr_distance,path = self.path_to_pokemon(graph_algo,pokemon)
            total_val = 0
            for i in range(len(path)-1):
                if path[i] in edge_bonuses and path[i+1] in edge_bonuses[path[i]]:
                    total_val+=edge_bonuses[path[i]][path[i+1]]
            if total_val == 0:
                total_val = 1
            
            #decision function
            curr_distance = curr_distance

            if curr_distance<min_dist:
                min_dist = curr_distance
                self.route = path 
                #first element in route is dest
                self.route = self.route[1:]
                self.target = pokemon
        return min_dist


    def path_to_pokemon(self,graph_algo:GraphAlgo,pokemon:dict):
        curr_distance=0
        #pokemon src -> pokemon pos
        scale = graph_algo.get_graph().all_out_edges_of_node(pokemon["src"])[pokemon["dest"]] * self.distance(graph_algo.get_graph().get_all_v()[pokemon["src"]].getPos(),graph_algo.get_graph().get_all_v()[pokemon["dest"]].getPos())
        pokmeon_src_pos_weight = scale*self.distance(graph_algo.get_graph().get_all_v()[pokemon["src"]].getPos(),pokemon["pos"])

        path = []
        #check if we have passed the pokemon or not
        flg = pokemon["dest"]==self.dest and pokmeon_src_pos_weight>self.weight
        #special case where the pokemon is on the same edge as we are on and we have yet to pass it 
        if pokemon["src"] == self.src.getId() and (self.dest == -1 or flg):
            #scale = self.distance(self.pos,pokemon["pos"])/self.distance(graph_algo.get_graph().get_all_v()[pokemon["src"]].getPos(),graph_algo.get_graph().get_all_v()[pokemon["dest"]].getPos())
            #curr_distance = scale*graph_algo.get_graph().all_out_edges_of_node(pokemon["src"])[pokemon["dest"]]
            if self.dest == -1:
                curr_distance = graph_algo.get_graph().all_out_edges_of_node(pokemon["src"])[pokemon["dest"]]
                path = [pokemon["dest"]]
        else:
            if self.dest == -1 and self.src.getId() != pokemon["src"]:
                #agent src -> pokemon src
                curr_distance,path = graph_algo.shortest_path(self.src.getId(),pokemon["src"])
            else:
                #agent dest -> pokemon src
                curr_distance,path = graph_algo.shortest_path(self.dest,pokemon["src"])

            #agent dest -> pokemon src -> pokemon dest
            curr_distance += graph_algo.get_graph().all_out_edges_of_node(pokemon["src"])[pokemon["dest"]]
            path = path + [pokemon["dest"]]
        
        return curr_distance,path







    def remove_target(self):
        self.target = None
        self.route = []
    
    def get_target(self):
        return self.target
            
    def getId(self):
        return self.id
    def getSrc(self):
        return self.src
    def getDest(self):
        return self.dest





    

    

























