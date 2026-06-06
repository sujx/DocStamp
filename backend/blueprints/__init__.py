"""HTTP route layer — Blueprint modules that only handle request/response.

Each module:
- Extracts parameters from Flask request (form, files, query, JSON body)
- Calls service-layer functions
- Returns JSON or send_file responses

No business logic lives here — it all lives in services/.
"""
