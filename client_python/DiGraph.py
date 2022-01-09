from GraphInterface import GraphInterface
from Node import Node

class DiGraph(GraphInterface):
    """Implementation of GraphInterface"""
    def __init__(self,graph:GraphInterface=None):
        
        self.nodes = {}
        self.mc = 0
        
        if graph != None:
            for k in graph.get_all_v():
                self.add_node(k)
            for k in graph.get_all_v():
                for node2,weight in graph.all_out_edges_of_node(k).items():
                    self.add_edge(k,node2,weight)

    def __repr__(self):
        return "Graph: |V|="+str(self.v_size())+" , |E|="+str(self.e_size())
    def __str__(self):
        return self.__repr__()

    def v_size(self) -> int:
        
        return len(self.nodes)

    def e_size(self) -> int:
       return sum([len(node.getParents()) for node in self.nodes.values()]) 
       
    def get_all_v(self) -> dict:
        return self.nodes

    def all_in_edges_of_node(self, id1: int) -> dict:
        return self.nodes[id1].getParents()

    def all_out_edges_of_node(self, id1: int) -> dict:
       return self.nodes[id1].getChildren()

    def get_mc(self) -> int:
        return self.mc

    def add_edge(self, id1: int, id2: int, weight: float) -> bool:
        if id1 in self.nodes and id2 in self.nodes and (id1 in self.nodes[id2].getParents()) == False:
            self.nodes[id1].addChild(id2,weight)
            self.nodes[id2].addParent(id1,weight)
            self.mc += 1
            return True
        return False

    def add_node(self, node_id: int, pos: tuple = None) -> bool:
        if (node_id in self.nodes) == False:
            self.nodes[node_id] = Node(node_id,pos,self.v_size())
            self.mc+=1
            return True
        return False

    def remove_node(self, node_id: int) -> bool:
        if node_id in self.nodes:
            parents_idx = [idx for idx in self.nodes[node_id].getParents()]
            children_idx = [idx for idx in self.nodes[node_id].getChildren()]
            
            for idx in parents_idx:
                self.remove_edge(idx,node_id)
            for idx in children_idx:
                self.remove_edge(node_id,idx)
            del self.nodes[node_id]
            return True
        return False
        

    def remove_edge(self, node_id1: int, node_id2: int) -> bool:
        if node_id1 in self.nodes and node_id2 in self.nodes and node_id1 in self.nodes[node_id2].getParents():
            del self.nodes[node_id1].getChildren()[node_id2]
            del self.nodes[node_id2].getParents()[node_id1]
            self.mc += 1
            return True
        return False