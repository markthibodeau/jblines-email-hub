"""
JBLines Email Hub — FastAPI application entry point.

Starts the scheduler, creates database tables, and mounts all API routes.
"""

import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import create_tables
from app.email_sync import sync_all_inboxes
from app.routers import auth, emails, customers, billing, schedule, chat, admin

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run on startup and shutdown."""
    logger.info("Starting JBLines Email Hub...")
    await create_tables()

    # Schedule email sync every 15 minutes
    scheduler.add_job(sync_all_inboxes, "interval", minutes=15, id="email_sync")
    scheduler.start()
    logger.info("Email sync scheduler started (every 15 minutes)")

    # Kick off initial sync as a background task so the server can open
    # its port immediately — a full 180-day sync across 6 inboxes can
    # take several minutes and would cause Render's health check to time out
    import asyncio
    asyncio.create_task(sync_all_inboxes())
    logger.info("Initial email sync started in background")

    yield

    scheduler.shutdown()
    logger.info("Scheduler stopped.")


app = FastAPI(
    title="JBLines Email Hub",
    description="Centralized email intelligence for JBLines — customers, billing, and scheduling.",
    version="1.0.0",
    lifespan=lifespan,
)

# Allow the Next.js frontend to talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",           # Local development
        "https://*.vercel.app",            # Vercel preview deployments
        "*",                               # Set to your actual domain in production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all routers
app.include_router(auth.router,      prefix="/api/auth",      tags=["Auth"])
app.include_router(emails.router,    prefix="/api/emails",    tags=["Emails"])
app.include_router(customers.router, prefix="/api/customers", tags=["Customers"])
app.include_router(billing.router,   prefix="/api/billing",   tags=["Billing"])
app.include_router(schedule.router,  prefix="/api/schedule",  tags=["Schedule"])
app.include_router(chat.router,      prefix="/api/chat",      tags=["Chat"])
app.include_router(admin.router,     prefix="/api/admin",     tags=["Admin"])


@app.get("/")
async def root():
    return {"status": "JBLines Email Hub is running", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/sync/trigger")
async def trigger_sync():
    """Manually trigger an email sync (admin use)."""
    import asyncio
    asyncio.create_task(sync_all_inboxes())
    return {"status": "Sync triggered in background"}
