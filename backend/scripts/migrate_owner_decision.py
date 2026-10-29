import sqlite3

conn = sqlite3.connect('backend/availo.db')
cur = conn.cursor()

new_cols = [
    ('owner_decision', 'VARCHAR(32)'),  # NO_DAMAGE_REPORTED | DAMAGE_REPORTED
    ('owner_decision_at', 'TIMESTAMP'),
    ('owner_decision_by_id', 'VARCHAR(36)'),
]

for col_name, col_type in new_cols:
    try:
        cur.execute(f'ALTER TABLE incident_reports ADD COLUMN {col_name} {col_type}')
        print(f'Added column {col_name} to incident_reports')
    except Exception as e:
        print(f'Column {col_name} skipped or error: {e}')

conn.commit()
conn.close()
print('Migration complete')
