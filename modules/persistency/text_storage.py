import sqlite3
from pathlib import Path

# Path to the SQLite database file
DB_PATH = Path("data/crawler_memory.db")

def get_connection(db_path=DB_PATH):
    return sqlite3.connect(db_path)

def create_database_file(db_path=DB_PATH):
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if not db_path.exists():
        db_path.touch()
        print(f"Created DB file at {db_path.resolve()}")
    else:
        print(f"DB file already exists at {db_path.resolve()}")

def setup_database():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS webpages")
    cur.execute("""
        CREATE VIRTUAL TABLE webpages USING fts5(
            url,
            content
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

def save_page(url, content):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO webpages (url, content)
        VALUES (?, ?)
    """, (url, content))
    conn.commit()
    cur.close()
    conn.close()

def wipe_database():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM webpages;")
    conn.commit()
    cur.close()
    conn.close()

def count_words(keyword=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("CREATE VIRTUAL TABLE IF NOT EXISTS vocab USING fts5vocab(webpages, 'row')")
    
    if keyword:
        cur.execute("SELECT sum(cnt) FROM vocab WHERE term = ?", (keyword.lower(),))
    else:
        cur.execute("SELECT sum(cnt) FROM vocab")
    
    total_words = cur.fetchone()[0] or 0
    cur.close()
    conn.close()
    return total_words

def save_many_pages(pages):
    create_database_file()
    setup_database()
    conn = get_connection()
    cur = conn.cursor()
    cur.executemany("""
        INSERT INTO webpages (url, content)
        VALUES (?, ?)
    """, pages)
    conn.commit()
    cur.close()
    conn.close()

if __name__ == "__main__":
    create_database_file()
    setup_database()
    
    save_page(
        "https://example.com/about",
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Curabitur gravida pellentesque orci. Cras lectus risus, ornare dictum lacus eget, efficitur commodo felis. Donec leo arcu, gravida ut augue ut, maximus tristique neque. Nulla semper cursus turpis, posuere maximus libero finibus in. Nullam pellentesque dui sit amet nibh pharetra ultrices. Cras congue, purus quis commodo finibus, nulla nisi suscipit ex, et tincidunt neque massa eu ipsum. Cras mattis ipsum sagittis leo laoreet accumsan."
    )

    print(f"Total word count: {count_words()}")
    print(f"Count of 'lorem': {count_words('lorem')}")
