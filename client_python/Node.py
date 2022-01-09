import random
class Node:
    def __init__(self,node_id: int, pos: tuple = None,random_range=10):
        self.parents = {}
        self.children = {}
        random_range = max(10,random_range)
        self.id = node_id
        self.color = "white"
        self.pokemon = False
        self.distance = float('inf')
        self.value = 0
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
    def addParent(self,node_id: int,weight:float) -> None:
        self.parents[node_id]=weight
    def getChildren(self) -> dict:
        return self.children
    def addChild(self,node_id: int,weight:float) -> None:
        self.children[node_id]=weight

    def getId(self) -> int:
        return self.id

    def getValue(self):
        return self.value

    def setValue(self,v):
        self.value = v

    def getColor(self) -> str:
        return self.color
    def setColor(self,c:str):
        self.color = c
    
    def getDistance(self) -> float:
        return self.distance
    def setDistance(self,d:float):
        self.distance = d

    def getPrev(self) -> int:
        return self.prev
    def setPrev(self,n:int):
        self.prev = n

    def getPos(self) -> tuple:
        return self.pos

    def isPokemon(self)->bool:
        return self.pokemon
        
    def setPokemon(self,flg:bool)->bool:
        self.pokemon = flg 