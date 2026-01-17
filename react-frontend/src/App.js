import React, {useState, useEffect} from 'react';
import { BrowserRouter as Router, Routes, Route, Link} from 'react-router-dom';

import SQLConsole from './components/SQLConsole'
import DataTable from './components/DataTable';
import TableManager from './components/TableManager';
import SchemaViewer from './components/SchemaViewer';
import WebREPL from './components/WebREPL';
import JoinVisualizer from './components/JoinVisualizer';
import './AppStyle.css';


function App(){

    const[tables, setTables] = useState([]);
    const[activeTable, setActiveTable] =useState(null);
    const[queryResult, setQueryResult] = useState(null);

    const fetchTables = async () => {
        try{
            const response = await fetch('http://localhost:5000/api/tables/');
            const data = await response.json();
            setTables(data.tables || []);
        } catch (error){
            console.error('Error fetching tables:', error);
        }
    };

    useEffect(() => {
        fetchTables();

    }, []

    );

    const handleTableClick = async (tableName) => {
        setActiveTable(tableName);

        try{
            const response = await fetch(`http://localhost:500/api/tables/${tableName}`);
            const data = await response.json();

            if (data.success){
                setQueryResult({
                    rows:data.data,
                    columns: data.columns,
                    rowcount: data.rowcount
                });
            }
        } catch (error){
            console.error('Error fetching table data:', error);
        }
    };

    const handleQueryResult = (result) => {
        setQueryResult(result)
        fetchTables()
    };

    return (
        <Router>
            <div className='APP'>
                <header className='App-header'>
                    <h1> Brandon's RDBMS WEB INTERFACE </h1>

                    <nav>
                        <Link to = "/">Dashboard</Link> |
                        <Link to = "/repl"> Web  REPL</Link> |
                        <Link to = "/schema"> Schema Browser</Link> |
                        <Link to ="/visualizer"> Join visualizer</Link>
                    </nav>

                </header>

                <div className='container'>
                    <Routes>
                        <Route path='/' element={
                            <div className='dashboard'>
                                <div className='sidebar'>
                                    <TableManager

                                    tables = {tables}
                                    onTableClick = {handleTableClick}
                                    onRefresh={fetchTables}
                                    activeTable={activeTable}
                                    />

                                    </div> 
                                    
                                    <div className='main-content'>
                                        <SQLConsole onExecute = {handleQueryResult}/>

                                        {queryResult && (
                                            <DataTable 
                                            data = {queryResult.rows}
                                            columns = {queryResult.columns}
                                            rowcount = {queryResult.rowcount}
                                            />
                                        )}
                                        </div>
                                        </div>
                        }/>
                                    <Route path="/repl" element={<WebREPL />} />
                                    <Route path="/schema" element={<SchemaViewer />} />
                                    <Route path ="/visualizer" element={<JoinVisualizer />} />
                        </Routes>
                </div>
            </div>

        </Router>
    );


}

export default App;