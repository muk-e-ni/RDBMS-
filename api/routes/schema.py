from flask import Blueprint, jsonify, current_app
import json
import os

schema_bp = Blueprint('schema', __name__, url_prefix='/api/schema')

@schema_bp.route('/<t_name>', methods=['GET'])
def get_table_schema(t_name):
    schema_file = f"web_data/{t_name}.schema"

    if not os.path.exists(schema_file):
        return jsonify({
            'success': False,
            'error': f" Table '{t_name}' not found" 
        }), 400
    
    try:
        with open(schema_file, 'r') as f:
            schema_data = json.load(f)

            return jsonify({
                'success': True,
                'table': t_name,
                'schema': schema_data
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    

@schema_bp.route('/all', methods = ['GET'])
def get_all_schema():
    data_dr = "web_data"
    schemas = []

    if os.path.exists(data_dr):
        for file in os.listdir(data_dr):
            if file.endswith('.schema'):
                t_name = file[:-7]

                try:
                    with open(os.path.join(data_dr, file), 'r') as f:
                        schema_data = json.load(f)

                    schemas.append({
                        'table': t_name,
                        'schema': schema_data
                    })
                except:
                    continue
    return jsonify({
        'success': True,
          'schemas':schemas
    })