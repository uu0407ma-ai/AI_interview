# AI智能面试系统

一个基于AI的自动化面试系统，能够根据候选人简历和岗位需求自动生成面试问题，支持在线语音面试，并能自动生成面试评估报告。

## 功能特点

- **智能面试问题生成**：基于候选人简历和岗位要求，自动生成针对性面试问题
- **在线语音面试**：候选人可通过网页进行语音回答，系统自动录音和转写
- **自动面试评估**：系统自动分析面试表现，生成详细的面试评估报告
- **完整招聘管理**：支持岗位管理、候选人管理和面试流程管理
- **定时自动处理**：定期检查并处理待生成的面试问题和面试报告

## 系统架构

- **后端**：基于Python和Flask的RESTful API服务
- **前端**：使用Vue.js和Bootstrap构建的响应式Web界面
- **数据库**：使用SQLite进行数据存储
- **AI模型**：集成大语言模型(GLM-4-plus)用于问题生成和面试评估
- **语音处理**：集成Whisper模型进行语音识别

## 安装指南

### 环境要求

- Python 3.10+
- 各种Python依赖包

### 安装步骤

1. **进入项目app目录**

```bash
cd app
```

2. **创建并激活虚拟环境**

```bash
python -m venv .venv
source .venv/bin/activate  # 在Windows上使用: .venv\Scripts\activate
```

3. **安装依赖包**

```bash
pip install -r requirements.txt
```

注意：安装weasyprint可能需要额外的系统依赖，请参考[weasyprint文档](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html)。

4. **初始化数据库**

```bash
python create_interview_system_db.py
```

## 使用说明

### 启动系统服务

1. **启动Web服务器**

```bash
python server.py
```

2. **启动面试问题生成服务**

```bash
python generate_interview_questions.py
```

3. **启动面试报告生成服务**

```bash
python generate_interview_reports.py
```

默认情况下，Web服务器会在 http://localhost:8000 上运行。

面试系统管理入口： http://localhost:8000/static/admin.html



### 系统流程

1. 管理员创建招聘岗位
2. 添加候选人信息和简历
3. 安排面试并生成面试链接
4. 系统自动为面试生成问题
5. 候选人通过链接参加面试
6. 面试完成后系统自动生成评估报告

## 主要脚本说明

| 文件名                        | 功能描述                                          |
|------------------------------|--------------------------------------------------|
| create_interview_system_db.py | 创建SQLite数据库和相关表结构                      |
| generate_interview_questions.py | 自动为待处理的面试生成面试问题                    |
| generate_interview_reports.py | 自动为已完成的面试生成评估报告                    |
| server.py                    | 提供Web API服务，处理前端请求                     |
| interview.html               | 面试前端界面，供候选人进行在线面试                  |

## 注意事项

1. **API密钥配置**：请确保在`generate_interview_questions.py`和`generate_interview_reports.py`中配置正确的大语言模型API密钥 , 修改位于 app目录下的 .env环境变量 。

2. **语音识别**：系统使用Whisper模型进行语音识别，首次运行时会自动下载模型，这可能需要一些时间。

3. **PDF处理**：系统支持解析候选人的PDF简历，但可能对某些格式的PDF支持不完善。

4. **定时任务**：系统使用schedule库实现定时任务，默认每5分钟检查一次是否有新的面试需要生成问题或报告。

5. **浏览器兼容性**：面试界面使用现代Web技术，推荐使用Chrome、Firefox、Edge等现代浏览器。

## 开发与扩展

系统使用模块化设计，可以根据需要进行扩展：

- 添加新的面试问题类型
- 集成不同的AI模型
- 扩展面试评估维度
- 添加更多的招聘管理功能

## 技术依赖

- Flask: Web服务器框架
- Vue.js: 前端框架
- Bootstrap: UI组件库
- OpenAI/GLM API: 生成面试问题和报告
- Whisper: 语音识别
- SQLite: 数据存储
- Weasyprint: PDF生成
- PyPDF2: PDF解析
- Schedule: 定时任务调度 