import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './styles/JoinVisualizerStyle.css';

const JoinVisualizer = () => {
  const [tables, setTables] = useState([]);
  const [leftTable, setLeftTable] = useState('');
  const [rightTable, setRightTable] = useState('');
  const [leftColumns, setLeftColumns] = useState([]);
  const [rightColumns, setRightColumns] = useState([]);
  const [joinType, setJoinType] = useState('INNER');
  const [leftKey, setLeftKey] = useState('');
  const [rightKey, setRightKey] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchTables();
  }, []);

  const fetchTables = async () => {
    try {
      const response = await axios.get('http://localhost:5000/api/tables');
      setTables(response.data.tables || []);
    } catch (error) {
      console.error('Error fetching tables:', error);
    }
  };

  const fetchTableSchema = async (tableName) => {
    try {
      const response = await axios.get(`http://localhost:5000/api/schema/${tableName}`);
      return response.data.schema?.columns || [];
    } catch (error) {
      console.error(`Error fetching schema for ${tableName}:`, error);
      return [];
    }
  };

  const handleLeftTableChange = async (e) => {
    const table = e.target.value;
    setLeftTable(table);
    if (table) {
      const columns = await fetchTableSchema(table);
      setLeftColumns(columns);
      if (columns.length > 0) {
        setLeftKey(columns[0].name);
      }
    }
  };

  const handleRightTableChange = async (e) => {
    const table = e.target.value;
    setRightTable(table);
    if (table) {
      const columns = await fetchTableSchema(table);
      setRightColumns(columns);
      if (columns.length > 0) {
        setRightKey(columns[0].name);
      }
    }
  };

  const executeJoin = async () => {
    if (!leftTable || !rightTable || !leftKey || !rightKey) {
      alert('Please select tables and join keys');
      return;
    }

    const sql = `SELECT * FROM ${leftTable} ${joinType} JOIN ${rightTable} ON ${leftTable}.${leftKey} = ${rightTable}.${rightKey}`;
    
    setLoading(true);
    try {
      const response = await axios.post('http://localhost:5000/api/execute', { sql });
      if (response.data.success) {
        setResult(response.data);
      } else {
        alert(`Error: ${response.data.error}`);
      }
    } catch (error) {
      alert(`Error: ${error.response?.data?.error || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="join-visualizer">
      <h2>JOIN Visualizer</h2>
      <p className="description">
        Visualize how different JOIN types work by selecting tables and keys.
      </p>

      <div className="join-config">
        <div className="table-selection">
          <div className="table-select">
            <label>Left Table:</label>
            <select value={leftTable} onChange={handleLeftTableChange}>
              <option value="">Select table</option>
              {tables.map(table => (
                <option key={table.name} value={table.name}>{table.name}</option>
              ))}
            </select>
          </div>

          <div className="join-type-select">
            <label>JOIN Type:</label>
            <select value={joinType} onChange={(e) => setJoinType(e.target.value)}>
              <option value="INNER">INNER JOIN</option>
              <option value="LEFT">LEFT JOIN</option>
              <option value="RIGHT">RIGHT JOIN</option>
            </select>
          </div>

          <div className="table-select">
            <label>Right Table:</label>
            <select value={rightTable} onChange={handleRightTableChange}>
              <option value="">Select table</option>
              {tables.map(table => (
                <option key={table.name} value={table.name}>{table.name}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="key-selection">
          <div className="key-select">
            <label>Left Table Key:</label>
            <select value={leftKey} onChange={(e) => setLeftKey(e.target.value)} disabled={!leftTable}>
              <option value="">Select column</option>
              {leftColumns.map(col => (
                <option key={col.name} value={col.name}>{col.name} ({col.dtype})</option>
              ))}
            </select>
          </div>

          <div className="join-symbol">
            <span>ON</span>
          </div>

          <div className="key-select">
            <label>Right Table Key:</label>
            <select value={rightKey} onChange={(e) => setRightKey(e.target.value)} disabled={!rightTable}>
              <option value="">Select column</option>
              {rightColumns.map(col => (
                <option key={col.name} value={col.name}>{col.name} ({col.dtype})</option>
              ))}
            </select>
          </div>
        </div>

        <div className="visualization">
          <div className="table-vis left-table">
            <h4>{leftTable || 'Left Table'}</h4>
            {leftColumns.length > 0 && (
              <div className="columns">
                {leftColumns.map(col => (
                  <div 
                    key={col.name} 
                    className={`column ${col.name === leftKey ? 'selected' : ''}`}
                    onClick={() => setLeftKey(col.name)}
                  >
                    {col.name}
                    {col.primary_key && <span className="pk">PK</span>}
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="join-vis">
            <div className="join-type">{joinType} JOIN</div>
            <div className="join-arrow">→</div>
          </div>

          <div className="table-vis right-table">
            <h4>{rightTable || 'Right Table'}</h4>
            {rightColumns.length > 0 && (
              <div className="columns">
                {rightColumns.map(col => (
                  <div 
                    key={col.name} 
                    className={`column ${col.name === rightKey ? 'selected' : ''}`}
                    onClick={() => setRightKey(col.name)}
                  >
                    {col.name}
                    {col.primary_key && <span className="pk">PK</span>}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <button 
          className="execute-btn"
          onClick={executeJoin}
          disabled={loading || !leftTable || !rightTable || !leftKey || !rightKey}
        >
          {loading ? 'Executing...' : 'Execute JOIN'}
        </button>
      </div>

      {result && (
        <div className="join-result">
          <h3>JOIN Result ({result.rowcount} rows)</h3>
          <div className="sql-preview">
            <code>
              SELECT * FROM {leftTable} {joinType} JOIN {rightTable} ON {leftTable}.{leftKey} = {rightTable}.{rightKey}
            </code>
          </div>
          
          {result.data && result.data.length > 0 ? (
            <div className="result-table">
              <table>
                <thead>
                  <tr>
                    {Object.keys(result.data[0]).map(col => (
                      <th key={col}>{col}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {result.data.slice(0, 10).map((row, idx) => (
                    <tr key={idx}>
                      {Object.values(row).map((val, colIdx) => (
                        <td key={colIdx}>{val !== null ? String(val) : <em>NULL</em>}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
              {result.data.length > 10 && (
                <p className="result-summary">
                  Showing 10 of {result.data.length} rows
                </p>
              )}
            </div>
          ) : (
            <p className="no-data">No rows returned from JOIN</p>
          )}
        </div>
      )}

      <div className="join-explanations">
        <h3>JOIN Types Explained</h3>
        <div className="explanation-cards">
          <div className="explanation-card">
            <h4>INNER JOIN</h4>
            <p>Returns only rows where there's a match in both tables.</p>
            <div className="venn">
              <div className="circle left">A</div>
              <div className="circle right">B</div>
              <div className="intersection">A ∩ B</div>
            </div>
          </div>
          
          <div className="explanation-card">
            <h4>LEFT JOIN</h4>
            <p>Returns all rows from left table, matched rows from right table (NULL if no match).</p>
            <div className="venn">
              <div className="circle left full">A</div>
              <div className="circle right">B</div>
            </div>
          </div>
          
          <div className="explanation-card">
            <h4>RIGHT JOIN</h4>
            <p>Returns all rows from right table, matched rows from left table (NULL if no match).</p>
            <div className="venn">
              <div className="circle left">A</div>
              <div className="circle right full">B</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default JoinVisualizer;