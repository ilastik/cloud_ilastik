VENV_PYTHON = venv/bin/python
VENV_PIP = venv/bin/pip
VENV_CELERY = venv/bin/celery

setup_dev:
	python3 -m venv venv
	${VENV_PIP} install -r requirements/local.txt
	${VENV_PYTHON} ./manage.py migrate
	${VENV_PYTHON} ./manage.py createsuperuser --username=ilastik --password=ilastik --email=ilastik@example.com --noinput

run_server:
	${VENV_PYTHON} ./manage.py check --tag=database
	${VENV_PYTHON} ./manage.py runserver

run_worker:
	${VENV_CELERY} beat -A config.celery_app --loglevel=INFO

clean:
	rm -fr venv
	rm -fr temp.db
	rm -fr cloud_ilastik/media/

.PHONY: clean setup run_server run_worker
