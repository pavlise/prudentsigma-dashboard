@echo off
cd /d "C:\Users\Pavlos Elpidorou\Documents\AI_Project"
call .venv\Scripts\activate.bat
streamlit run dashboard.py --logger.level=error
