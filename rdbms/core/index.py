import os
import pickle
from typing import Dict, List, Set, Any

class Index:

    def __init__(self, 
                 t_name: str,
                 column_name: str):
        self.t_name = t_name
        self.column_name = column_name
        self.index: Dict[Any, Set[int]] = {}
        
        
    def add(self,
                value: Any,
                rowid: int):
            
            if value not in self.index:
                self.index[value] = set()

            self.index[value].add(rowid)

    def remove(self,
                   value: Any, 
                   rowid:int):
            
            if value in self.index:
                self.index[value].discard(rowid)
                if not self.index[value]:
                    del self.index[value]
    def get(self,
                value: Any) -> Set[int]:
            return self.index.get(value, set())
        
    def save (self,
                  storage):
            path = storage.index_path(self.t_name,
                                      self.column_name)
            
            with open(path, 'wb') as f:
                pickle.dump(self.index, f)

    def load(self, storage):
            path = storage.index_path(self.t_name,
                                      self.column_name)
            if os.path.exists(path):
                with open(path, 'rb') as f:
                    self.index = pickle.load(f)

            else:
                self.index = {}


