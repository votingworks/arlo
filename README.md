# Arlo: Open-source risk-limiting audit software by [Voting Works](voting.works)

## Setting up the dev environment

1. Download [`python-dev`](https://www.python.org/) >3.7 
2. Download [`pip`](https://pypi.org/project/pip/)
3. Install `pipenv` (note: run `python3 -m pip install pipenv` to get a version that's compatible with your python install if your system defaults to a python other than >3.7).
4. Install [`yarn`](https://yarnpkg.com/en/docs/install).
5. Run via `./run-dev.sh`

### Troubleshooting

* `psychopg2` has known issues depending on your install (see, e.g., [here](https://github.com/psycopg/psycopg2/issues/674)). If you run into issues, switch `psychopg2` to `psychopg2-binary` in the Pipfile
* `pipenv install` can hang attempting to get [a lock on the packages it's installing](https://github.com/pypa/pipenv/issues/3827). To get around this, add the `--skip-lock` flag in the Makefile (the first line should be `pipenv install --skip-lock`).
