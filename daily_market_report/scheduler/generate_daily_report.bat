@echo off
cd /d "C:\Users\Pavlos Elpidorou\Documents\AI_Project"
python automated_report.py
echo Report generation completed at %date% %time% >> reports\log.txt