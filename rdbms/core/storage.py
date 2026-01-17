# core/storage.py
import os
import json
import pickle
from typing import List, Dict, Any
from .schema import TableSchema, Column, Row, DataType

class StorageEngine:
    def __init__(self, db_path: str = "data"):
        self.db_path = db_path
        os.makedirs(db_path, exist_ok=True)
        
    def table_path(self, t_name: str) -> str:
        return os.path.join(self.db_path, f"{t_name}.tbl")
    
    def schema_path(self, t_name: str) -> str:
        return os.path.join(self.db_path, f"{t_name}.schema")
    
    def index_path(self, t_name: str, column: str) -> str:
        return os.path.join(self.db_path, f"{t_name}_{column}.idx")
    
    def save_schema(self, t_name: str, schema: TableSchema):
        """Save table schema to disk"""
        with open(self.schema_path(t_name), 'w') as f:
            json.dump({
                'name': schema.name,
                'columns': [
                    {
                        'name': col.name,
                        'dtype': col.dtype.value,
                        'length': col.length,
                        'primary_key': col.primary_key,
                        'unique': col.unique,
                        'nullable': col.nullable
                    }
                    for col in schema.columns.values()
                ]
            }, f, indent=2)
    
    def load_schema(self, t_name: str) -> TableSchema:
        """Load table schema from disk"""
        path = self.schema_path(t_name)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Table {t_name} does not exist")
        
        with open(path, 'r') as f:
            data = json.load(f)
        
        columns = []
        for col_data in data['columns']:
            columns.append(Column(
                name=col_data['name'],
                dtype=DataType(col_data['dtype']),
                length=col_data['length'],
                primary_key=col_data['primary_key'],
                unique=col_data['unique'],
                nullable=col_data['nullable']
            ))
        
        return TableSchema(data['name'], columns)
    
    def insert_row(self, t_name: str, row: Dict[str, Any]) -> int:
        """Append a row to table file, return rowid"""
        path = self.table_path(t_name)
        # Simple CSV-like format for now
        with open(path, 'a') as f:
            # Convert dict to CSV line
            values = []
            schema = self.load_schema(t_name)
            for col_name in schema.columns:
                value = row.get(col_name)
                if value is None:
                    values.append("NULL")
                else:
                    values.append(str(value).replace(',', '\\,'))
            f.write(','.join(values) + '\n')
        
        # Return line number as rowid
        with open(path, 'r') as f:
            return sum(1 for _ in f)  # Count lines
    
    def read_rows(self, t_name: str) -> List[Dict[str, Any]]:
        """Read all rows from table"""
        path = self.table_path(t_name)
        if not os.path.exists(path):
            return []
        
        schema = self.load_schema(t_name)
        rows = []
        
        with open(path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                if line.strip():
                    values = line.strip().split(',')
                    row = {}
                    for col_name, raw_value in zip(schema.columns.keys(), values):
                        if raw_value == "NULL":
                            row[col_name] = None
                        else:
                            # Basic type conversion
                            col = schema.columns[col_name]
                            if col.dtype == DataType.INTEGER:
                                row[col_name] = int(raw_value)
                            elif col.dtype == DataType.BOOLEAN:
                                row[col_name] = raw_value.lower() == 'true'
                            else:
                                row[col_name] = raw_value.replace('\\,', ',')
                    rows.append(Row(row, line_num))
        
        return rows
    
    def delete_row(self, t_name: str, rowid: int) -> bool:
        """Delete a row by rowid (mark as deleted)"""
        # For simplicity, we'll rewrite the entire file
        path = self.table_path(t_name)
        rows = self.read_rows(t_name)
        
        if 1 <= rowid <= len(rows):
            # Remove the row
            del rows[rowid - 1]
            
            # Rewrite file
            with open(path, 'w') as f:
                for row in rows:
                    values = []
                    for col_name in self.load_schema(t_name).columns:
                        value = row.values.get(col_name)
                        if value is None:
                            values.append("NULL")
                        else:
                            values.append(str(value).replace(',', '\\,'))
                    f.write(','.join(values) + '\n')
            return True
        return False