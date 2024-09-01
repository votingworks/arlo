# set base image (host OS)
FROM python:3.8

RUN apt-get update && \
    apt-get install -y locales && \
    sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
    dpkg-reconfigure --frontend=noninteractive locales
    
ENV POETRY_VERSION=1.1.15
ENV LC_ALL en_US.UTF-8
ENV ENV LANG en_US.UTF-8

RUN pip install -U poetry==$POETRY_VERSION

COPY ./server ./server 
COPY ./scripts ./scripts 
COPY ./pyproject.toml .
COPY ./poetry.lock .
COPY ./alembic.ini .

RUN poetry install

# command to run on container start
#ENTRYPOINT ["poetry", "run", "python", "-m", "main"]

