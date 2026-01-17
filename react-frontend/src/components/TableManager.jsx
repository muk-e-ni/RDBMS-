// frontend/src/components/TableManager.js
import React, { useState } from 'react';
import axios from 'axios';
import './styles/TableManagerStyle.css';


const TableManager = ({ tables, onTableClick, onRefresh, activeTable }) => {
  const [newTableName, setNewTableName] = useState('');
  const [newTableSchema, setNewTableSchema] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState(null);

  const handleCreateTable = async (e) => {
    e.preventDefault();
    if (!newTableName.trim() || !newTableSchema.trim()) {
      setError('Table name and schema are required');
      return;
    }

    setIsCreating(true);
    setError(null);

    try {
      const sql = `CREATE TABLE ${newTableName} (${newTableSchema})`;
      const response = await axios.post('http://localhost:5000/api/execute', { sql });
      
      if (response.data.success) {
        setNewTableName('');
        setNewTableSchema('');
        onRefresh();
        alert(`Table '${newTableName}' created successfully!`);
      } else {
        setError(response.data.error);
      }
    } catch (err) {
      setError(err.response?.data?.error || err.message);
    } finally {
      setIsCreating(false);
    }
  };

  const handleDropTable = async (tableName) => {
    if (!window.confirm(`Are you sure you want to drop table '${tableName}'?`)) {
      return;
    }

    try {
      const response = await axios.delete(`http://localhost:5000/api/tables/${tableName}`);
      if (response.data.success) {
        onRefresh();
        alert(`Table '${tableName}' dropped successfully!`);
      }
    } catch (err) {
      alert(`Error dropping table: ${err.response?.data?.error || err.message}`);
    }
  };

  const exampleSchemas = [
    "id INT PRIMARY KEY, name VARCHAR(50), email VARCHAR(100)",
    "id INT PRIMARY KEY, title VARCHAR(100), price DECIMAL(10,2), stock INT",
    "id INT PRIMARY KEY, first_name VARCHAR(50), last_name VARCHAR(50), age INT"
  ];

  return (
    <div className="table-manager">
      <div className="tables-list">
        <h3>Tables ({tables.length})</h3>
        <button onClick={onRefresh} className="refresh-btn">
          Refresh
        </button>
        
        <ul>
          {tables.map((table, index) => (
            <li 
              key={index} 
              className={table.name === activeTable ? 'active' : ''}
            >
              <button
                className="table-btn"
                onClick={() => onTableClick(table.name)}
              >
                {table.name}
                {table.row_count !== undefined && (
                  <span className="row-count"> ({table.row_count})</span>
                )}
              </button>
              <button
                className="drop-btn"
                onClick={() => handleDropTable(table.name)}
                title="Drop table"
              >
                ×
              </button>
            </li>
          ))}
          
          {tables.length === 0 && (
            <li className="empty">No tables found</li>
          )}
        </ul>
      </div>

      <div className="create-table">
        <h3>Create New Table</h3>
        <form onSubmit={handleCreateTable}>
          <div className="form-group">
            <label>Table Name:</label>
            <input
              type="text"
              value={newTableName}
              onChange={(e) => setNewTableName(e.target.value)}
              placeholder="e.g., users"
              disabled={isCreating}
            />
          </div>
          
          <div className="form-group">
            <label>Table Schema:</label>
            <textarea
              value={newTableSchema}
              onChange={(e) => setNewTableSchema(e.target.value)}
              placeholder="e.g., id INT PRIMARY KEY, name VARCHAR(50)"
              rows={4}
              disabled={isCreating}
            />
            <div className="schema-examples">
              <small>Examples:</small>
              {exampleSchemas.map((schema, index) => (
                <button
                  key={index}
                  type="button"
                  className="example-schema"
                  onClick={() => setNewTableSchema(schema)}
                >
                  {schema}
                </button>
              ))}
            </div>
          </div>

          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          <button 
            type="submit" 
            disabled={isCreating || !newTableName.trim() || !newTableSchema.trim()}
            className="create-btn"
          >
            {isCreating ? 'Creating...' : 'Create Table'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default TableManager;