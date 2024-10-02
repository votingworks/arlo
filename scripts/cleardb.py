from server.database import engine, clear_db

if __name__ == "__main__":
    print(f"database: {engine.url}")

    print("clearing data from all tables…")
    clear_db()
