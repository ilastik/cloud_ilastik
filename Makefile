setup_dev:
	python3 -m venv venv
	. venv/bin/activate
	pip install -r requirements/local.txt
	python ./manage.py migrate
	python ./manage.py createsuperuser --username=ilastik --password=ilastik --email=ilastik@example.com --noinput

runserver:
	python ./manage.py check --tag=database
	python ./manage.py runserver


clean:
	rm -fr venv
	rm -fr temp.db
	rm -fr cloud_ilastik/media/


.PHONY: clean setup
