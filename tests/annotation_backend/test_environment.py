
import sqlite3
def test_environment_ready():
    conn = sqlite3.connect(":memory:")
    cur = conn.cursor()
    cur.execute("CREATE TABLE test (id INT, val TEXT)")
    cur.execute("INSERT INTO test VALUES (1, 'ok')")
    conn.commit()
    cur.execute("SELECT val FROM test")
    res = cur.fetchone()[0]
    assert res == 'ok'
    conn.close()
