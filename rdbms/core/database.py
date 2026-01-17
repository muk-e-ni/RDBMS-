# core/database.py
from .parser import SQLParser
from .executor import QueryExecutor, QueryResult
from .storage import StorageEngine

class Database:
    """Main database interface"""
    
    def __init__(self, db_path: str = "data"):
        self.storage = StorageEngine(db_path)
        self.executor = QueryExecutor(self.storage)
    
    def execute(self, sql: str) -> QueryResult:
        """Execute SQL statement"""
        # Parse SQL
        parsed = SQLParser.parse(sql)
        
        # Execute command
        result = self.executor.execute(parsed)
        
        return result
    
    def query(self, sql: str) -> QueryResult:
        """Execute SQL query (SELECT)"""
        result = self.execute(sql)
        return result
    
    def close(self):
        """Close database connection"""
        # For now, nothing to close
        pass