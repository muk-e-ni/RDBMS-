from flask import Blueprint, jsonify, current_app
import os 

tables_bp = Blueprint('tables', __name__, url_prefix='/api/tables')

@tables_bp.route('/', methods = ['GET'])
def list_tables():
    data_dir = "web_data"
    tables = []

    if os.path.exists(data_dir):
        for file in os.listdir(data_dir):
            if file.endswith('.tbl'):
                table_name = file [:-4]
                tables.append({
                    'name': table_name,
                    'row_count': count_table_rows(table_name)

                })

    return jsonify({ 'tables':tables})

@tables_bp.route('/<t_name>', methods = ['GET'])
def get_table_data(t_name):
    db = current_app.config['DATABASE']

    try:
        result = db.execute(f"SELECT * FROM {t_name}")
        return jsonify({
            'success': True,
            'table': t_name,
            'data': result.rows,
            'columns': list(result.rows[0].keys()) if result.rows and len(result.rows) > 0 else [],
            'rowcount': result.rowcount

        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error' : str(e)
        }), 400
    
@tables_bp.route('/<t_name>', methods=['DELETE'])
def drop_table(t_name):
    db = current_app.config['DATABASE']

    try:
        result = db.execute(f"DROP TABLE {t_name}")
        return jsonify({
            'success': True,
            'message': f"Table '{t_name}' dropped successfully"
        })
    except Exception as e:
        return jsonify({ 'success': False, 'error': str(e)}), 400
    
def count_table_rows(t_name):
    table_file = f"web_data/{t_name}.tbl"

    if os.path.exists(table_file):
        with open(table_file, 'r') as f:

            return sum(1 for line in f if line.strip())
        return 0