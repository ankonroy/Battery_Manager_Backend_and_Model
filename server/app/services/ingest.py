from server.app.models.session import SessionUpload

class IngestService:
    async def process_session(self, session: SessionUpload):
        # 1. Validate data (already handled by Pydantic)
        # 2. Normalize units if necessary
        # 3. Save to database (TimescaleDB)
        # 4. Trigger anomaly detection check (async)
        
        # Placeholder implementation
        print(f"Processing session for device: {session.device_id}")
        return {"status": "success", "message": "Session recorded"}
