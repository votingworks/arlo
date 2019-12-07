FROM python:3.7.3
RUN pip install --upgrade pip
RUN pip install pipenv
RUN mkdir /code
WORKDIR /code
COPY Pipfile Pipfile.lock /code/
RUN pipenv install --dev