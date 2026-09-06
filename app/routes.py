from flask import Blueprint, render_template, request, jsonify, current_app
from app.services.flowchart_service import FlowchartService


routes = Blueprint('routes', __name__)
flowchart_service = FlowchartService()


@routes.route('/')
def index():
    """Main page."""
    return render_template('index.html')


@routes.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and generate flowchart."""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Get file extension
        filename = file.filename.lower()
        ext = None
        for supported_ext in flowchart_service.get_supported_extensions():
            if filename.endswith(supported_ext):
                ext = supported_ext
                break
        
        if not ext:
            return jsonify({
                'error': f'Supported files: {", ".join(flowchart_service.get_supported_extensions())}'
            }), 400
        
        # Read file
        code = file.read().decode('utf-8')
        
        if len(code) > current_app.config['MAX_CONTENT_LENGTH']:
            return jsonify({'error': 'File too large'}), 400
        
        # Generate flowchart
        result = flowchart_service.generate(code, ext)
        
        if not result.get('success'):
            return jsonify({'error': result.get('error', 'Generation failed')}), 400
        
        return jsonify(result)
        
    except Exception as e:
        import traceback
        print(f"Error: {traceback.format_exc()}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500