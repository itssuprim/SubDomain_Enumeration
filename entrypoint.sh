#!/bin/bash

# Start MariaDB service
service mysql start

# Wait for DB to start
sleep 10

# Initialize database
mysql -uroot -proot subdomain_tool << EOF
CREATE TABLE IF NOT EXISTS results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tool_name VARCHAR(255),
    result VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS errors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    error_message TEXT
);
EOF

# Run your Python script
python3 subenum.py -d example.com -o output