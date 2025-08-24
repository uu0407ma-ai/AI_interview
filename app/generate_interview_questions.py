import sqlite3
import time
import schedule
import threading
import json
import io
from datetime import datetime
from openai import OpenAI
import PyPDF2
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

# 初始化OpenAI客户端
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL")
)
    
# 从PDF二进制数据中提取文本内容
def extract_text_from_pdf(pdf_content):
    try:
        # 如果输入是None或空值，返回空字符串
        if pdf_content is None or pdf_content == b'':
            return "无简历内容"
            
        # 创建BytesIO对象处理二进制数据
        pdf_file = io.BytesIO(pdf_content)
        
        # 创建PDF阅读器
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        # 提取所有页面的文本
        text = ""
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text += page.extract_text() + "\n"
        
        # 如果没有提取到文本，尝试使用另一种方法
        if not text.strip():
            return "无法从PDF中提取文本内容"
            
        return text
    except Exception as e:
        print(f"PDF文本提取错误: {str(e)}")
        # 如果pdf解析失败，尝试作为纯文本处理
        try:
            if isinstance(pdf_content, bytes):
                return pdf_content.decode('utf-8', errors='ignore')
            return str(pdf_content)
        except:
            return "无法解析简历内容"

# 连接到SQLite数据库
def get_db_connection():
    return sqlite3.connect('interview_system.db')

# 获取未开始的面试列表
def get_pending_interviews():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 获取所有状态为0(未开始)的面试
    cursor.execute('''
        SELECT i.id, i.candidate_id, i.interviewer, i.start_time
        FROM interviews i
        WHERE i.status = 0
    ''')
    
    interviews = cursor.fetchall()
    conn.close()
    return interviews

# 获取候选人信息
def get_candidate_info(candidate_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT c.id, c.name, c.email, c.resume_content, c.position_id
        FROM candidates c
        WHERE c.id = ?
    ''', (candidate_id,))
    
    candidate = cursor.fetchone()
    conn.close()
    return candidate

# 获取岗位信息
def get_position_info(position_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT p.id, p.name, p.requirements, p.responsibilities
        FROM positions p
        WHERE p.id = ?
    ''', (position_id,))
    
    position = cursor.fetchone()
    conn.close()
    return position

# 根据简历内容和岗位信息生成面试问题
def generate_questions(resume_content, position_name, requirements, responsibilities):
    # 解析简历内容 : 抽取pdf中resume_content的文本内容
    try:
        resume_text = extract_text_from_pdf(resume_content)
    except:
        resume_text = "无法解析简历内容"
    
    print("resume_text:", resume_text)

    # 返回json格式参考
    json_format = [
         {"question": "请介绍一下你的专业背景和技能", "score_standard": "清晰度5分，相关性5分，深度5分"},
         {"question": "你认为自己最适合这个岗位的原因是什么？", "score_standard": "匹配度5分，自我认知5分，表达5分"},
         {"question": "描述一个你解决过的技术挑战", "score_standard": "复杂度5分，解决方案5分，结果5分"},
         {"question": "你如何看待团队合作？", "score_standard": "协作能力5分，沟通能力5分，角色意识5分"},
         {"question": "你对这个行业的未来趋势有什么看法？", "score_standard": "了解程度5分，前瞻性5分，分析能力5分"}
    ]
    # 调用OpenAI API生成面试问题
    try:
        response = client.chat.completions.create(
            #model="gpt-4", # 或其他适合的模型
            model="qwen-turbo",
            messages=[
                {"role": "system", "content": "你是一名专业的招聘面试官，请根据岗位要求和候选人简历生成5个针对性的技术面试问题，每个问题附带评分标准,返回标准的json格式。"},
                {"role": "user", "content": f"岗位名称: {position_name}\n岗位要求: {requirements}\n岗位职责: {responsibilities}\n候选人简历: {resume_text}\n\n请生成10个面试问题和评分标准，JSON格式参考 {json_format} ，每个问题满分10分。"}
            ],
            response_format={"type": "json_object"},
            stream = False
        )
        
        # 解析响应内容
        questions_json = response.choices[0].message.content
        questions = json.loads(questions_json)
        print("questions:", questions)
        
        return questions

    except Exception as e:
        print(f"生成面试问题时出错: {str(e)}")
 

# 将生成的问题保存到数据库
def save_questions(interview_id, questions):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    for question in questions:
        # 将score_standard转换为JSON字符串(如果是字典类型)
        score_standard = question['score_standard']
        if isinstance(score_standard, dict):
            score_standard = json.dumps(score_standard, ensure_ascii=False)
            
        cursor.execute('''
            INSERT INTO interview_questions (interview_id, question, score_standard)
            VALUES (?, ?, ?)
        ''', (interview_id, question['question'], score_standard))
    
    # 更新面试状态为"试题已备好"(1)
    cursor.execute('''
        UPDATE interviews SET status = 1 , question_count = ? WHERE id = ?
    ''', (len(questions), interview_id))
    
    conn.commit()
    conn.close()

# 主处理函数
def process_pending_interviews():
    print(f"[{datetime.now()}] 开始处理未开始的面试...")
    
    # 获取所有未开始的面试
    pending_interviews = get_pending_interviews()
    
    if not pending_interviews:
        print("没有未开始的面试需要处理")
        return
    
    print(f"找到 {len(pending_interviews)} 个待处理的面试")
    
    for interview in pending_interviews:
        interview_id, candidate_id, interviewer, start_time = interview
        
        # 获取候选人信息
        candidate = get_candidate_info(candidate_id)
        if not candidate:
            print(f"无法找到候选人ID: {candidate_id}的信息")
            continue
        
        candidate_id, candidate_name, candidate_email, resume_content, position_id = candidate
        
        # 获取岗位信息
        position = get_position_info(position_id)
        if not position:
            print(f"无法找到岗位ID: {position_id}的信息")
            continue
        
        position_id, position_name, requirements, responsibilities = position
        
        print(f"为面试ID: {interview_id}, 候选人: {candidate_name}, 岗位: {position_name} 生成面试问题")
        
        # 生成面试问题
        questions = generate_questions(resume_content, position_name, requirements, responsibilities)
        
        # 保存问题到数据库
        save_questions(interview_id, questions)

        
        print(f"已为面试ID: {interview_id} 成功生成 {len(questions)} 个问题")

# 定时任务
def run_scheduler():
    schedule.every(5).minutes.do(process_pending_interviews)
    
    while True:
        schedule.run_pending()
        time.sleep(1)

# 主函数
if __name__ == "__main__":
  
    # 立即运行一次，然后启动定时任务
    process_pending_interviews()
    
    # 在后台线程中运行定时任务
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()
    
    print("面试问题生成定时任务已启动，每5分钟执行一次")
    
    try:
        # 保持主线程运行
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("程序已停止") 