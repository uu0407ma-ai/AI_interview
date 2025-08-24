import sqlite3

# 连接到SQLite数据库（如果不存在则创建）
conn = sqlite3.connect('interview_system.db')
cursor = conn.cursor()

# 创建待招聘岗位表
cursor.execute('''
CREATE TABLE IF NOT EXISTS positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT, -- 岗位ID，唯一标识
    name TEXT NOT NULL, -- 岗位名称
    requirements TEXT, -- 岗位要求
    responsibilities TEXT, -- 岗位职责
    quantity INTEGER, -- 需求人数
    status INTEGER, -- 招聘状态：0=未启动，1=进行中，2=已完成
    created_at INTEGER DEFAULT (strftime('%s', 'now')), -- 岗位发布时间，Unix时间戳
    recruiter TEXT -- 招聘负责人
)
''')

# 创建候选人表
cursor.execute('''
CREATE TABLE IF NOT EXISTS candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT, -- 候选人ID，唯一标识
    position_id INTEGER NOT NULL, -- 申请的岗位ID
    name TEXT NOT NULL, -- 候选人姓名
    email TEXT, -- 候选人邮件
    resume_content BLOB -- 简历文件二进制内容
)
''')

# 创建面试表
cursor.execute('''
CREATE TABLE IF NOT EXISTS interviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT, -- 面试ID，唯一标识
    candidate_id INTEGER NOT NULL, -- 候选人ID
    interviewer TEXT, -- 面试官
    start_time INTEGER, -- 面试开始时间，Unix时间戳
    end_time INTEGER, -- 面试结束时间，Unix时间戳
    status INTEGER, -- 面试状态：0=未开始，1=试题已备好 2 =面试进行中  3 =面试完毕 4 =面试报告已生成
    question_count INTEGER, -- 面试问题数量
    is_passed INTEGER, -- 面试结果：0=未通过，1=通过
    voice_reading INTEGER, -- 是否开启语音朗读：0=关闭，1=开启
    report_content BLOB, -- 面试报告二进制内容
    token TEXT -- 面试链接验证令牌
)
''')

# 创建面试问题表
cursor.execute('''
CREATE TABLE IF NOT EXISTS interview_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT, -- 问题ID，唯一标识
    interview_id INTEGER NOT NULL, -- 面试ID
    question TEXT NOT NULL, -- 面试问题内容
    score_standard TEXT, -- 评分标准或分值说明
    answer_audio BLOB, -- 回答录音二进制内容
    answer_text TEXT, -- 回答文本内容
    created_at INTEGER DEFAULT (strftime('%s', 'now')), -- 问题创建时间，Unix时间戳
    answered_at INTEGER -- 回答时间，Unix时间戳
)
''')





# 提交更改并关闭连接
conn.commit()
conn.close()

print("数据库和表已成功创建。")