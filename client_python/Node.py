import random
import numpy as np
class Edge():
    

    def __init__(self,weight,value):
        self.weight = weight
        self.value = value

    def __add__(self, e):
        if isinstance(e,Edge):
            return Edge(self.weight+e.weight,self.value+e.value)
        else:
            return Edge(self.weight+e,self.value)

    def __radd__(self, e):
        if isinstance(e,Edge):
            return Edge(self.weight+e.weight,self.value+e.value)
        else:
            return Edge(self.weight+e,self.value)


    def __sub__(self,e):
        if isinstance(e,Edge):
            return Edge(self.weight-e.weight,self.value-e.value)
        else:
            return Edge(self.weight-e,self.value)

    def __rsub__(self,e):
        if isinstance(e,Edge):
            return Edge(e.weight-self.weight,e.value-self.value)
        else:
            return Edge(e-self.weight,self.value)
    

    def __mul__(self, e):
        if isinstance(e,Edge):
            return Edge(self.weight*e.weight,self.value*e.value)
        else:
            return Edge(self.weight*e,self.value)

    def __rmul__(self,e):
        if isinstance(e,Edge):
            return Edge(self.weight*e.weight,self.value*e.value)
        else:
            return Edge(self.weight*e,self.value)


    def __truediv__(self,e):
        if isinstance(e,Edge) and e.value != 0:
            return Edge(self.weight/e.weight,self.value/e.value)
        else:
            return Edge(self.weight/e,self.value)
    def __rtruediv__(self,e):
        if isinstance(e,Edge) and self.value != 0:
            return Edge(e.weight/self.weight,e.value/self.value)
        else:
            return Edge(e/self.weight,self.value)

    
    def __format__(self, __format_spec: str) -> str:
        return "{:f}".format(self.weight,f=__format_spec)
    

    def __eq__(self,e):
        if isinstance(e,Edge):
            return self.decision_function() == e.decision_function()
        else:
            return self.weight==e
    def __ne__(self,e):
        return self.__eq__(e) == False

    def __lt__(self,e):
        if isinstance(e,Edge):
            return self.decision_function() < e.decision_function()
        else:
            return self.weight < e

    def __le__(self,e):
        return self.__lt__(e) or self.__eq__(e)
    

    def __gt__(self,e):
        return self.__le__(e) == False
    
    def __ge__(self,e):
        return self.__gt__(e) or self.__eq__(e)


    def decision_function(self):
        if self.value != 0:
            return self.weight/self.value
        return self.weight

class Node:
    def __init__(self,node_id: int, pos: tuple = None,random_range=10):
        self.parents = {}
        self.children = {}
        random_range = max(10,random_range)
        self.id = node_id
        self.color = "white"
        self.distance = Edge(float('inf'),0)
        self.prev = None
        if pos==None:
            pos =tuple([random.randrange(-10,10) for _ in range(3)])
        self.pos=pos

    def __repr__(self): #0: |edges out| 1 |edges in| 1
        return str(self.id)+": |edges out| "+str(len(self.children))+" |edges in| "+str(len(self.parents))
    def __str__(self):
        return self.__repr__()
    def getParents(self) -> dict:
        return self.parents
    def addParent(self,node_id: int,weight:float,value:int=0) -> None:
        self.parents[node_id]=Edge(weight,value)
    def getChildren(self) -> dict:
        return self.children
    def addChild(self,node_id: int,weight:float,value:int=0) -> None:
        self.children[node_id]=Edge(weight,value)

    def getId(self) -> int:
        return self.id


    def getColor(self) -> str:
        return self.color
    def setColor(self,c:str):
        self.color = c
    
    def getDistance(self) -> Edge:
        return self.distance

    def setDistance(self,d:float,val:int=None):
        if val == None:
            self.distance = Edge(d,self.distance.value)
        else:
            self.distance = Edge(d,val)


    def getPrev(self) -> int:
        return self.prev
    def setPrev(self,n:int):
        self.prev = n

    def getPos(self) -> tuple:
        return self.pos

