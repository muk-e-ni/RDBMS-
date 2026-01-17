// frontend/src/components/DataTable.js
import React from 'react';
import './styles/DataTableStyle.css';

const DataTable = ({ data, columns, rowCount }) => {
  if (!data || data.length === 0) {
    return (
      <div className="data-table empty">
        <p>No data to display</p>
        {rowCount !== undefined && <p>Rows affected: {rowCount}</p>}
      </div>
    );
  }

  // If columns not provided, extract from first row
  const tableColumns = columns || Object.keys(data[0]);

  return (
    <div className="data-table">
      <div className="table-header">
        <h3>Query Results</h3>
        <span className="row-count">{data.length} row{data.length !== 1 ? 's' : ''}</span>
      </div>
      
      <div className="table-container">
        <table>
          <thead>
            <tr>
              {tableColumns.map((column, index) => (
                <th key={index}>{column}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.map((row, rowIndex) => (
              <tr key={rowIndex}>
                {tableColumns.map((column, colIndex) => (
                  <td key={colIndex}>
                    {row[column] !== null && row[column] !== undefined 
                      ? String(row[column])
                      : <span className="null-value">NULL</span>
                    }
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      
      {rowCount !== undefined && (
        <div className="table-footer">
          Total rows affected: {rowCount}
        </div>
      )}
    </div>
  );
};

export default DataTable;