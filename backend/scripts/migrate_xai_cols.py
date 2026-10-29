import sqlite3

conn = sqlite3.connect('backend/availo.db')
cur = conn.cursor()

new_cols = [
    ('comparison_status', 'VARCHAR(64) DEFAULT "comparable"'),
    ('similarity_metric', 'FLOAT DEFAULT 1.0'),
    ('similarity_algorithm', 'VARCHAR(128) DEFAULT "Normalized Grayscale L1 Pixel Difference"'),
    ('observed_differences', 'JSON DEFAULT "[]"'),
    ('damage_category', 'VARCHAR(64)'),
    ('location_description', 'TEXT'),
    ('supporting_evidence', 'TEXT'),
    ('alternative_explanations', 'JSON DEFAULT "[]"'),
    ('human_review_required', 'BOOLEAN DEFAULT 0'),
    ('difference_image_url', 'VARCHAR(1024)'),
    ('bounding_boxes', 'JSON DEFAULT "[]"'),
]

for col_name, col_type in new_cols:
    try:
        cur.execute(f'ALTER TABLE damage_assessments ADD COLUMN {col_name} {col_type}')
        print(f'Added column {col_name}')
    except Exception as e:
        print(f'Column {col_name} skipped or error: {e}')

conn.commit()
conn.close()
print('Migration complete')

