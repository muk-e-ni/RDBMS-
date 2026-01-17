from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from rdbms.core.database import Database
 
def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = '123'

    CORS(app, resources={r"/api/*":{"origins": "http://localhost:3000"}})

    socketio = SocketIO(app, cors_allowed_origins = "*", async_mode = 'gevent')

    db = Database("web_data")

    from .routes.query import query_bp
    from .routes.tables import tables_bp
    from .routes.schema import schema_bp


    app.register_blueprint(query_bp)
    app.register_blueprint(tables_bp)
    app.register_blueprint(schema_bp)

    app.config['DATABASE'] = db
    app.config['SOCKETIO'] = socketio

    @socketio.on('connect')
    def handle_connect():
        print("client connected")

    @socketio.on('disconnect')
    def handle_disconnect():
        print('client disconnected')

    @socketio.on('execute_sql')
    def handle_sql_command(data):
        
        sql = data.get('sql', '').strip()
        if not sql:
            socketio.emit('sql_result', {'error': 'No SQL Provided'})
            return
        try:
            result = db.execute(sql)
            response = {
                'success': True,
                'data': result.rows if hasattr(result, 'rows') and result.rows is not None else None,
                'rowcount': result.rowcount,
                'message': f'Executed Successfully'

            }
            socketio.emit('sql_result', response)
        except Exception as e:
            socketio.emit('sql_result', {
                'success': False,
                'error': str(e)
            })
    return app, socketio
app, socketio = create_app()

if __name__ == '__main__':
        print("Brandon's RDBMS API Server Starting...")
        print("API available at: http://localhost:5000")
        print("Websocket REPL available at: ws://localhost:5000")
        socketio.run(app, debug=True, port=5000)
