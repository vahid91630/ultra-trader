install:
	pip install -r requirements.txt

run:
	python deployment/main.py

dashboard:
	python fast_dashboard.py

monitor:
	python -m monitoring.news_monitor