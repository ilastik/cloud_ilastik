setup_dev:
	python3 -m venv venv
	. venv/bin/activate
	pip install -r requirements/local.txt
	python ./manage.py migrate
	python ./manage.py createsuperuser --username=ilastik --password=ilastik --email=ilastik@example.com --noinput

run_server:
	venv/bin/python ./manage.py check --tag=database
	venv/bin/python ./manage.py runserver

run_worker:
	venv/bin/celery beat -A config.celery_app --loglevel=INFO

clean:
	rm -fr venv
	rm -fr temp.db
	rm -fr cloud_ilastik/media/

.PHONY: clean setup run_server, run_worker
