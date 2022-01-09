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
                        print(self.distance(self.position,pokemon["pos"]))
                        print("agent pos:",self.position,pokemon["pos"])
                        self.remove_target()
                    
        return found_pokemon
    
    #check if we need to alert the server to move
    def update(self,graph_algo:GraphAlgo,client:Client,pokemons:List[dict]):
        time = int(client.time_to_end())
        ellapsed_time = self.time-time
        move = False
        self.time = time
        

        #if len(self.route) == 0 and self.target != None and (self.target["src"] != self.src.getId() or self.dest != self.target["dest"]):
            #curr_distance,self.dest


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
        #set target as the closest pokemon
        min_dist = float('inf')
        for pokemon in pokemons:     

            curr_distance,path = self.path_to_pokemon(graph_algo,pokemon)

            #decision function
            curr_distance = curr_distance/self.speed

            if curr_distance<min_dist:
                min_dist = curr_distance
                self.route = path 
                #first element in route is dest
                self.route = self.route[1:]
                self.target = pokemon
        return min_dist


    def path_to_pokemon(self,graph_algo:GraphAlgo,pokemon):
        curr_distance=0
        path = []
        #check if we have passed the pokemon or not
        flg = pokemon["dest"]==self.dest and self.distance(pokemon["pos"],self.position) >= self.distance(pokemon["pos"],self.calcPos(self.interval*self.speed,graph_algo))
        #special case where the pokemon is on the same edge as we are on and we have yet to pass it 
        if pokemon["src"] == self.src.getId() and (self.dest == -1 or flg):
            curr_distance = self.distance(pokemon["pos"],self.position)/self.distance(graph_algo.get_graph().get_all_v()[pokemon["src"]].getPos(),graph_algo.get_graph().get_all_v()[pokemon["dest"]].getPos())
            curr_distance = curr_distance*graph_algo.get_graph().all_out_edges_of_node(pokemon["src"])[pokemon["dest"]]
            if self.dest == -1:
                path = [pokemon["dest"]]
        else:
            if self.dest == -1 and self.src.getId() != pokemon["src"]:
                curr_distance,path = graph_algo.shortest_path(self.src.getId(),pokemon["src"])
            else:
                #agent dest -> pokemon src
                curr_distance,path = graph_algo.shortest_path(self.dest,pokemon["src"])

                scale = self.src.getChildren()[self.dest]/self.distance(self.src.getPos(), graph_algo.get_graph().get_all_v()[self.dest].getPos())
                #agent pos -> agent dest -> pokemon src
                curr_distance += self.distance(self.position, graph_algo.get_graph().get_all_v()[self.dest].getPos())*scale

            scale = graph_algo.get_graph().all_out_edges_of_node(pokemon["src"])[pokemon["dest"]] * self.distance(graph_algo.get_graph().get_all_v()[pokemon["src"]].getPos(),graph_algo.get_graph().get_all_v()[pokemon["dest"]].getPos())
            #agent pos -> agent dest -> pokemon src -> pokemon pos
            curr_distance += self.distance(graph_algo.get_graph().get_all_v()[pokemon["src"]].getPos(),pokemon["pos"])*scale
            path = path + [pokemon["dest"]]
        
        return curr_distance,path

    def remove_target(self):
        self.target = None
        self.route = []
    
    def get_target(self):
        return self.target
            































































































    def build_route_from_pokemons(self, graph_algo:GraphAlgo, pokemons: List[dict]):
        best_pokemons = []
        new_route = []
        best_score = float('-inf')
        
        for i in range(len(pokemons)):
            temp = [n for n in pokemons]
            temp = temp[0:i] + temp[i+1:]
            path_without_i,value1,lenPath,new_pokemons = self.TSP_recursive(graph_algo,pokemons[i],temp)
            if len(path_without_i)<=1:
                continue


            lenPath1, path_src_to_i = graph_algo.shortest_path(self.dest,pokemons[i]["src"])
            lenPath2, path_i_to_first = graph_algo.shortest_path(pokemons[i]["dest"],path_without_i[0])
            lenPath3 = graph_algo.get_graph().all_out_edges_of_node(pokemons[i]["src"])[pokemons[i]["dest"]]

            path = path_src_to_i + path_i_to_first + path_without_i
            path_len = lenPath+lenPath1+lenPath2+lenPath3
            value = value1 + pokemons[i]["value"]

            score = value/path_len
            
            if(best_score<score):
                new_route = path
                best_score = score
                best_pokemons = [pokemons[i]["id"]] + new_pokemons
 
        out = []       
        for i in range(len(new_route)):
            if i<len(new_route)-1 and new_route[i] == new_route[i+1]:
                continue
            out.append(new_route[i])
        return out,best_pokemons,best_score


    def TSP_recursive(self,graph_algo:GraphAlgo,pokemon:dict,pokemons: List[dict]) -> tuple[List[int], float]:
        if len(pokemons)<1:
            return [],0,0,[]
        new_route = []
        best_score = float('-inf')
        best_value = 0
        best_length = 0
        for i in range(len(pokemons)):
            
            lenPath1, path_idx_to_i = graph_algo.shortest_path(pokemon["dest"],pokemons[i]["src"])
            lenPath1 += graph_algo.get_graph().all_out_edges_of_node(pokemons[i]["src"])[pokemons[i]["dest"]]
            path_idx_to_i = path_idx_to_i

            temp = [n for n in pokemons]
            temp = temp[0:i] + temp[i+1:]
            
            path_i_to_end,lenPath2,value1,new_pokemons = self.TSP_recursive(pokemons[i], temp)

            path_idx_to_end = path_idx_to_i + path_i_to_end
            path_len = lenPath1+lenPath2

            value = value1 + pokemons[i]["value"]
            score = value/path_len

            if(best_score<score):
                new_route = path_idx_to_end
                best_score = score
                best_length = path_len
                best_value = value
                best_pokemons = [pokemons[i]["id"]] + new_pokemons
        return new_route,best_length,best_value,best_pokemons


            











    
    

    #algorithm for determening the best way to reallocate the pokemon assigned to the agents
    def simulate_change(self,graph_algo:GraphAlgo, p_to_add:dict = None, best_p_found:dict={}):
        new_pokemon_route = []
        route_cost = {}
        new_route_cost = {}
        if p_to_add != None:
            new_pokemon_route = [i for i in self.pokemon_route]
            p_in_route= False
            for i in range(len(self.route)-1):
                if self.route[i] == p_to_add["src"] and self.route[i+1] ==  p_to_add["dest"]:
                    p_in_route = True
            if p_in_route:
                return 0
            new_pokemon_route.append(p_to_add)
            route_cost = self.calc_route_costs(graph_algo,self.route)
            
                
            
        elif graph_algo.get_graph().get_all_v()[p_to_add].isPokemon() and len(best_p_found)>0:
            route_cost = self.calc_route_costs(graph_algo,self.route)
            new_pokemon_route = [p for p in self.pokemon_route if(p not in best_p_found or route_cost[p] < best_p_found[p]["value"])]
        
        if new_pokemon_route != self.pokemon_route and len(new_pokemon_route)>0:
            
            new_route,new_pokemon_route,dest = self.build_route_from_pokemons(graph_algo,new_pokemon_route)
            
            new_route_cost = self.calc_route_costs(graph_algo,new_route,self.src.getId(),dest)
            #update best_p_found
            for key, value in new_route_cost.items():
                if key not in best_p_found or best_p_found[key]["value"] > value:
                    best_p_found[key] = {"id":self.id,"value":value}
            return sum(new_route_cost.values())-sum(route_cost.values())
        return 0
    
        

    #returns the weight to reach each point on the route from the start of the route
    def calc_route_costs(self,graph_algo:GraphAlgo,route,src=None,dest=None):
        route_costs = {}
        if dest == None:
            dest = self.dest
        if src == None:
            src = self.src
        if dest != -1:
            route_costs[dest] = graph_algo.get_graph().all_out_edges_of_node(self.src)[dest]-self.position
            src = dest
        for n in route:
            dest = n
            route_costs[dest] = graph_algo.get_graph().all_out_edges_of_node(src)[dest] + route_costs[src]
            src = dest

        return route_costs

    #takes a new pokemon that was summoned with its src and dest, changes this route to pass throgh the pokemon if its on the route
    def updateRoute(self,graph:DiGraph,src:int,pokemon_node:int,dest:int):

        if src == self.src and dest == self.dest and graph.all_out_edges_of_node(src)[dest]>self.position:
            self.route = [dest]+self.route
            self.dest = pokemon_node
        if len(self.route)>1:
            newPokemon = []
            new_route = [self.route[0]]
            if graph.get_all_v()[self.route[0]].isPokemon():
                newPokemon.append(self.route[0])

            for i in range(len(self.route)-1):
                if self.route[i] == src and self.route[i+1] == dest:
                    new_route.append(pokemon_node)
                    newPokemon.append(pokemon_node)
                
                if graph.get_all_v()[self.route[i+1]].isPokemon():
                    newPokemon.append(self.route[i+1])
                
                new_route.append(self.route[i+1])
            self.route = new_route
            self.pokemon_route = newPokemon


    def getId(self):
        return self.id
    def getSrc(self):
        return self.src
    def getDest(self):
        return self.dest





    

    

























