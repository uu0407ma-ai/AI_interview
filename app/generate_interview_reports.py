import sqlite3
import time
import schedule
from jinja2 import Environment
from weasyprint import HTML
import json
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
import os



# 加载环境变量
load_dotenv()

# 初始化OpenAI客户端
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL")
)
   

def fetch_interviews_with_status_3():
    """Fetch all interviews with status = 3 (interview completed)"""
    conn = sqlite3.connect('interview_system.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT * FROM interviews WHERE status = 3
    ''')
    
    interviews = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return interviews

def fetch_candidate_info(candidate_id):
    """Fetch candidate information by candidate_id"""
    conn = sqlite3.connect('interview_system.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT * FROM candidates WHERE id = ?
    ''', (candidate_id,))
    
    row = cursor.fetchone()
    candidate = dict(row) if row else None
    conn.close()
    return candidate

def fetch_position_info(position_id):
    """Fetch position information by position_id"""
    conn = sqlite3.connect('interview_system.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT * FROM positions WHERE id = ?
    ''', (position_id,))
    
    row = cursor.fetchone()
    position = dict(row) if row else None
    conn.close()
    return position

def fetch_interview_questions(interview_id):
    """Fetch all questions and answers for a specific interview"""
    conn = sqlite3.connect('interview_system.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT * FROM interview_questions WHERE interview_id = ?
    ''', (interview_id,))
    
    questions = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return questions

def call_ai_model(candidate_name, position_name, interviewer, questions):
        """
        调用OpenAI API生成面试报告
        
        Args:
            candidate_name: 候选人姓名
            position_name: 职位名称
            interviewer: 面试官姓名
            questions: 面试问题列表，包含问题内容、评分标准和回答
            
        Returns:
            JSON格式的面试评估结果
        """
        # 构建发送给OpenAI的提示内容
        prompt = f"""
        你是一位专业的面试评估专家，需要对候选人"{candidate_name}"应聘"{position_name}"职位的面试表现进行评估。
        面试官是{interviewer}。
        
        请根据以下面试问题、评分标准和候选人的回答，对每个问题进行评分和点评，并给出综合评价
        注意每个问题评分范围是0-100分，综合评分范围是0-100分
        
        """
        
        # 添加每个问题的详细信息
        for i, q in enumerate(questions, 1):
            prompt += f"""
        问题{i}: {q.get('question', '未提供问题')}
        评分标准: {q.get('score_standard', '未提供评分标准')}
        候选人回答: {q.get('answer_text', '未提供回答')}
        
        """
        
        prompt += """
        请以JSON格式返回评估结果，包含以下内容：
        1. 每个问题的评分和评价
        2. 技术能力总分(满分100)
        3. 沟通能力总分(满分100)
        4. 综合评分(满分100)
        5. 面试官评语(综合评价候选人的优缺点)
        6. 录用建议(推荐录用/可以考虑/不建议录用)
        
        JSON格式示例:
        {
            "question_evaluations": [
                {"id": 1, "question": "[question]", "score_standard": "[score_standard]", "answer": "[answer_text]", "score": 7, "comments": "回答详细，展示了扎实的基础知识..."},
                {"id": 2, "question": "[question]", "score_standard": "[score_standard]", "answer": "[answer_text]", "score": 9, "comments": "思路清晰，解决方案合理..."}
                ...
            ],
            "technical_score": 88,
            "communication_score": 90,
            "overall_score": 89,
            "comments": "候选人技术基础扎实，沟通能力强...",
            "recommendation": "推荐录用"
        }
        """
        
        try:
            # 调用大模型 API
            response = client.chat.completions.create(
                model="qwen-turbo",
                messages=[
                    {"role": "system", "content": "你是一位专业的面试评估专家，负责评估技术面试表现。"},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                stream = False
            )
            
            # 解析返回的JSON结果
            result_text = response.choices[0].message.content
            evaluation_result = json.loads(result_text)
            
            # Create model output similar to the example
            model_output = {
                "candidate_name": candidate_name,
                "position": position_name,
                "interview_date": datetime.now().strftime("%Y年%m月%d日"),
                "interviewer": interviewer,
                "evaluation_result": evaluation_result
            }
            
            return model_output
            
        except Exception as e:
            print(f"调用AI模型时出错: {str(e)}")
            # 创建一个模拟的评估结果，以防API调用失败
            # 返回模拟数据
            model_output = {
                "candidate_name": candidate_name,
                "position": position_name,
                "interview_date": datetime.now().strftime("%Y年%m月%d日"),
                "interviewer": interviewer,
                "evaluation_result": {}
            }
            return model_output

def generate_pdf_report(model_output):
    """Generate PDF report using the template and model output"""
    # HTML template updated to match data structure from call_ai_model
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>面试报告</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; margin: auto; }
            .header { text-align: center; border-bottom: 2px solid #333; padding-bottom: 20px; }
            .section { margin-top: 20px; }
            .section h2 { color: #2c3e50; }
            .table { width: 100%; border-collapse: collapse; margin-top: 10px; }
            .table th, .table td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            .table th { background-color: #f2f2f2; }
            .question-section { border: 1px solid #ddd; padding: 15px; margin-bottom: 15px; border-radius: 5px; }
            .question-title { font-weight: bold; color: #2c3e50; }
            .score { font-weight: bold; color: #e74c3c; }
            .footer { margin-top: 30px; text-align: center; color: #7f8c8d; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>面试报告</h1>
                <p>{{ interview_date }}</p>
            </div>
            <div class="section">
                <h2>候选人信息</h2>
                <table class="table">
                    <tr><th>姓名</th><td>{{ candidate_name }}</td></tr>
                    <tr><th>应聘职位</th><td>{{ position }}</td></tr>
                    <tr><th>面试官</th><td>{{ interviewer }}</td></tr>
                </table>
            </div>
            <div class="section">
                <h2>面试评估</h2>
                <table class="table">
                    <tr><th>技术能力</th><td>{{ evaluation_result.technical_score }}/100</td></tr>
                    <tr><th>沟通能力</th><td>{{ evaluation_result.communication_score }}/100</td></tr>
                    <tr><th>综合评分</th><td>{{ evaluation_result.overall_score }}/100</td></tr>
                </table>
            </div>
            <div class="section">
                <h2>面试官评语</h2>
                <p>{{ evaluation_result.comments }}</p>
            </div>
            <div class="section">
                <h2>推荐意见</h2>
                <p>{{ evaluation_result.recommendation }}</p>
            </div>
            
            <div class="section">
                <h2>问题评估详情</h2>
                {% for question in evaluation_result.question_evaluations %}
                <div class="question-section">
                    <p class="question-title">问题{{ question.id }}: {{ question.question }}</p>
                    <p><strong>评分标准:</strong> {{ question.score_standard }}</p>
                    <p><strong>候选人回答:</strong> {{ question.answer }}</p>
                    <p><strong>评分:</strong> <span class="score">{{ question.score }}/10</span></p>
                    <p><strong>点评:</strong> {{ question.comments }}</p>
                </div>
                {% endfor %}
            </div>
            
            <div class="footer">
                <p>Generated by xAI Interview System</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Initialize Jinja2 environment
    env = Environment()
    
    # Load template from string
    template = env.from_string(html_template)
    
    # Render template
    rendered_html = template.render(**model_output)
    
    # Convert to PDF bytes
    pdf_bytes = HTML(string=rendered_html).write_pdf()
    
    return pdf_bytes

def update_interview_report(interview_id, report_content):
    """Save the report content to the interview record and update status to 4"""
    conn = sqlite3.connect('interview_system.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    UPDATE interviews 
    SET report_content = ?, status = 4 
    WHERE id = ?
    ''', (report_content, interview_id))
    
    conn.commit()
    conn.close()

def process_pending_reports():
    """Main function to process all interviews with status = 3"""
    print(f"[{datetime.now()}] Checking for interviews that need reports...")
    
    # 1. Get all interviews with status = 3
    interviews = fetch_interviews_with_status_3()
    
    if not interviews:
        print("No interviews need reports at this time.")
        return
    
    print(f"Found {len(interviews)} interviews that need reports.")
    
    for interview in interviews:
        try:
            interview_id = interview['id']
            candidate_id = interview['candidate_id']
            interviewer = interview['interviewer']
            
            # 2. Get candidate information
            candidate = fetch_candidate_info(candidate_id)
            if not candidate:
                print(f"Could not find candidate with ID {candidate_id}")
                continue
            
            # 3. Get position information
            position = fetch_position_info(candidate['position_id'])
            if not position:
                print(f"Could not find position with ID {candidate['position_id']}")
                continue
            
            # 4. Get interview questions and answers
            questions = fetch_interview_questions(interview_id)
            
            # 5. Call AI model to generate report
            model_output = call_ai_model(
                candidate['name'],
                position['name'],
                interviewer,
                questions
            )
            
            # Generate PDF report
            pdf_report = generate_pdf_report(model_output)
            
            # 6. Save report to database
            # 7. Update interview status to 4
            update_interview_report(interview_id, pdf_report)
            
            print(f"Generated report for interview ID {interview_id}, candidate: {candidate['name']}")
            
        except Exception as e:
            print(f"Error processing interview ID {interview.get('id', 'unknown')}: {str(e)}")

def run_scheduler():
    """Set up the scheduler to run the task every 5 minutes"""
    # Schedule the job to run every 5 minutes
    schedule.every(5).minutes.do(process_pending_reports)
    
    # Run the job once immediately when starting
    process_pending_reports()
    
    # Keep the script running
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    print("Starting interview report generation service...")
    run_scheduler() 