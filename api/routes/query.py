from flask import Blueprint, request, jsonify, current_app
import json

query_bp = Blueprint('query', __name__, url_prefix='/api')

@query_bp.route('/execute', methods=['POST'])
def execute_query():
    db = current_app.config['DATABASE']

    try:
        data = request.get_json()
        if not data or 'sql' not in data:
            return jsonify({ 
                'success': False,
                'error': 'No Sql Provided'
            }), 400
        
        sql = data['sql'].strip()
        result = db.execute(sql)

        response = {
            'success': True,
            'data': result.rows if hasattr(result, 'rows') and result.rows is not None else None,
            'rowcount': result.rowcount,
            'columns': list(result.rows[0].keys()) if result.rows and len(result.rows) > 0 else []

        }
        return jsonify(response)
    
    except Exception as e: 
        return jsonify({'success': False,
                        'error': str(e)}), 400
    
@query_bp.route('/batch', methods=['POST'])
def execute_batch():
    db = current_app.cont['DATABASE']

    try:
        data = request.get_json()

        if not data or 'queries' not in data:
            return jsonify({ 
                'success':False,
                'error': 'No queries provided'
            }), 400
        
        queries = data['queries']
        results = []

        for sql in queries:
            try:
                result = db.execute(sql.strip())
                results.append({
                    'sql': sql,
                    'success': True,
                    'rowcount': result.rowcount
                })

            except Exception as e:
                results.append({
                    'sql' : sql,
                    'success': False,
                    'error' : str(e)
                })

        return jsonify({
            'success': True,
            'results': results
        })
    
    except Exception as e:
        return jsonify({ 
            'success': False,
            'error': str(e)
        }), 400
