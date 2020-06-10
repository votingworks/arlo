# pylint: disable=invalid-name
import sys

from server.api.routes import create_organization

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m scripts.create-org <org_name>")
        sys.exit(1)

    print(create_organization(sys.argv[1]).id)
