#!/usr/bin/env python3
# repl.py - Interactive REPL for the RDBMS

import sys
  # For command history
from core.database import Database
def print_help():
    print("""
MyRDBMS Commands:
    .help              - Show this help
    .tables            - List all tables
    .exit or .quit     - Exit the REPL
    .schema <table>    - Show table schema
    SQL                - Execute SQL statement
    
SQL Examples:
    CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(50))
    INSERT INTO users VALUES (1, 'Alice')
    SELECT * FROM users
    SELECT * FROM users WHERE id = 1
    UPDATE users SET name = 'Bob' WHERE id = 1
    DELETE FROM users WHERE id = 1
    DROP TABLE users
""")

def print_table(rows, headers):
    """Pretty print table data"""
    if not rows:
        print("(no rows)")
        return
    
    # Calculate column widths
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, col in enumerate(headers):
            col_widths[i] = max(col_widths[i], len(str(row.get(col, ''))))
    
    # Print header
    header_row = " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
    print(header_row)
    print("-" * len(header_row))
    
    # Print rows
    for row in rows:
        row_str = " | ".join(str(row.get(col, '')).ljust(col_widths[i]) for i, col in enumerate(headers))
        print(row_str)

def main():
    print("############## W3LCOM3 TO MY SIMPLE RDBMS REPL ################## ")
    print("Type .help for commands, .exit to quit")
    
    # Initialize database
    db = Database()
    
    while True:
        try:
            # Get input
            line = input("brandon'sRdbms $> ").strip()
            
            if not line:
                continue
            
            # Handle meta-commands
            if line.startswith('.'):
                cmd = line[1:].split()
                if cmd[0] == 'help':
                    print_help()
                elif cmd[0] == 'exit' or cmd[0] == 'quit':
                    print("Goodbye!")
                    break
                elif cmd[0] == 'tables':
                    # This would require implementing SHOW TABLES
                    print("Tables feature coming soon!")
                elif cmd[0] == 'schema' and len(cmd) > 1:
                    # This would require implementing DESCRIBE
                    print(f"Schema for {cmd[1]} coming soon!")
                else:
                    print(f"Unknown command: {line}")
                continue
            
            # Execute SQL
            try:
                result = db.execute(line)
                
                if result.rows is not None:
                    if result.rows:
                        # Print results as table
                        headers = list(result.rows[0].keys())
                        print_table(result.rows, headers)
                    print(f"({result.rowcount} row{'s' if result.rowcount != 1 else ''})")
                else:
                    print(f"Query OK, {result.rowcount} row{'s' if result.rowcount != 1 else ''} affected")
                    
            except Exception as e:
                print(f"Error: {e}")
                
        except KeyboardInterrupt:
            print("\nUse .exit to quit")
        except EOFError:
            print("\nGoodbye!")
            break
    
    db.close()

if __name__ == "__main__":
    main()