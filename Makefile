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
	cd backend && source ./venv/bin/activate && autoflake -r --in-place --remove-all-unused-imports ./app
	cd backend && source ./venv/bin/activate && isort ./app
	cd backend && source ./venv/bin/activate && black ./app
	cd backend && source ./venv/bin/activate && autoflake -r --in-place --remove-all-unused-imports ./data
	cd backend && source ./venv/bin/activate && isort ./data
	cd backend && source ./venv/bin/activate && black ./data
	cd backend && source ./venv/bin/activate && autoflake -r --in-place --remove-all-unused-imports ./tests
	cd backend && source ./venv/bin/activate && isort ./tests
	cd backend && source ./venv/bin/activate && black ./tests
	cd backend && source ./venv/bin/activate && autoflake -r --in-place --remove-all-unused-imports ./migrations
	cd backend && source ./venv/bin/activate && isort ./migrations
	cd backend && source ./venv/bin/activate && black ./migrations