# set base image (host OS)
FROM python:3.8


ENV POETRY_VERSION=1.1.15

RUN pip install -U poetry==$POETRY_VERSION

COPY . . 
COPY ./pyproject.toml .
COPY ./poetry.lock .

RUN poetry install

# command to run on container start
ENTRYPOINT ["poetry", "run", "python", "-m", "server.main"]

