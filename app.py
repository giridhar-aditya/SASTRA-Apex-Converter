from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys
import torch
import sastra
from SASTRA_Code_Converter_DL import get_config, get_model, Validate

app = Flask(__name__)
CORS(app)

@app.route('/', methods=['GET'])
def home():
    return "Backend is running!"

@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({'status': 'ok'})


@app.route('/convert', methods=['POST'])
def convert_rule_based():
    data = request.get_json()
    cpp_code = data.get('code')
    output_folder = data.get('output_folder')

    try:
        input_path = os.path.join(output_folder, 'input.cpp')
        with open(input_path, 'w', encoding='utf-8') as f:
            f.write(cpp_code)

        intermediate_path = os.path.join(output_folder, 'output.txt')
        output_path = os.path.join(output_folder, 'output_sastra.rs')
        sastra.preprocess(input_path, intermediate_path)
        sastra.convert(intermediate_path, output_path)

        return jsonify({'message': 'Rule-based conversion complete!'})
    except Exception as e:
        print(f"[ERROR] Rule-based conversion failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/convert_ai', methods=['POST'])
def convert_ai():
    data = request.get_json()
    cpp_code = data.get('code')
    output_folder = data.get('output_folder')

    try:
        config = get_config()
        model = get_model(config)
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(__file__)

        model_path = os.path.join(base_path, 'Training_1_24.pth')
        checkpoint = torch.load(model_path, map_location=torch.device('cpu'))
        model.load_state_dict(checkpoint['model_state_dict'])
        model.eval()

        rust_code = Validate(model, cpp_code, validate=False)
        output_path = os.path.join(output_folder, 'output_ai.rs')
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(rust_code)

        return jsonify({'message': 'AI conversion complete!'})
    except Exception as e:
        print(f"[ERROR] AI conversion failed: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print('>>> Flask backend starting on http://127.0.0.1:5000')
    app.run(host='127.0.0.1', port=5000)
