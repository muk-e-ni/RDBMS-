# rdbms/core/schema.py
from enum import Enum
from typing import Dict, List, Any, Optional

class DataType(Enum):
    INTEGER = "INT"
    VARCHAR = "VARCHAR"
    BOOLEAN = "BOOLEAN"
    DATE = "DATE"

class Column:
    def __init__(self, name: str, dtype: DataType, length: int = None, 
                 primary_key: bool = False, unique: bool = False, 
                 nullable: bool = True):
        self.name = name
        self.dtype = dtype
        self.length = length
        self.primary_key = primary_key
        self.unique = unique
        self.nullable = nullable
    
    def __repr__(self):
        result = f"{self.name} {self.dtype.value}"
        if self.length is not None:
            result += f"({self.length})"
        if self.primary_key:
            result += " PRIMARY KEY"
        elif self.unique:
            result += " UNIQUE"
        if not self.nullable:
            result += " NOT NULL"
        return result

class TableSchema:
    def __init__(self, name: str, columns: List[Column]):
        self.name = name
        self.columns = {col.name: col for col in columns}
        self.primary_key = [col.name for col in columns if col.primary_key]
        
    def validate_row(self, row: Dict[str, Any]) -> bool:
        """Validate a row against schema constraints"""
        # Check all required columns present
        for col_name, col in self.columns.items():
            if not col.nullable and col_name not in row:
                return False
            if col_name in row:
                # Type checking would go here
                pass
        return True
    
    def __repr__(self):
        cols = "\n  ".join(str(col) for col in self.columns.values())
        return f"Table: {self.name}\n  {cols}"

class Row:
    def __init__(self, values: Dict[str, Any], rowid: int = None):
        self.values = values
        self.rowid = rowid  # Internal row identifier for indexing