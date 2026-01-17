// frontend/src/components/WebREPL.js
import React, { useState, useEffect, useRef } from 'react';
import { io } from 'socket.io-client';
import './styles/WebREPLStyle.css';

const WebREPL = () => {
  const [input, setInput] = useState('');
  const [output, setOutput] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const socketRef = useRef(null);
  const outputEndRef = useRef(null);

  useEffect(() => {
    // Connect to WebSocket
    socketRef.current = io('http://localhost:5000');

    socketRef.current.on('connect', () => {
      setIsConnected(true);
      addOutput("Connected to Brandon's RDBMS WebSocket REPL", 'system');
    });

    socketRef.current.on('disconnect', () => {
      setIsConnected(false);
      addOutput('Disconnected from server', 'system');
    });

    socketRef.current.on('sql_result', (data) => {
      if (data.success) {
        if (data.data) {
          // Display table data
          addOutput(`Query successful (${data.rowcount} rows):`, 'success');
          if (data.data.length > 0) {
            const headers = Object.keys(data.data[0]);
            const tableOutput = [headers.join(' | ')];
            tableOutput.push('-'.repeat(tableOutput[0].length));
            data.data.forEach(row => {
              tableOutput.push(headers.map(h => row[h] || 'NULL').join(' | '));
            });
            addOutput(tableOutput.join('\n'), 'data');
          } else {
            addOutput('(no rows)', 'info');
          }
        } else {
          addOutput(`Command executed successfully. Rows affected: ${data.rowcount}`, 'success');
        }
      } else {
        addOutput(`Error: ${data.error}`, 'error');
      }
    });

    return () => {
      if (socketRef.current) {
        socketRef.current.disconnect();
      }
    };
  }, []);

  const addOutput = (text, type = 'normal') => {
    setOutput(prev => [...prev, { text, type, timestamp: new Date().toLocaleTimeString() }]);
    setTimeout(() => {
      outputEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, 100);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim() || !isConnected) return;

    addOutput(`> ${input}`, 'input');
    socketRef.current.emit('execute_sql', { sql: input });
    setInput('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && e.ctrlKey) {
      handleSubmit(e);
    }
  };

  const clearOutput = () => {
    setOutput([]);
  };

  const exampleCommands = [
    "CREATE TABLE students (id INT PRIMARY KEY, name VARCHAR(50), grade VARCHAR(2))",
    "INSERT INTO students VALUES (1, 'Alice', 'A')",
    "INSERT INTO students VALUES (2, 'Bob', 'B')",
    "SELECT * FROM students",
    "SELECT name FROM students WHERE grade = 'A'",
    "DROP TABLE students"
  ];

  return (
    <div className="web-repl">
      <div className="repl-header">
        <h2>Web REPL</h2>
        <div className="connection-status">
          Status: 
          <span className={isConnected ? 'connected' : 'disconnected'}>
            {isConnected ? ' Connected' : ' Disconnected'}
          </span>
        </div>
      </div>

      <div className="output-container">
        <div className="output-toolbar">
          <button onClick={clearOutput}>Clear Output</button>
        </div>
        <div className="output">
          {output.map((item, index) => (
            <div key={index} className={`output-line ${item.type}`}>
              <span className="timestamp">[{item.timestamp}]</span>
              <pre>{item.text}</pre>
            </div>
          ))}
          <div ref={outputEndRef} />
        </div>
      </div>

      <form onSubmit={handleSubmit} className="input-form">
        <div className="input-group">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Enter SQL command (Ctrl+Enter to execute)"
            rows={3}
            disabled={!isConnected}
          />
          <button type="submit" disabled={!isConnected || !input.trim()}>
            Execute
          </button>
        </div>
        <div className="input-hint">
          <small>Press Ctrl+Enter to execute</small>
        </div>
      </form>

      <div className="examples">
        <h4>Example Commands:</h4>
        <div className="example-buttons">
          {exampleCommands.map((cmd, index) => (
            <button
              key={index}
              type="button"
              className="example-btn"
              onClick={() => setInput(cmd)}
            >
              {cmd.split(' ')[0]}...
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default WebREPL;