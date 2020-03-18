# React app

- GET /
- GET /election/<election_id>
- GET /auditboard/<passphrase>
- GET /election/<election_id>/board/<board_id>
- GET /<path:filename>

# Auth

- GET /auth/jurisdictionadmin/callback
- GET /auth/jurisdictionadmin/start
- GET /auth/auditadmin/callback
- GET /auth/auditadmin/start
- GET /auth/logout
- GET /auth/me

# Audit set up

- POST /election/new
- POST /election/<election_id>/audit/basic
- GET /election/<election_id>/audit/status
- POST /election/<election_id>/audit/sample-size
- POST /election/<election_id>/audit/jurisdictions
- POST /election/<election_id>/jurisdiction/<jurisdiction_id>/manifest
- POST /election/<election_id>/audit/freeze
- POST /election/<election_id>/audit/reset

# Multi-jurisdiction audit set up

- GET /election/<election_id>/jurisdictions_file
- POST /election/<election_id>/jurisdictions_file

# Running the audit

- GET /election/<election_id>/jurisdiction/<jurisdiction_id>/<round_num>/retrieval-list
- POST /election/<election_id>/jurisdiction/<jurisdiction_id>/<round_num>/results
- GET /election/<election_id>/jurisdiction/<jurisdiction_id>/round/<round_id>/ballot-list
- GET /election/<election_id>/jurisdiction/<jurisdiction_id>/audit-board/<audit_board_id>/round/<round_id>/ballot-list
- POST /election/<election_id>/jurisdiction/<jurisdiction_id>/batch/<batch_id>/ballot/<ballot_position>

# Audit board member sign up

- GET /election/<election_id>/jurisdiction/<jurisdiction_id>/audit-board/<audit_board_id>
- POST /election/<election_id>/jurisdiction/<jurisdiction_id>/audit-board/<audit_board_id>

# Audit report

- GET /election/<election_id>/audit/report
