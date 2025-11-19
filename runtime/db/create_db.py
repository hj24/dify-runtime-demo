import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def create_database():
    # Connect to default 'postgres' database
    try:
        con = psycopg2.connect(dbname='postgres', host='localhost', user='postgres', password='difyai123456')
        con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = con.cursor()
        
        # Check if db exists
        cur.execute("SELECT 1 FROM pg_database WHERE datname = 'dsl_demo'")
        exists = cur.fetchone()
        
        if not exists:
            cur.execute('CREATE DATABASE dsl_demo')
            print("Database 'dsl_demo' created successfully.")
        else:
            print("Database 'dsl_demo' already exists.")
            
        cur.close()
        con.close()
    except Exception as e:
        print(f"Failed to create database: {e}")

if __name__ == "__main__":
    create_database()
