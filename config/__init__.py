import configparser
import os
import sys

DEFAULT_DATABASE_URL = 'postgres://postgres@localhost:5432/arlo'

def read_database_url_config() -> str:
  environment_database_url = os.environ.get('DATABASE_URL', None)

  if environment_database_url:
    return environment_database_url

  database_cfg_path = os.path.normpath(os.path.join(__file__, '..', 'database.cfg'))
  database_config = configparser.ConfigParser()
  database_config.read(database_cfg_path)

  flask_env = os.environ.get('FLASK_ENV', 'development')
  result = database_config.get(flask_env, 'database_url', fallback=None)

  if not result:
    print(f'WARNING: no database url was configured, falling back to default: {DEFAULT_DATABASE_URL}', file=sys.stderr)
    print(f'To configure your own database url, either run with a DATABASE_URL environment variable', file=sys.stderr)
    print(f'or copy `config/database.cfg.example` to `config/database.cfg` and edit it as needed.', file=sys.stderr)

  return result or DEFAULT_DATABASE_URL

DATABASE_URL = read_database_url_config()
