@router.get("/")
async def root():
    return {"status": "ok", "service": "Sports-Booking"}

@router.get("/health-public")
async def health_public():
    return {"status": "ok"}