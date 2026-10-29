import sqlite3

conn = sqlite3.connect('backend/availo.db')
cur = conn.cursor()

# Create damage_claims table if not exists
cur.execute('''
CREATE TABLE IF NOT EXISTS damage_claims (
    id VARCHAR(36) PRIMARY KEY,
    incident_id VARCHAR(36) NOT NULL REFERENCES incident_reports(id) ON DELETE CASCADE,
    claimant_id VARCHAR(36) NOT NULL REFERENCES users(id),
    description TEXT NOT NULL,
    photo_angles JSON DEFAULT "[]",
    justification TEXT NOT NULL,
    estimated_cost NUMERIC(10, 2) DEFAULT 0.00,
    invoice_url VARCHAR(1024),
    requested_resolution VARCHAR(32) DEFAULT "COMPENSATION",
    status VARCHAR(32) DEFAULT "SUBMITTED",
    researcher_response VARCHAR(32),
    researcher_note TEXT,
    researcher_counter_amount NUMERIC(10, 2),
    researcher_evidence_url VARCHAR(1024),
    responded_at TIMESTAMP,
    repair_plan TEXT,
    repair_due_date TIMESTAMP,
    repair_evidence_url VARCHAR(1024),
    repair_verified_by_id VARCHAR(36),
    repair_verified_at TIMESTAMP,
    agreed_compensation NUMERIC(10, 2),
    payment_reference VARCHAR(256),
    settled_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

print("Created damage_claims table successfully")
conn.commit()
conn.close()
