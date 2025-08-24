#!/bin/sh
python server.py &
python generate_interview_questions.py &
python generate_interview_reports.py &
wait