import sqlite3

DB_NAME = "vehicle.db"


#Create the database and table if they do not exist.
def init():
    global conn, cursor
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vehicles_in (
            ticket_id INTEGER PRIMARY KEY,
            plate TEXT,
            type TEXT NOT NULL
                CHECK (type IN ('CAR', 'MOTORCYCLE', 'BYCYCLE')),
            IN_TIME INTEGER NOT NULL
        )
    """)

    conn.commit()

#Get a vehicle by ticket ID. Return a dict or None.
def get(ticket):
    cursor.execute("""
        SELECT ticket_id, plate, type, IN_TIME
        FROM vehicles_in
        WHERE ticket_id = ?
    """, (ticket,))

    row = cursor.fetchone()
    return dict(row) if row else None

#Insert a vehicle entry. Return True if successful.
def post(ticket, plate, type, time_in):
    try:
        cursor.execute("""
            INSERT INTO vehicles_in (ticket_id, plate, type, IN_TIME)
            VALUES (?, ?, ?, ?)
        """, (ticket, plate, type, time_in))

        conn.commit()
        return True

    except sqlite3.IntegrityError:
        conn.rollback()
        return False

#Delete a vehicle by ticket ID. Return True if a row was deleted.
def delete(ticket):
    cursor.execute("""
        DELETE FROM vehicles_in
        WHERE ticket_id = ?
    """, (ticket,))

    deleted = cursor.rowcount > 0
    conn.commit()
    return deleted

#Close the database connection.
def close():
    conn.close()