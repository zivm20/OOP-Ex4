from random import getstate
from GraphAlgo import GraphAlgo
from DiGraph import DiGraph
from Node import Node
from client import Client


EPS = 0.001
class Agent:

    def __init__(self,id,weight_per_time,src,dest):
        self.id = id
        self.weight_per_time = weight_per_time

        self.route = []
        self.pokemon_route = []
        self.position = 0
        self.time = 0
        self.dest = dest
        self.src = src

    #updates the agent
    def update(self, graph_algo:GraphAlgo, client:Client, time:int,real_dest:int):
        graph = graph_algo.get_graph()
        state = self.get_state_at_time(graph,time)
        
        
        if state["dest"] != self.dest:
            old_dest = self.dest
            old_src = self.src
            if len(self.route)>0:
                if(self.dest != -1):
                    self.src = self.dest
                self.dest = self.route[0]
                self.route = self.route[1:]
                self.position = 0
                self.time = time
                if graph_algo.get_graph().get_all_v()[old_dest].isPokemon():
                    
                    self.pokemon_route = self.pokemon_route[1:]
                    self.position = graph_algo.get_graph().all_out_edges_of_node(old_src)[old_dest]
                    graph_algo.get_graph().remove_node(old_dest)
                    print(self.pokemon_route,state["pokemon_route"])
                    #print(self.route,state["route"])
                    self.src = old_src
                    return True
            #print("time",time,"src",self.src,"dest",self.dest,"real dest",real_dest)
            
        
        if real_dest != self.dest:
            
            if graph_algo.get_graph().get_all_v()[self.dest].isPokemon():
                
                new_dest = [i for i in graph_algo.get_graph().all_out_edges_of_node(self.dest)][0]
                if real_dest != new_dest:
                    #print("time",time,"src",self.src,"dest",self.dest,"real dest",real_dest)
                    self.time = time
                    self.pos = 0
                    client.choose_next_edge('{"agent_id":'+str(self.id)+', "next_node_id":'+str(new_dest)+'}')
                    return True
            elif graph_algo.get_graph().get_all_v()[self.src].isPokemon() != True:
                #print("time",time,"src",self.src,"dest",self.dest,"real dest",real_dest)
                self.time = time
                self.pos = 0
                client.choose_next_edge('{"agent_id":'+str(self.id)+', "next_node_id":'+str(self.dest)+'}')
                return True
            return False


        state = self.get_state_at_time(graph_algo.get_graph(),time)
        self.position = state["pos"]
        self.time = time
        return False

    #returns true iff the agent reached a node and now requires us to update the server
    def update_required(self, graph_algo:GraphAlgo, time:int,real_dest:int)->bool:
        graph = graph_algo.get_graph()
        state = self.get_state_at_time(graph,time)
        return real_dest != state["dest"]
    
    #returns the state of the agent at some time stamp
    def get_state_at_time(self,graph:DiGraph,time:int) ->tuple:
        time = time - self.time
        curr_pos = self.position
        curr_route = [i for i in self.route]
        curr_pokemon = [i for i in self.pokemon_route]
        src = self.src
        dest = self.dest
        
        if dest == -1 and len(curr_route)>0:
            dest = curr_route[0]
            if graph.get_all_v()[dest].isPokemon():
                curr_pokemon = curr_pokemon[1:]
            curr_route = curr_route[1:]
        
        if dest != -1:
            travel_distance = (self.weight_per_time*time) + curr_pos 
            while travel_distance > graph.all_out_edges_of_node(src)[dest]:
                travel_distance -= graph.all_out_edges_of_node(src)[dest]
                if graph.get_all_v()[dest].isPokemon():
                    curr_pokemon = curr_pokemon[1:]
                
                curr_pos=0
                src = dest
                if len(curr_route)==0:
                    dest = -1
                    break
                dest = self.route[0]
                curr_route = curr_route[1:]
        
            if dest != -1:
                curr_pos = travel_distance
            else:
                curr_pos = 0

            """
            for i in range(time):
                
                weight = graph.all_out_edges_of_node(src)[dest]
                while i < time and curr_pos < weight:
                    curr_pos = curr_pos+self.weight_per_time
                    i+=1
                if i<time:
                    if 0<len(curr_route):
                        if graph.get_all_v()[dest].isPokemon():
                            curr_pokemon = curr_pokemon[1:]
                        curr_pos = 0
                        src = dest
                        dest = self.route[0]
                        curr_route = curr_route[1:]
                    else:
                        curr_pos = 0
                        src = dest
                        dest = -1
                        break
            """
        return {"pos":curr_pos,"src":src,"dest":dest,"route":curr_route,"pokemon_route":curr_pokemon}

    #algorithm for determening the best way to reallocate the pokemon assigned to the agents
    def simulate_change(self,graph_algo:GraphAlgo, p_to_add:int = -1, best_p_found:dict={}):
        new_pokemon_route = []
        route_cost = {}
        new_route_cost = {}
        if p_to_add != -1 and graph_algo.get_graph().get_all_v()[p_to_add].isPokemon() and p_to_add != self.dest:
            new_pokemon_route = [i for i in self.pokemon_route]
            if (p_to_add in self.route) == False:
                route_cost = self.calc_route_costs(graph_algo,self.route)
                new_pokemon_route.append(p_to_add)
                
            
        elif graph_algo.get_graph().get_all_v()[p_to_add].isPokemon() and len(best_p_found)>0:
            route_cost = self.calc_route_costs(graph_algo,self.route)
            new_pokemon_route = [p for p in self.pokemon_route if(p not in best_p_found or route_cost[p] < best_p_found[p]["value"])]
        
        if new_pokemon_route != self.pokemon_route and len(new_pokemon_route)>0:
            
            new_route,src,dest = self.build_route_from_pokemons(graph_algo,new_pokemon_route)
            
            new_route_cost = self.calc_route_costs(graph_algo,new_route,src,dest)
            #update best_p_found
            for key, value in new_route_cost.items():
                if key not in best_p_found or best_p_found[key]["value"] > value:
                    best_p_found[key] = {"id":self.id,"value":value}
            return sum(new_route_cost.values())-sum(route_cost.values())
        return 0
    
    #use tsp to find the shortest path that starts at this agents "dest" and goes over all the pokemon in the list
    def build_route_from_pokemons(self, graph_algo:GraphAlgo,new_pokemon_route,inplace=False):
        new_route = []
        src = self.src
        dest = self.dest
        if len(new_pokemon_route)>0:
            dest = self.dest
            if dest == -1:
                dest = self.src
            new_route_p_order,_ = graph_algo.TSP_recursive(dest,new_pokemon_route)
            _,new_route_to_first = graph_algo.shortest_path(dest,new_route_p_order[0])
            temp = new_route_to_first + new_route_p_order
            new_route = []
            for i in range(len(temp)):
                if i<len(temp)-1 and temp[i] == temp[i+1]:
                    continue
                new_route.append(temp[i])

            if len(new_route)>0 and graph_algo.get_graph().get_all_v()[new_route[-1]].isPokemon():
                outEdges = [i for i in graph_algo.get_graph().all_out_edges_of_node(new_route[-1])]
                new_route.append(outEdges[0])
            if self.dest == -1 and len(new_route)>1:
                src = new_route[0]
                dest = new_route[1]
                new_route = new_route[2:]
            elif len(new_route)>0:
                new_route = new_route[1:]
            
        if inplace:
            self.route = new_route
            self.src=src
            self.dest=dest
            self.pokemon_route = new_pokemon_route
        return new_route,src,dest
        

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





    

    

























