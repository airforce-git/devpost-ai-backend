from flask import Flask, request, jsonify
import os
import requests
import logging
from dotenv import load_dotenv

load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# 添加 CORS 支持
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

# 处理 OPTIONS 请求
@app.route('/generate', methods=['OPTIONS'])
def handle_options():
    return '', 200

@app.route('/healthz')
def healthz():
    return jsonify({"status": "ok", "model": "deepseek-coder"})

@app.route('/generate', methods=['POST'])
def generate_blog():
    data = request.get_json()
    if not data or 'topic' not in data:
        return jsonify({"error": "Missing 'topic' in request body"}), 400
    
    topic = data['topic']
    
    prompt = f"请生成一篇关于 '{topic}' 的结构化技术博客，包含以下部分：\n1. 标题\n2. 代码示例（如果适用）\n3. 常见陷阱\n4. 总结\n\n最后请加上：\n本文由 CodeDraft 生成，请人工校对。"
    
    try:
        deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        if not deepseek_api_key:
            return jsonify({"error": "DEEPSEEK_API_KEY is not set in environment"}), 500
            
        response = requests.post(
            "https://api.deepseek.com/chat/completions",
            headers={
                "Authorization": f"Bearer {deepseek_api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-coder",
                "messages": [
                    {"role": "system", "content": "你是一位专业的技术博客作者。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 2000
            },
            timeout=60  # 增加超时设置
        )
        
        response.raise_for_status()
        result = response.json()
        content = result['choices'][0]['message']['content']
        
        return jsonify({"content": content})
    except requests.exceptions.Timeout:
        return jsonify({"error": "模型响应超时，请稍后再试"}), 504
    except requests.exceptions.RequestException as e:
        logging.error(f"DeepSeek API error: {e}")
        return jsonify({"error": "模型服务暂时不可用"}), 502
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return jsonify({"error": "内部服务错误"}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5001))
    app.run(host='0.0.0.0', port=port, debug=False)
