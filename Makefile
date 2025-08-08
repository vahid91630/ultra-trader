install:
	pip install -r requirements.txt

run:
	python deployment/main.py

dashboard:
	gunicorn --bind 0.0.0.0:$${PORT:-5000} fast_dashboard:app