install:
	pip install -r requirements.txt

run:
	python deployment/main.py

dashboard:
	python monitoring/fast_dashboard.py