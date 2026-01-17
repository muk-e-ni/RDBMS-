import React, { useState } from 'react';
import axios from 'axios';

import './styles/SQLConsoleStyle.css'

const SQLConsole = ( { onExecute }) => {
    const [sql, setsql] = useState('');
    const [ isLoading, setIsLoading ] = useState(false);
    const[ history, setHistory ] = useState('');
    const [ error, setError ] = useState(null);

    const executeSQL = async (sqlText) => {
        setIsLoading(true)
        setError(null);

        try{
            const response = await axios.post('http://localhost:5000/api/execute', {
                sql: sqlText
            });

            if ( response.data.success ){
                onExecute({
                    rows: response.data.data || [],
                    columns: response.data.columns || [],
                    rowcount: response.data.rowcount || 0
                });

                if (!history.includes(sqlText)){
                    setHistory([sqlText, ...history.slice(0,9)]);
                }
            }else{
                setError(response.data.error);
            }
        } catch (err){
            setError(err.response?.data?.error || err.message);
        } finally{
            setIsLoading(false);
        }
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        if (sql.trim()){
            executeSQL(sql);
            setsql('');
        }
    };
    const handleHistoryClick = (query) => {
        setsql(query);
    };

    const exampleQueries = [
        "CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(50), email Varchar(100))",
        "INSERT INTO users VALUES (1, 'Alice', 'alice@example.com')",

        "SELECT * FROM users",
        "SELECT * FROM users WHERE id = 1",
        "UPDATE users SET name = 'Bob' WHERE id = 1",
        "DROP TABLE users",
        "SELECT users.name, orders.product, orders.amount FROM users INNER JOIN orders ON users.id = orders.user_id",
        "SELECT users.name, orders.product FROM users LEFT JOIN orders ON users.id = orders.user_id",
        "SELECT * FROM users WHERE name LIKE 'A%'"

    ];

    return(
        <div className='sql-console'>
            <h3>SQL Console</h3>

            <form onSubmit={handleSubmit}> 
                <textarea
                    value={sql}
                    onChange={(e) => setsql(e.target.value)}
                    placeholder='Enter SQL Query (e.g., SELECT * FROM "table_name")'
                    rows={6}
                    disabled={isLoading}
                    />

                    <div className='button-group'>
                        <button type='submit' disabled={isLoading || !sql.trim()}>
                            {isLoading ? "Executing..." : "Execute"}
                        </button>

                        <button type='button' onClick={()=> setsql('')} disabled={isLoading}>
                            Clear
                        </button>
                    </div>

            </form>
            {error && (
                <div className="error-message">
                    <strong>Error:</strong> {error}
                    </div>

            )}

            <div className='examples'>
                <h4>Example Queries:</h4>
                <div className='example-buttons'>
                    {exampleQueries.map((query, index) => (
                        <button
                        key={index}
                        type='button'
                        className='example-btn'
                        onClick={() => setsql(query)}
                        disabled={isLoading}
                        >
                            {query.split(' ')[0]}...

                        </button>
                    ))}

                </div>
            </div>
            {history.length > 0 && (
                <div className='history'>
                    <h4>Recent Queries:</h4>
                    <ul>
                        {history.map((query, index) => (
                            <li key={index}>
                                <button
                                type='button'
                                className='history-item'
                                onClick={() => handleHistoryClick(query)}>

                                    {query.length > 60 ? query.substring(0, 60) + '...' : query }


                                </button>

                            </li>
                        ))}
                    </ul>

                </div>
            )}

        </div>
    );

};

export default SQLConsole