# rdbms/core/parser.py
import re
from typing import List, Dict, Any, Tuple, Optional
from .schema import DataType

class SQLParser:
    """Simplified SQL parser"""
    
    @staticmethod
    def parse(sql: str) -> Dict[str, Any]:
        """Parse SQL statement into structured command"""
        sql = sql.strip()
        
        # Normalize SQL for case-insensitive matching but preserve original for values
        sql_upper = sql.upper()
        
        if sql_upper.startswith("CREATE TABLE"):
            return SQLParser._parse_create_table(sql)
        elif sql_upper.startswith("INSERT INTO"):
            return SQLParser._parse_insert(sql)
        elif sql_upper.startswith("SELECT"):
            return SQLParser._parse_select(sql)
        elif sql_upper.startswith("UPDATE"):
            return SQLParser._parse_update(sql)
        elif sql_upper.startswith("DELETE FROM"):
            return SQLParser._parse_delete(sql)
        elif sql_upper.startswith("DROP TABLE"):
            return SQLParser._parse_drop_table(sql)
        else:
            raise ValueError(f"Unsupported SQL statement: {sql}")
    
    @staticmethod
    def _parse_create_table(sql: str) -> Dict[str, Any]:
        """Parse CREATE TABLE statement"""
        # Extract table name and column definitions
        # Use case-insensitive matching
        match = re.match(r"CREATE\s+TABLE\s+(\w+)\s*\((.*)\)", sql, re.IGNORECASE | re.DOTALL)
        if not match:
            raise ValueError("Invalid CREATE TABLE syntax. Expected: CREATE TABLE name (col1 type, ...)")
        
        t_name = match.group(1).lower()
        columns_def = match.group(2).strip()
        
        # Parse column definitions
        columns = []
        # Split by commas, but not inside parentheses (for VARCHAR(50))
        col_defs = []
        current = ""
        paren_depth = 0
        
        for char in columns_def:
            if char == '(':
                paren_depth += 1
                current += char
            elif char == ')':
                paren_depth -= 1
                current += char
            elif char == ',' and paren_depth == 0:
                col_defs.append(current.strip())
                current = ""
            else:
                current += char
        
        if current.strip():
            col_defs.append(current.strip())
        
        for col_def in col_defs:
            if not col_def.strip():
                continue
                
            col_def_upper = col_def.upper()
            tokens = col_def.strip().split()
            col_name = tokens[0].lower()
            
            # Determine data type
            dtype_str = tokens[1].upper()
            length = None
            
            # Handle VARCHAR(50) or similar
            if '(' in dtype_str and ')' in dtype_str:
                # Extract type and length
                dtype_match = re.match(r"(\w+)\((\d+)\)", dtype_str)
                if dtype_match:
                    dtype_str = dtype_match.group(1)
                    length = int(dtype_match.group(2))
            elif '(' in tokens[1]:
                # Handle case where parentheses might be separate token
                if len(tokens) > 2 and '(' in tokens[2]:
                    length_match = re.search(r"\((\d+)\)", tokens[2])
                    if length_match:
                        length = int(length_match.group(1))
            
            # Map to DataType enum
            dtype_map = {
                "INT": DataType.INTEGER,
                "INTEGER": DataType.INTEGER,
                "VARCHAR": DataType.VARCHAR,
                "TEXT": DataType.VARCHAR,
                "STRING": DataType.VARCHAR,
                "BOOL": DataType.BOOLEAN,
                "BOOLEAN": DataType.BOOLEAN,
                "DATE": DataType.DATE
            }
            
            if dtype_str not in dtype_map:
                raise ValueError(f"Unsupported data type: {dtype_str}")
            
            dtype = dtype_map[dtype_str]
            
            # Check for constraints
            primary_key = "PRIMARY KEY" in col_def_upper
            unique = "UNIQUE" in col_def_upper or primary_key
            nullable = "NOT NULL" not in col_def_upper
            
            columns.append({
                'name': col_name,
                'dtype': dtype,
                'length': length,
                'primary_key': primary_key,
                'unique': unique,
                'nullable': nullable
            })
        
        return {
            'type': 'CREATE_TABLE',
            't_name': t_name,
            'columns': columns
        }
    
    @staticmethod
    def _parse_insert(sql: str) -> Dict[str, Any]:
        """Parse INSERT INTO statement"""
        # Use case-insensitive flag
        sql_upper = sql.upper()
        
        # Match: INSERT INTO table (col1, col2) VALUES (val1, val2)
        pattern = r"INSERT\s+INTO\s+(\w+)\s*\((.*?)\)\s*VALUES\s*\((.*)\)"
        match = re.match(pattern, sql, re.IGNORECASE | re.DOTALL)
        
        if not match:
            # Try without column names: INSERT INTO table VALUES (val1, val2)
            pattern = r"INSERT\s+INTO\s+(\w+)\s*VALUES\s*\((.*)\)"
            match = re.match(pattern, sql, re.IGNORECASE | re.DOTALL)
            if match:
                t_name = match.group(1).lower()
                values_str = match.group(2)
                return {
                    'type': 'INSERT',
                    't_name': t_name,
                    'columns': None,
                    'values': SQLParser._parse_values(values_str)
                }
            raise ValueError("Invalid INSERT syntax. Expected: INSERT INTO table VALUES (val1, val2) or INSERT INTO table (col1, col2) VALUES (val1, val2)")
        
        t_name = match.group(1).lower()
        columns_str = match.group(2)
        values_str = match.group(3)
        
        columns = [col.strip().lower() for col in columns_str.split(',')]
        values = SQLParser._parse_values(values_str)
        
        if len(columns) != len(values):
            raise ValueError(f"Column count ({len(columns)}) doesn't match value count ({len(values)})")
        
        return {
            'type': 'INSERT',
            't_name': t_name,
            'columns': columns,
            'values': values
        }
    
    @staticmethod
    def _parse_values(values_str: str) -> List[Any]:
        """Parse values list, handling quoted strings"""
        values = []
        current = ""
        in_quotes = False
        quote_char = None
        
        i = 0
        while i < len(values_str):
            char = values_str[i]
            
            if char in ("'", '"') and (not in_quotes or char == quote_char):
                # Handle escaped quotes
                if i + 1 < len(values_str) and values_str[i + 1] == char:
                    current += char
                    i += 1  # Skip next quote
                else:
                    in_quotes = not in_quotes
                    quote_char = char if in_quotes else None
                current += char
            elif char == ',' and not in_quotes:
                values.append(SQLParser._parse_value(current.strip()))
                current = ""
            else:
                current += char
            
            i += 1
        
        if current.strip():
            values.append(SQLParser._parse_value(current.strip()))
        
        return values
    
    @staticmethod
    def _parse_value(value: str) -> Any:
        """Convert string value to Python type"""
        value = value.strip()
        
        if value.upper() == "NULL":
            return None
        elif (value.startswith("'") and value.endswith("'")) or \
             (value.startswith('"') and value.endswith('"')):
            # Remove quotes
            return value[1:-1]
        elif value.upper() == "TRUE":
            return True
        elif value.upper() == "FALSE":
            return False
        elif re.match(r'^-?\d+$', value):
            return int(value)
        elif re.match(r'^-?\d+\.\d+$', value):
            return float(value)
        else:
            # Return as string
            return value
    
    @staticmethod
    def _parse_select(sql: str) -> Dict[str, Any]:
        """Parse SELECT statement (simplified)"""
        # SELECT parser handling JOIN
        pattern = r"SELECT\s+(.+?)\s+FROM\s+(.+?)(?:\s+WHERE\s+(.+?))?(?:\s+ORDER BY\s+(.+?))?$"
        match = re.match(pattern, sql, re.IGNORECASE | re.DOTALL)
        if not match:
            raise ValueError("Invalid SELECT syntax. Expected: SELECT col1, col2 FROM table WHERE condition")
        
        columns_str = match.group(1).strip()
        from_clause = match.group(2).strip()
        where_clause=match.group(3)
        order_by_clause = match.group(4)
        
        # Parse columns
        if columns_str.strip() == "*":
            columns = ["*"]
        else:
            columns = [col.strip().lower() for col in columns_str.split(',')]

        from_parsed = SQLParser._parse_from_clause(from_clause)
        
        # Parse WHERE clause (simplified)
        where = None
        if where_clause:
            where = SQLParser._parse_where_clause(where_clause)

        order_by = None
        if order_by_clause:
                order_by = [col.strip().lower for col in order_by_clause.split(',')]
        
        
        return {
                'type': 'SELECT',
                'columns': columns,
                'from': from_parsed,
                'where': where,
                'order_by': order_by
            }
    
    @staticmethod
    def _parse_from_clause(from_clause: str) -> Dict[str, Any]:
        from_clause_upper = from_clause.upper()

        if "INNER JOIN" in from_clause_upper:
            return SQLParser._parse_join(from_clause, "INNER")
        elif "LEFT JOIN" in from_clause_upper:
            return SQLParser._parse_join(from_clause, "LEFT")
        elif "RIGHT JOIN" in from_clause_upper:
            return SQLParser._parse_join(from_clause, "RIGHT")
        
        else:
            t_name = from_clause.strip().lower()
            return{
                'type': 'SIMPLE',
                'table': t_name
            }
        
    @staticmethod
    def _parse_join(from_clause: str, join_type: str) -> Dict[str, Any]:

        #pattern: table1 INNER JOIN table2 ON table1.id = table2.table1_id

        pattern= r"(\w+)\s+" + join_type + r"\s+JOIN\s+(\w+)\s+ON\s+(.+)"
        match = re.match(pattern, from_clause, re.IGNORECASE | re.DOTALL)

        if not match:
            raise ValueError (f"Invalid {join_type} JOIN syntax")
        
        left_table = match.group(1).lower()
        right_table = match.group(2).lower()
        on_clause = match.group(3).strip()

        #parsing ON condition: table1.column = table2.column

        on_pattern = r"(\w+)\.(\w+)\s*=\s*(\w+)\.(\w+)"
        on_match = re.match(on_pattern, on_clause, re.IGNORECASE)

        if not on_match:
            raise ValueError (f"Invalid ON clause: { on_clause}")
        
        left_table_ref = on_match.group(1).lower()
        left_column = on_match.group(2).lower()
        right_table_ref = on_match.group(3).lower()
        right_column = on_match.group(4).lower()
        
        if left_table_ref != left_table:
            raise ValueError(f"Left table reference mismatch: {left_table_ref} != {left_table}")
        if right_table_ref != right_table:
            raise ValueError(f"Right table reference mismatch: {right_table_ref} != {right_table}")
        
        return{
            'type': 'JOIN',
            'join_type': join_type.upper(),
            'left_table': left_table,
            'right_table': right_table,

            'on':{
                'left_column': left_column,
                'right_column': right_column
            }
        }
    
    @staticmethod
    def _parse_where_clause(where_clause:str) -> Dict[str, Any]:

        where_clause = where_clause.strip()

        if " AND " in where_clause.upper():
            parts = re.split(r'\s+AND\S+', where_clause, flags = re.IGNORECASE)
            conditions = [ SQLParser._parse_simple_condition(p.strip()) for p in parts]

            return{
                'type': 'AND',
                'conditions': conditions
            }
        elif " OR " in where_clause.upper():
            parts =re.split(r'\s+OR\s+', where_clause, flags=re.IGNORECASE)
            conditions = [SQLParser._parse_simple_condition(p.strip()) for p in parts]

            return{
                'type': 'OR',
                 'conditions': conditions
            }
        else:
            return SQLParser._parse_simple_condition(where_clause)
        
    @staticmethod
    def _parse_simple_condition(condition: str) -> Dict[str, Any]:
        
        #support: col = value, col > value, col LIKE "pattern"

        pattern = r"(\w+)\s*([=<>!]+|LIKE|IN)\s*(.+)"
        match = re.match(pattern, condition, re.IGNORECASE)

        if not match:

            #try table.column syntax

            pattern = r"(\w+\.\w+)\s*([=<>!]+|LIKE|IN)\s*(.+)"
            match = re.match(pattern, condition, re.IGNORECASE)

            if not match:
                raise ValueError(f"Invalid condition: {condition}")
            
        column = match.group(1).lower()
        operator = match.group(2).upper()
        raw_value = match.group(3).strip()

        value = SQLParser._parse_value(raw_value)

        return{
            'type': 'CONDITION',
            'column': column,
            'operator': operator,
            'value': value
        }


    


    @staticmethod
    def _parse_update(sql: str) -> Dict[str, Any]:
        """Parse UPDATE statement"""
        pattern = r"UPDATE\s+(\w+)\s+SET\s+(.+?)\s+WHERE\s+(.+)"
        match = re.match(pattern, sql, re.IGNORECASE | re.DOTALL)
        if not match:
            raise ValueError("Invalid UPDATE syntax. Expected: UPDATE table SET col1 = val1 WHERE condition")
        
        t_name = match.group(1).lower()
        set_clause = match.group(2).strip()
        where_clause = match.group(3).strip()
        
        # Parse SET clause
        updates = {}
        assignments = [a.strip() for a in set_clause.split(',')]
        for assignment in assignments:
            if '=' not in assignment:
                raise ValueError(f"Invalid assignment: {assignment}")
            col, value = assignment.split('=', 1)
            updates[col.strip().lower()] = SQLParser._parse_value(value.strip())
        
        # Parse WHERE clause
        where = None
        where_pattern = r"(\w+)\s*([=<>!]+)\s*(.+)"
        where_match = re.match(where_pattern, where_clause, re.IGNORECASE)
        if where_match:
            column = where_match.group(1).lower()
            operator = where_match.group(2).strip()
            raw_value = where_match.group(3).strip()
            value = SQLParser._parse_value(raw_value)
            where = {'column': column, 'op': operator, 'value': value}
        else:
            raise ValueError(f"Invalid WHERE clause: {where_clause}")
        
        return {
            'type': 'UPDATE',
            't_name': t_name,
            'updates': updates,
            'where': where
        }
    
    @staticmethod
    def _parse_delete(sql: str) -> Dict[str, Any]:
        """Parse DELETE FROM statement"""
        pattern = r"DELETE\s+FROM\s+(\w+)(?:\s+WHERE\s+(.+))?"
        match = re.match(pattern, sql, re.IGNORECASE | re.DOTALL)
        if not match:
            raise ValueError("Invalid DELETE syntax. Expected: DELETE FROM table WHERE condition")
        
        t_name = match.group(1).lower()
        where_clause = match.group(2)
        
        where = None
        if where_clause:
            where_clause = where_clause.strip()
            where_pattern = r"(\w+)\s*([=<>!]+)\s*(.+)"
            where_match = re.match(where_pattern, where_clause, re.IGNORECASE)
            if where_match:
                column = where_match.group(1).lower()
                operator = where_match.group(2).strip()
                raw_value = where_match.group(3).strip()
                value = SQLParser._parse_value(raw_value)
                where = {'column': column, 'op': operator, 'value': value}
        
        return {
            'type': 'DELETE',
            't_name': t_name,
            'where': where
        }
    
    @staticmethod
    def _parse_drop_table(sql: str) -> Dict[str, Any]:
        """Parse DROP TABLE statement"""
        match = re.match(r"DROP\s+TABLE\s+(\w+)", sql, re.IGNORECASE)
        if not match:
            raise ValueError("Invalid DROP TABLE syntax. Expected: DROP TABLE t_name")
        
        return {
            'type': 'DROP_TABLE',
            't_name': match.group(1).lower()
        }
    
