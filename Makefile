build:
	docker compose --file ./cicd/docker-compose.yml build

up: start
run: start
start: stop
	docker compose --file ./cicd/docker-compose.yml up --detach

stop:
	docker compose --file ./cicd/docker-compose.yml down

configure:
	cd backend && python3.11 -m venv venv
	cd backend && source ./venv/bin/activate && pip install -r requirements.dev.txt -r requirements.txt
	cd frontend && npm install

format:
	cd backend && source ./venv/bin/activate && autoflake -r --in-place --remove-all-unused-imports ./src
	cd backend && source ./venv/bin/activate && isort ./src
	cd backend && source ./venv/bin/activate && black ./src