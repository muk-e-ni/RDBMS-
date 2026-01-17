// frontend/src/components/SchemaViewer.js
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './styles/SchemaViewerStyle.css';

const SchemaViewer = () => {
  const [schemas, setSchemas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchSchemas();
  }, []);

  const fetchSchemas = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.get('http://localhost:5000/api/schema/all');
      if (response.data.success) {
        setSchemas(response.data.schemas || []);
      } else {
        setError(response.data.error);
      }
    } catch (err) {
      setError(err.response?.data?.error || err.message);
    } finally {
      setLoading(false);
    }
  };

  const refreshSchemas = () => {
    fetchSchemas();
  };

  if (loading) {
    return <div className="schema-viewer loading">Loading schemas...</div>;
  }

  if (error) {
    return (
      <div className="schema-viewer error">
        <p>Error loading schemas: {error}</p>
        <button onClick={refreshSchemas}>Retry</button>
      </div>
    );
  }

  return (
    <div className="schema-viewer">
      <div className="schema-header">
        <h2>Database Schema Browser</h2>
        <button onClick={refreshSchemas} className="refresh-btn">
          Refresh
        </button>
      </div>

      {schemas.length === 0 ? (
        <div className="no-schemas">
          <p>No tables found in the database.</p>
          <p>Create a table using the SQL Console or Dashboard.</p>
        </div>
      ) : (
        <div className="schemas-list">
          {schemas.map((table, index) => (
            <div key={index} className="schema-card">
              <h3 className="table-name">{table.table}</h3>
              <div className="schema-details">
                <table>
                  <thead>
                    <tr>
                      <th>Column</th>
                      <th>Type</th>
                      <th>Constraints</th>
                    </tr>
                  </thead>
                  <tbody>
                    {table.schema.columns.map((column, colIndex) => (
                      <tr key={colIndex}>
                        <td className="column-name">{column.name}</td>
                        <td className="column-type">
                          {column.dtype}
                          {column.length && `(${column.length})`}
                        </td>
                        <td className="column-constraints">
                          {column.primary_key && <span className="constraint pk">PRIMARY KEY</span>}
                         
                          {column.unique && !column.primary_key && <span className="constraint unique">UNIQUE</span>}
                          {!column.nullable && <span className="constraint not-null">NOT NULL</span>}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="table-stats">
                <span>Columns: {table.schema.columns.length}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default SchemaViewer;