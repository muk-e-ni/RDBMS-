# core/executor.py
from typing import List, Dict, Any
from .schema import Column, TableSchema, DataType
from .storage import StorageEngine
from .index import Index

class QueryResult:
    """Container for query results"""
    def __init__(self, rows: List[Dict] = None, rowcount: int = 0):
        self.rows = rows or []
        self.rowcount = rowcount
    
    def __repr__(self):
        return f"QueryResult(rows={len(self.rows)}, affected={self.rowcount})"

class QueryExecutor:
    """Execute parsed SQL commands"""
    
    def __init__(self, storage: StorageEngine):
        self.storage = storage
        self.indexes: Dict[str, Dict[str, Index]] = {}  # table -> {column -> index}
    
    def execute(self, parsed: Dict[str, Any]) -> QueryResult:
        """Execute a parsed SQL command"""
        cmd_type = parsed['type']
        
        if cmd_type == 'CREATE_TABLE':
            return self._execute_create_table(parsed)
        elif cmd_type == 'INSERT':
            return self._execute_insert(parsed)
        elif cmd_type == 'SELECT':
            return self._execute_select(parsed)
        elif cmd_type == 'UPDATE':
            return self._execute_update(parsed)
        elif cmd_type == 'DELETE':
            return self._execute_delete(parsed)
        elif cmd_type == 'DROP_TABLE':
            return self._execute_drop_table(parsed)
        else:
            raise ValueError(f"Unsupported command type: {cmd_type}")
    
    def _execute_create_table(self, parsed: Dict[str, Any]) -> QueryResult:
        """Create a new table"""
        t_name = parsed['t_name']
        columns = []
        
        for col_def in parsed['columns']:
            columns.append(Column(
                name=col_def['name'],
                dtype=col_def['dtype'],
                length=col_def['length'],
                primary_key=col_def['primary_key'],
                unique=col_def['unique'],
                nullable=col_def['nullable']
            ))
        
        schema = TableSchema(t_name, columns)
        self.storage.save_schema(t_name, schema)
        
        # Create empty table file
        open(self.storage.table_path(t_name), 'w').close()
        
        # Initialize indexes for primary key and unique columns
        self.indexes[t_name] = {}
        for column in columns:
            if column.primary_key or column.unique:
                self._create_index(t_name, column.name)
        
        return QueryResult(rowcount=0)
    
    def _create_index(self, t_name: str, column_name: str):
        """Create an index on a column"""
        if t_name not in self.indexes:
            self.indexes[t_name] = {}
        
        index = Index(t_name, column_name)
        self.indexes[t_name][column_name] = index
        
        # index from existing data
        rows = self.storage.read_rows(t_name)
        for row in rows:
            if column_name in row.values:
                index.add(row.values[column_name], row.rowid)
        
        index.save(self.storage)
    
    def _execute_insert(self, parsed: Dict[str, Any]) -> QueryResult:
        """Insert a row into table"""
        t_name = parsed['t_name']
        schema = self.storage.load_schema(t_name)
        
        # Prepare row data
        if parsed['columns'] is None:
            # VALUES only, assume all columns in order
            values = parsed['values']
            columns = list(schema.columns.keys())
            if len(values) != len(columns):
                raise ValueError(f"Expected {len(columns)} values, got {len(values)}")
            row = dict(zip(columns, values))
        else:
            # Column-value pairs
            row = dict(zip(parsed['columns'], parsed['values']))
        
        # Validate against schema
        if not schema.validate_row(row):
            raise ValueError("Row violates schema constraints")
        
        # Check primary key uniqueness
        for pk_col in schema.primary_key:
            if pk_col in row:
                # Use index if available
                if t_name in self.indexes and pk_col in self.indexes[t_name]:
                    index = self.indexes[t_name][pk_col]
                    if row[pk_col] in index.index:
                        raise ValueError(f"Duplicate primary key value: {row[pk_col]}")
        
        # Insert row
        rowid = self.storage.insert_row(t_name, row)
        
        # Update indexes
        if t_name in self.indexes:
            for col_name, index in self.indexes[t_name].items():
                if col_name in row:
                    index.add(row[col_name], rowid)
            # Save indexes
            for index in self.indexes[t_name].values():
                index.save(self.storage)
        
        return QueryResult(rowcount=1)
    
    def _execute_select(self, parsed: Dict[str, Any]) -> QueryResult:
        """Select rows from table"""

        from_clause = parsed['from']
        if from_clause['type'] == 'SIMPLE':
            return self._execute_simple_select(parsed)
        
        elif from_clause['type'] == 'JOIN':
            return self._execute_join_select(parsed)
        
        else:
            raise ValueError(f"Unsupported FROM clause type: {from_clause['type']}")
        
    def _execute_simple_select(self, parsed: Dict[str, Any]) -> QueryResult:
        
        t_name = parsed['from']['table']
        schema = self.storage.load_schema(t_name)
        
        # Read all rows
        rows = self.storage.read_rows(t_name)
        
        # Apply WHERE clause
        filtered_rows = self._apply_where_clause(rows, parsed.get('where'), t_name)
        
    
        # Select columns
        result_rows = []
        selected_columns = parsed['columns']
        
        if selected_columns == ["*"]:
            selected_columns = list(schema.columns.keys())
        
        for row in filtered_rows:
            result_row = {}
            for col in selected_columns:
                if col in row.values:
                    result_row[col] = row.values[col]
                else:
                    result_row[col] = None
            result_rows.append(result_row)

        if parsed.get('order_by'):
            result_rows = self._apply_order_by(result_rows, parsed['order_by'])
        
        return QueryResult(rows=result_rows, rowcount=len(result_rows))
    

    def _execute_join_select(self, parsed: Dict[str, Any]) -> QueryResult:
        #getting table names from the parser

        from_clause = parsed['from']
        join_type = from_clause['join_type']
        left_table = from_clause['left_table']
        right_table = from_clause['right_table']
        on_clause = from_clause['on']

        #loading schemas

        left_schema = self.storage.load_schema(left_table)
        right_schema = self.storage.load_schema(right_table)

        #reading rows

        left_rows = self.storage.read_rows(left_table)
        right_rows = self.storage.read_rows(right_table)

        #performing JOIN

        if join_type == 'INNER':
            joined_rows = self._perform_inner_join(
                left_rows, right_rows, on_clause['left_column'], on_clause['right_column']
            )

        elif join_type == 'LEFT':
            joined_rows = self._perform_left_join(
                left_rows,right_rows, on_clause['left_column'], on_clause['right_column']
            )

        elif join_type == 'RIGHT':
            joined_rows = self._perform_right_join(
                left_rows, right_rows, on_clause['left_column'], on_clause['right_column']
            )
        
        else:
            raise ValueError(f"Unsupported JOIN type: {join_type}")
        
        #applying THE WHERE clause to joined rows

        filtered_rows = self._apply_where_clause_to_joined(
            joined_rows, parsed.get('where'), left_table, right_table
        )

        result_rows = []
        selected_columns = parsed['columns']

        if selected_columns == ["*"]:
            for row in filtered_rows:
                result_row = {}
                for  col in left_schema.columns:
                    if row['left'] is not None and hasattr(row['left'], 'values'):
                        result_row[f"{left_table}.{col}"] = row['left'].values.get(col)

                    else:
                        result_row[f"{left_table}.{col}"] = None

                for col in right_schema.columns:
                    if row['right'] is not None and hasattr(row['right'], 'values'):
                        result_row[f"{right_table}.{col}"] = row['right'].values.get(col)

                    else:
                        result_row[f"{right_table}.{col}"] = None

                result_rows.append(result_row)

        else:
            for row in filtered_rows:
                result_row = {}
                for col_spec in selected_columns:
                    if '.' in col_spec:
                        t_name, col_name = col_spec.split('.')

                        if t_name == left_table:
                            if row['left'] is not None and hasattr(row['left'], 'values'):
                                result_row[col_spec] = row['left'].values.get(col_name)
                            else:
                                result_row[col_spec] = None

                        elif t_name == right_table:
                            if row['right'] is not None and hasattr(row['right'], 'values'):
                                result_row[col_spec] = row['right'].values.get(col_name)
                            else:
                                result_row[col_spec] = None
                        else:
                            result_row[col_spec] = None
                    else:
                        if row['left'] is not None and hasattr(row['left'], 'values') and  col_spec in row['left'].values:
                            result_row[col_spec] = row['left'].values[col_spec]

                        elif row['right'] is not None and hasattr(row['right'], 'values') and col_spec in row['right'].values:
                            result_row[col_spec] = row['right'].values[col_spec]

                        else:
                            result_row[col_spec] = None
                result_rows.append(result_row)

        if parsed.get('order_by'):
            result_rows = self._apply_order_by(result_rows, parsed['order_by'])

        return QueryResult(rows=result_rows, rowcount=len(result_rows))
    
    def _perform_inner_join(self, left_rows, right_rows, left_key, right_key):

        joined_rows =[]

        #a hash map for right table if indexed

        right_map = {}

        for right_row in right_rows:
            key_value = right_row.values.get(right_key)
            if key_value is not None:
                if key_value not in right_map:
                    right_map[key_value] = []
                right_map[key_value].append(right_row)

        #now perform join
        for left_row in left_rows:
            key_value = left_row.values.get(left_key)
            if key_value is not None and key_value in right_map:
                for right_row in right_map[key_value]:
                    joined_rows.append({
                        'left': left_row,
                        'right': right_row
                    })
        return joined_rows
    
    def _perform_left_join(self, left_rows, right_rows, left_key, right_key):

        joined_rows = []

        if left_rows is None:
            left_rows = []
        if right_rows is None:
            right_rows =[]

        #hash map for right table

        right_map = {}
        for right_row in right_rows:
            key_value = right_row.values.get(right_key)
            if key_value is not None:
                if key_value not in right_map:
                    right_map[key_value] = []

                right_map[key_value].append(right_row)

        # now perform left join

        for left_row in left_rows:
            if left_row is None:
                joined_rows.append({
                    'left':None,
                    'right': None
                })
                continue
            key_value = left_row.values.get(left_key) if hasattr(left_row, 'values') else None
            if key_value is not None and key_value in right_map:

                #matchin rows found
                for right_row in right_map[key_value]:
                    joined_rows.append({
                        'left':left_row,
                        'right': right_row
                    })
            else:

                #no match

                joined_rows.append({
                    'left': left_row,
                    'right': None
                })

        return joined_rows
    
    def _perform_right_join(self,left_rows, right_rows, left_key, right_key):
        # reversing the tables and doing a left join

        if left_rows is None:
            left_rows = []
        if right_rows is None:
            right_rows = []

        joined = self._perform_left_join(right_rows,left_rows,right_key, left_key)

        #swaping left and right in results

        for row in joined:
            row['left'], row['right'] = row['right'], row['left']

        return joined
    
    def _apply_where_clause(self, rows, where, t_name=None):

        if not where:
            return rows
        
        filtered =[]

        for row in rows:
            if self._evaluate_condition(row.values, where, t_name):
                filtered.append(row)

        return filtered
    
    def _apply_where_clause_to_joined(self, joined_rows, where, left_table, right_table):

        if not where:
            return joined_rows
        
        filtered = []
        for joined_row in joined_rows:

            #combinig values from both tables
            values = {}

            #adding left table values with table prefix
            if joined_row['left'] is not None and hasattr(joined_row['left'], 'values'):
                for key, value in joined_row['left'].values.items():
                    values[f"{left_table}.{key}"] = value

                    values[key] = value # add without prefix

            #now right table values
            if joined_row['right'] is not None and hasattr(joined_row['right'], 'values'):
                for key, value in joined_row['right'].values.items():
                    values[f"{right_table}.{key}"] = value
                    values[key] = value 

            if self._evaluate_condition(values, where):
                filtered.append(joined_row)

        return filtered
    
    def _evaluate_condition(self, values, condition, default_table=None):

        if condition['type'] == 'AND':
            return all(self._evaluate_condition(values, cond, default_table) for cond in condition['conditions'])
        
        elif condition['type'] == 'OR':
            return any(self._evaluate_condition(values, cond, default_table) for cond in condition['conditions'])
        elif condition['type'] =='CONDITION':
            col = condition[ 'column']
            op = condition['operator']
            expected = condition['value']

            if '.' in col and col not in values:
                col_name = col.split('.')[1]
                if col_name in values:
                    col = col_name

            actual = values.get(col)

            if op == '=':
                return actual == expected
            elif op == '!=':
                return actual != expected
            elif op == '>':
                return actual is not None and actual > expected
            elif op == '<':
                return actual is not None and actual < expected
            elif op == '>=':
                return actual is not None and actual >= expected
            elif op == '<=':
                return actual is not None and actual <= expected
            elif op == 'LIKE':
                if actual is None or expected is None:
                    return False
                
                pattern = str(expected).replace('%', '.*')
                import re
                return bool(re.match(pattern,str(actual), re.IGNORECASE))
            else:
                raise ValueError(f"Unsupported operator: {op}")
            
        return False
    
    def _apply_order_by(self,rows, order_by_columns):

        if not order_by_columns or not rows:
            return rows
        
        def sort_key(row):
            key = []
            for col in order_by_columns:
                value = row.get(col)

                if value is None:
                    key.append((1, ''))
                else:
                    key.append((0,str(value).lower()))
            return key
        return sorted(rows, key=sort_key)
            
                                  

   
    def _execute_update(self, parsed: Dict[str, Any]) -> QueryResult:
        """Update rows in table"""
        t_name = parsed['t_name']
        updates = parsed['updates']
        where = parsed.get('where')
        
        # Read all rows
        rows = self.storage.read_rows(t_name)
        updated_count = 0
        
        for row in rows:
            should_update = True
            
            # Check WHERE condition
            if where:
                column = where['column']
                value = where['value']
                should_update = (column in row.values and row.values[column] == value)
            
            if should_update:
                # Remove old values from indexes
                if t_name in self.indexes:
                    for col_name, index in self.indexes[t_name].items():
                        if col_name in row.values:
                            index.remove(row.values[col_name], row.rowid)
                
                # Apply updates
                for col, new_value in updates.items():
                    row.values[col] = new_value
                
                # Add new values to indexes
                if t_name in self.indexes:
                    for col_name, index in self.indexes[t_name].items():
                        if col_name in row.values:
                            index.add(row.values[col_name], row.rowid)
                
                updated_count += 1
        
        # Rewrite table file with updates
        if updated_count > 0:
            self._rewrite_table(t_name, rows)
            
            # Save indexes
            if t_name in self.indexes:
                for index in self.indexes[t_name].values():
                    index.save(self.storage)
        
        return QueryResult(rowcount=updated_count)
    
    def _execute_delete(self, parsed: Dict[str, Any]) -> QueryResult:
        """Delete rows from table"""
        t_name = parsed['t_name']
        where = parsed.get('where')
        
        rows = self.storage.read_rows(t_name)
        deleted_count = 0
        new_rows = []
        
        for row in rows:
            should_delete = True
            
            # Check WHERE condition
            if where:
                column = where['column']
                value = where['value']
                should_delete = (column in row.values and row.values[column] == value)
            
            if should_delete:
                # Remove from indexes
                if t_name in self.indexes:
                    for col_name, index in self.indexes[t_name].items():
                        if col_name in row.values:
                            index.remove(row.values[col_name], row.rowid)
                deleted_count += 1
            else:
                new_rows.append(row)
        
        # Rewrite table file without deleted rows
        if deleted_count > 0:
            self._rewrite_table(t_name, new_rows)
            
            # Save indexes
            if t_name in self.indexes:
                for index in self.indexes[t_name].values():
                    index.save(self.storage)
        
        return QueryResult(rowcount=deleted_count)
    
    def _execute_drop_table(self, parsed: Dict[str, Any]) -> QueryResult:
        """Drop a table"""
        t_name = parsed['t_name']
        
        # Remove table files
        import os
        paths = [
            self.storage.table_path(t_name),
            self.storage.schema_path(t_name),
        ]
        
        for path in paths:
            if os.path.exists(path):
                os.remove(path)
        
        # Remove index files
        if t_name in self.indexes:
            for col_name in self.indexes[t_name]:
                idx_path = self.storage.index_path(t_name, col_name)
                if os.path.exists(idx_path):
                    os.remove(idx_path)
            del self.indexes[t_name]
        
        return QueryResult(rowcount=0)
    
    def _rewrite_table(self, t_name: str, rows: List):
        """Rewrite entire table file"""
        path = self.storage.table_path(t_name)
        schema = self.storage.load_schema(t_name)
        
        with open(path, 'w') as f:
            for row in rows:
                values = []
                for col_name in schema.columns:
                    value = row.values.get(col_name)
                    if value is None:
                        values.append("NULL")
                    else:
                        values.append(str(value).replace(',', '\\,'))
                f.write(','.join(values) + '\n')