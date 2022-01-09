from GraphAlgoInterface import GraphAlgoInterface
from GraphInterface import GraphInterface
from DiGraph import DiGraph
import json
from typing import List




class GraphAlgo(GraphAlgoInterface):
    def __init__(self,g:GraphInterface = None):
        self.graph = g

    def get_graph(self) -> GraphInterface:
        return self.graph
    def load_from_json(self,json_path:str="",json_string:str="") -> bool:
        self.graph = DiGraph()
        data = {}
        if json_path != "":
            try:
                with open(json_path,'r') as f:
                    data = json.loads(f.read())
                    self.load_json(data)
            except:
                return False
            return True
        elif json_string != "":
            try:
                data = json.loads(json_string)
                self.load_json(data)
            except:
                return False
            return True
        return False
        

        return True
    def load_json(self,data):
        for node in data["Nodes"]:
            if "pos" in node:
                pos = tuple([ float(i) for i in node["pos"].split(',')] )
            else:
                pos = None
            id = node["id"]
            
            self.graph.add_node(id,pos)
        
        for edge in data["Edges"]:
            src = edge["src"]
            dest = edge["dest"]
            w = edge["w"]
            self.graph.add_edge(src,dest,w)
        



    def save_to_json(self, file_name: str) -> bool:
        try:
            data = {}
            data["Edges"] = []
            data["Nodes"] = []
            for idx in self.graph.get_all_v():
                for childIdx,w in self.graph.all_out_edges_of_node(idx).items():
                    data["Edges"].append({
                        "src":idx,
                        "w":w,
                        "dest":childIdx
                    })
                pos = str(self.graph.get_all_v()[idx].getPos())
                if '(' and ')' in pos:
                    pos = pos[1:-1]
                    pos.replace(" ","")
                
                data["Nodes"].append({
                    "pos":pos,
                    "id":idx
                })
            with open(file_name,'w') as outfile:
                json.dump(data,outfile)
        except:
            return False
        return True





    def shortest_path(self, id1: int, id2: int) -> tuple[float, List[int]]:
        for k,v in self.graph.get_all_v().items():
           v.setDistance(float('inf'))
           v.setColor("white")
           v.setPrev(None)

        self.graph.get_all_v()[id1].setDistance(0)
        unVisited = []
        self.add_next_nodes(unVisited,id1)

        while len(unVisited) > 0:
            
            current = unVisited[0]
            
            unVisited = unVisited[1:]
            if self.graph.get_all_v()[current].getColor() != "white":
                continue
            self.graph.get_all_v()[current].setColor("black")
            self.add_next_nodes(unVisited,current)
        if(self.graph.get_all_v()[id2].getDistance()) == float('inf'):
            return float('inf'), []
        
        shortestPath = [id2]
        self.generate_shortest_path(shortestPath,id2)
        shortestPath = shortestPath[::-1]
        return self.graph.get_all_v()[id2].getDistance(), shortestPath


    def generate_shortest_path(self,path:List[int],target:int) -> None:
        if(self.graph.get_all_v()[target].getPrev() != None):
            path.append(self.graph.get_all_v()[target].getPrev() )
            self.generate_shortest_path(path,self.graph.get_all_v()[target].getPrev())
        return


    def add_next_nodes(self,lst:List[dict], node_id:int)->None:
        for k,v in self.graph.all_out_edges_of_node(node_id).items():
            if self.graph.get_all_v()[k].getColor() == "white":
                if self.graph.get_all_v()[k].getDistance() > self.graph.get_all_v()[node_id].getDistance()+v:
                    self.graph.get_all_v()[k].setDistance(self.graph.get_all_v()[node_id].getDistance()+v)
                    self.graph.get_all_v()[k].setPrev(node_id)                
                idx = 0
                while idx<len(lst) and self.graph.get_all_v()[lst[idx]].getDistance() < self.graph.get_all_v()[k].getDistance():
                    idx+=1
                lst.insert(idx,k)
        
            


    def TSP(self, node_lst: List[int]) -> tuple[List[int], float]:
        best_lst = []
        best_length = float('inf')
        for i in range(len(node_lst)):
            temp = [n for n in node_lst]
            temp = temp[0:i] + temp[i+1:]
            path_without_i,lenPath1 = self.TSP_recursive(node_lst[i],temp)
            if len(path_without_i)<=1:
                continue
            lenPath2, path_i_to_first = self.shortest_path(node_lst[i],path_without_i[0])

            path = path_i_to_first + path_without_i
            path_len = lenPath1+lenPath2
            
            if(path_len<best_length):
                best_lst = path
                best_length = path_len
        out = []
        
        for i in range(len(best_lst)):
            if i<len(best_lst)-1 and best_lst[i] == best_lst[i+1]:
                continue
            out.append(best_lst[i])
        return out,best_length


    def TSP_recursive(self,idx:int,node_lst: List[int]) -> tuple[List[int], float]:
        if len(node_lst)<1:
            return [],0
        best_length = float('inf')
        best_lst = []

        for i in range(len(node_lst)):
            lenPath1, path_idx_to_node_i = self.shortest_path(idx,node_lst[i])
            temp = [n for n in node_lst]
            temp = temp[0:i] + temp[i+1:]
            
            path_i_to_end,lenPath2 = self.TSP_recursive(node_lst[i], temp)
            path_idx_to_end = path_idx_to_node_i + path_i_to_end
            path_len = lenPath1+lenPath2
            if(path_len<best_length):
                best_length = path_len
                best_lst = path_idx_to_end
        return best_lst,best_length




    def centerPoint(self) -> tuple[int, float]:
        if False==self.isConnected():
            return None
        distanceMat = self.all_pairs_shortest_path()
        distances = { i: max(nodes.values())  for i,nodes in  distanceMat.items()}
        
        return min(distances.items(), key=lambda x: x[1])
    

    def isConnected(self) -> bool:
        flg = True
        if(self.graph.v_size()==0):
            return True
        for k,v in self.graph.get_all_v().items():
            v.setDistance(float('inf'))
            v.setColor("white")

        #check if there exists a path between all nodes in the graph 
        self.dfs(0)
        for k,v in self.graph.get_all_v().items():
            if(v.getColor() == "white"):
                flg = False
            v.setDistance(float('inf'))
            v.setColor("white")
        if flg == False:
            return False
        
        #check if there exists a path between all nodes in the transpose graph 
        self.dfs(0,False)
        for k,v in self.graph.get_all_v().items():
            if(v.getColor() == "white"):
                flg = False
            v.setDistance(float('inf'))
            v.setColor("white")
        if flg == False:
            return False
            

        return True


    def dfs(self,idx:int,direction:bool = True) -> None:
        if(self.graph.get_all_v()[idx].getColor() != "white"):
            return
        self.graph.get_all_v()[idx].setColor("gray")
        #going from parent to child
        if direction == True:
            for childIdx in self.graph.all_out_edges_of_node(idx):
                self.dfs(childIdx)
        #going from child to parent
        else:
            for parentIdx in self.graph.all_in_edges_of_node(idx):
                self.dfs(parentIdx,False)

        self.graph.get_all_v()[idx].setColor("black")
        return


    def all_pairs_shortest_path(self) -> List[List[float]]:
        matrix = {j:{i:float('inf') for i in self.graph.get_all_v()} for j in self.graph.get_all_v()}
        for src in self.graph.get_all_v():
            for dest,w in self.graph.all_out_edges_of_node(src).items():
                matrix[src][dest] = w
        for matNum in self.graph.get_all_v():
            new_nodes = [i for i in self.graph.get_all_v() if i!=matNum]
            for src in new_nodes:
                for dest in new_nodes:
                    if(src != dest):
                        if matrix[src][matNum] != float('inf') and matrix[matNum][dest] != float('inf'):
                            matrix[src][dest] = min(matrix[src][dest], matrix[src][matNum] + matrix[matNum][dest])
                    else:
                        matrix[src][dest] = 0
        return matrix
            














