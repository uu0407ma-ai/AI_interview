from flask import Flask, jsonify, request, send_file
import sqlite3
from io import BytesIO
from flask_cors import CORS
import time
import string
import secrets
from datetime import datetime
import whisper
import io
import tempfile
import torch
import os
import subprocess


# 检查数据库文件是否存在
if not os.path.exists('interview_system.db'):
    # 调用数据库初始化脚本 ，直接调用 create_interview_system_db.py 脚本
    print("数据库文件不存在，正在初始化数据库...")
    import create_interview_system_db   
    print("数据库初始化完成")
    

print("torch 版本：", torch.__version__)


# https://huggingface.co/openai/whisper-large-v3
# 加载 large-v3 模型 ， 确保 GPU 可用
if torch.cuda.is_available():
    whisperModel = whisper.load_model("large-v3").to("cuda")  # 显式移动到 GPU
    print("GPU 可用，使用 large-v3 模型")
else:
    whisperModel = whisper.load_model("base")
    print("GPU 不可用，使用 base 模型")

# tiny：最小的模型，适合资源受限的设备，速度快但精度较低。
# base：基础模型，平衡了速度和精度，适合一般用途。
# small：中等规模模型，精度高于 base，适合需要更好性能的场景。
# medium：中大型模型，精度进一步提高，适合高质量转录。
# large：最大模型，精度最高，适合专业级应用，但需要更多计算资源。

app = Flask(__name__, static_folder='static', static_url_path='/static')

CORS(app)

# 生成随机令牌
def generate_token(length=32):
    alphabet = string.ascii_letters + string.digits
    token = ''.join(secrets.choice(alphabet) for _ in range(length))
    return token

def get_db():
    conn = sqlite3.connect('interview_system.db')
    conn.row_factory = sqlite3.Row
    return conn

# 岗位管理
@app.route('/api/positions', methods=['GET'])
def get_positions():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM positions')
    positions = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(positions)

@app.route('/api/positions', methods=['POST'])
def create_position():
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO positions (name, requirements, responsibilities, quantity, status, created_at, recruiter)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (data['name'], data['requirements'], data['responsibilities'], data['quantity'], data['status'], int(time.time()), data['recruiter']))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

@app.route('/api/positions/<int:id>', methods=['PUT'])
def update_position(id):
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE positions SET name=?, requirements=?, responsibilities=?, quantity=?, status=?, recruiter=?
        WHERE id=?
    ''', (data['name'], data['requirements'], data['responsibilities'], data['quantity'], data['status'], data['recruiter'], id))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

@app.route('/api/positions/<int:id>', methods=['DELETE'])
def delete_position(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM positions WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

# 候选人管理
@app.route('/api/candidates', methods=['GET'])
def get_candidates():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id,position_id, name, email  FROM candidates')
    candidates = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(candidates)

@app.route('/api/candidates', methods=['POST'])
def create_candidate():
    data = request.form
    
    resume_content = request.files['resume_content'].read() if 'resume_content' in request.files else None
    resume_binary = sqlite3.Binary(resume_content) if resume_content is not None else None
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO candidates (position_id, name, email, resume_content)
        VALUES (?, ?, ?, ?)
    ''', (data['position_id'], data['name'], data['email'],  resume_binary))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

@app.route('/api/candidates/<int:id>/resume', methods=['GET'])
def download_resume(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT resume_content FROM candidates WHERE id=?', (id,))
    resume = cursor.fetchone()
    conn.close()
    if resume and resume['resume_content']:
        return send_file(BytesIO(resume['resume_content']), download_name=f'resume_{id}.pdf', as_attachment=True)
    return jsonify({'error': '简历不存在'}), 404

# 删除候选人
@app.route('/api/candidates/<int:id>', methods=['DELETE'])
def delete_candidate(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM candidates WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})


# 面试管理
@app.route('/api/interviews', methods=['GET'])
def get_interviews():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, candidate_id, interviewer, start_time, status, is_passed, token FROM interviews')
    interviews = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(interviews)

@app.route('/api/interviews', methods=['POST'])
def create_interview():
    data = request.json
    data['token'] = generate_token()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO interviews (candidate_id, interviewer, start_time, status, is_passed , token)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (data['candidate_id'], data['interviewer'], data['start_time'], data['status'], data['is_passed'], data['token'] ))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

@app.route('/api/interviews/<int:id>', methods=['PUT'])
def update_interview(id):
    data = request.json
    data['token'] = generate_token()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE interviews SET candidate_id=?, interviewer=?, start_time=?, status=?, is_passed=? ,token=?
        WHERE id=?
    ''', (data['candidate_id'], data['interviewer'], data['start_time'], data['status'], data['is_passed'], data['token'], id))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

# API: 下载面试报告
@app.route('/api/interviews/<int:interview_id>/report', methods=['GET'])
def download_interview_report(interview_id):
    conn = get_db()
    
    # 获取面试信息及报告内容
    interview = conn.execute('''SELECT id, candidate_id, report_content FROM interviews WHERE id = ? ''', (interview_id, )).fetchone()
    
    conn.close()
    
    if not interview:
        return jsonify({"error": "面试不存在"}), 404
    
    if not interview['report_content']:
        return jsonify({"error": "面试报告尚未生成"}), 404
    
    # 将BLOB转换为字节流
    report_data = io.BytesIO(interview['report_content'])
    
    # 生成文件名
    file_name = f"面试报告_{interview['id']}.pdf"
    
    # 发送文件
    return send_file(
        report_data,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=file_name
    )

# API: 删除面试
@app.route('/api/interviews/<int:id>', methods=['DELETE'])
def delete_interview(id):
    conn = get_db()
    cursor = conn.cursor()
    
    # 先删除相关的面试问题
    cursor.execute('DELETE FROM interview_questions WHERE interview_id = ?', (id,))
    
    # 然后删除面试记录
    cursor.execute('DELETE FROM interviews WHERE id = ?', (id,))
    
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

# API: 获取面试信息
@app.route('/api/interview/<token>/info', methods=['GET'])
def get_interview_info(token):
    conn = get_db()
    
    # 获取面试及相关信息
    interview_info = conn.execute('''
        SELECT i.id, i.question_count, i.voice_reading, i.start_time, i.status,
               c.name as candidate_name, c.email as candidate_email,
               p.name as position_name, p.requirements
        FROM interviews i
        JOIN candidates c ON i.candidate_id = c.id
        JOIN positions p ON c.position_id = p.id
        WHERE i.token = ?
    ''', (token,)).fetchone()
    
    conn.close()
    
    if not interview_info:
        return jsonify({"error": "面试不存在"}), 404
    
    # 转换为字典
    result = dict(interview_info)
    
    # 格式化时间
    if result['start_time']:
        result['time'] = datetime.fromtimestamp(result['start_time']).strftime('%Y年%m月%d日 %H:%M')
    else:
        result['time'] = "未设置时间"
    
    # 构造返回数据
    return jsonify({
        "interview_id": result['id'],
        "time": result['time'],
        "position": result['position_name'],
        "candidate": result['candidate_name'],
        "status": result['status'],
        "question_count": result['question_count'],
        "voice_reading": result['voice_reading']
    })

# API: 获取下一个问题
@app.route('/api/interview/<token>/get_question', methods=['GET'])
def get_next_question(token):
    current_question_id = request.args.get('current_id', type=int, default=0)
    
    conn = get_db()
    
    # 先获取面试ID
    interview = conn.execute('SELECT id FROM interviews WHERE token = ?', (token,)).fetchone()
    
    if not interview:
        conn.close()
        return jsonify({"id": 0, "text": "面试无效"}), 404
    
    # 获取下一个问题
    next_question = None
    if current_question_id == 0:
        # 获取第一个问题
        next_question = conn.execute('''
            SELECT id, question as text
            FROM interview_questions
            WHERE interview_id = ?
            ORDER BY id ASC
            LIMIT 1
        ''', (interview['id'],)).fetchone()
    else:
        # 获取下一个问题
        next_question = conn.execute('''
            SELECT id, question as text
            FROM interview_questions
            WHERE interview_id = ? AND id > ?
            ORDER BY id ASC
            LIMIT 1
        ''', (interview['id'], current_question_id)).fetchone()
    
    conn.close()
    
    # 如果没有下一个问题，返回结束标志
    if not next_question:
        return jsonify({"id": 0, "text": "面试已完成"})
    
    return jsonify(dict(next_question))

# API: 提交答案
@app.route('/api/interview/<token>/submit_answer', methods=['POST'])
def submit_answer(token):
    conn = get_db()
    # 验证令牌
    interview = conn.execute('SELECT id FROM interviews WHERE token = ?', (token,)).fetchone()
    
    if not interview:
        conn.close()
        return jsonify({"error": "面试不存在"}), 404
    
    # 获取问题ID和音频答案
    question_id = request.form.get('question_id')
    audio_answer = request.files.get('audio_answer')
    
    if not question_id or not audio_answer:
        conn.close()
        return jsonify({"error": "缺少必要参数"}), 400
    
    audio_data = audio_answer.read()
    # 从 webm 音频文件 提取 中文文本
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
        temp_file.write(audio_data)
        temp_file_path = temp_file.name

    # 使用 transcribe 处理临时文件，此处获得的text是繁体中文，但是不影响后续功能
    result = whisperModel.transcribe(temp_file_path, language="zh")
    audio_text = result["text"]

    answered_time = int(time.time())
    
    conn.execute('''
        UPDATE interview_questions
        SET answer_audio = ?, answer_text = ?, answered_at = ?
        WHERE id = ? AND interview_id = ?
    ''', (audio_data, audio_text, answered_time, question_id, interview['id']))
    
    # 获取下一个问题
    next_question = conn.execute('''
        SELECT id, question as text
        FROM interview_questions
        WHERE interview_id = ? AND id > ?
        ORDER BY id ASC
        LIMIT 1
    ''', (interview['id'], question_id)).fetchone()
    
    conn.commit()
    
    # 如果没有下一个问题，检查是否所有问题都已回答
    if not next_question:
        # 检查是否所有问题都已回答
        all_answered = conn.execute('''
            SELECT COUNT(*) as total, SUM(CASE WHEN answered_at IS NOT NULL THEN 1 ELSE 0 END) as answered
            FROM interview_questions
            WHERE interview_id = ?
        ''', (interview['id'],)).fetchone()
        
        # 如果所有问题都已回答，将面试状态更新为"已完成"
        if all_answered['total'] == all_answered['answered']:
            conn.execute('UPDATE interviews SET status = 3 WHERE id = ?', (interview['id'],))
            conn.commit()
        
        result = {
            "status": "success",
            "message": "答案已提交",
            "next_question": {"id": 0, "text": "面试已完成"}
        }
    else:
        result = {
            "status": "success",
            "message": "答案已提交",
            "next_question": dict(next_question)
        }
    
    conn.close()
    return jsonify(result)

# New API endpoint to toggle voice reading
@app.route('/api/interview/<token>/toggle_voice_reading', methods=['POST'])
def toggle_voice_reading(token):
    data = request.json
    enabled = data.get('enabled', False)
    
    conn = get_db()
    # Update voice reading setting
    conn.execute('UPDATE interviews SET voice_reading = ? WHERE token = ?', 
                (1 if enabled else 0, token))
    conn.commit()
    conn.close()
    
    return jsonify({'status': 'success', 'voice_reading': enabled})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)