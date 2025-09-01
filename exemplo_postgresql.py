import psycopg2
from dotenv import load_dotenv

postgres_password = load_dotenv("SENHA_POSTGRES")

def main():
    conn = psycopg2.connect(f"'postgres://{postgres_password}@pg-zambom-primeiro-aiven-alex.g.aivencloud.com:10404/defaultdb?sslmode=require'")

    query_sql = 'SELECT VERSION()'

    cur = conn.cursor()
    cur.execute(query_sql)

    version = cur.fetchone()[0]
    print(version)


if __name__ == "__main__":
    main()