from typing import Optional
import stripe
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field

from ..services.db import db
from ..settings import settings
from ..utils.audit import audit_event
from ..utils.security import get_current_user
from .websocket import send_notification

router = APIRouter()

# Configure Stripe
stripe.api_key = settings.STRIPE_API_KEY

class SubscriptionStatus(BaseModel):
    plan: Optional[str] = Field(None, description="Current subscription plan")
    status: str = Field(..., description="Subscription status")
    trial_remaining: Optional[int] = Field(None, description="Remaining trial edits")

class CheckoutSession(BaseModel):
    session_id: str = Field(..., description="Stripe checkout session ID")

@router.get("/status", response_model=SubscriptionStatus,
            summary="Get subscription status",
            description="Get current user's subscription status and trial usage.")
async def get_subscription_status(user: dict = Depends(get_current_user)):
    # PUBLIC_INTERFACE
    """Get subscription status.
    
    Args:
        user: Current authenticated user
        
    Returns:
        Subscription status and trial info
    """
    sub = db.get_subscription(user["id"])
    usage = db.get_usage(user["id"])
    edits_used = usage.get("edits_completed", 0)
    
    if not sub:
        return SubscriptionStatus(
            status="trial",
            trial_remaining=max(0, 10 - edits_used)
        )
    
    return SubscriptionStatus(
        plan=sub["plan"],
        status=sub["status"]
    )

@router.post("/checkout/{plan}", response_model=CheckoutSession,
             summary="Create checkout session",
             description="Create Stripe checkout session for subscription.")
async def create_checkout(
    plan: str,
    request: Request,
    user: dict = Depends(get_current_user)
):
    # PUBLIC_INTERFACE
    """Create Stripe checkout session.
    
    Args:
        plan: Subscription plan (basic/pro)
        request: FastAPI request object
        user: Current authenticated user
        
    Returns:
        Checkout session ID
        
    Raises:
        HTTPException: If plan is invalid
    """
    # Validate plan
    if plan not in ["basic", "pro"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid plan"
        )
    
    price_id = settings.STRIPE_PRICE_BASIC if plan == "basic" else settings.STRIPE_PRICE_PRO
    
    try:
        session = stripe.checkout.Session.create(
            customer_email=user["email"],
            payment_method_types=["card"],
            line_items=[{
                "price": price_id,
                "quantity": 1
            }],
            mode="subscription",
            success_url=f"{settings.SITE_URL}/dashboard?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.SITE_URL}/pricing",
            metadata={
                "user_id": user["id"]
            }
        )
        
        audit_event("checkout_started", user["id"], {
            "plan": plan,
            "session_id": session.id
        })
        
        return CheckoutSession(session_id=session.id)
    
    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/webhook", include_in_schema=False)
async def stripe_webhook(request: Request):
    # Handle Stripe webhooks
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Handle subscription events
    if event.type == "customer.subscription.created":
        subscription = event.data.object
        user_id = subscription.metadata.get("user_id")
        if user_id:
            plan = "basic" if subscription.items.data[0].price.id == settings.STRIPE_PRICE_BASIC else "pro"
            db.set_subscription(
                user_id=user_id,
                plan=plan,
                status="active"
            )
            
            # Send WebSocket notification
            await send_notification(user_id, "subscription_update", {
                "status": "active",
                "plan": plan
            })
            
            audit_event("subscription_created", user_id, {
                "subscription_id": subscription.id,
                "plan": subscription.items.data[0].price.id
            })
    
    elif event.type == "customer.subscription.deleted":
        subscription = event.data.object
        user_id = subscription.metadata.get("user_id")
        if user_id:
            db.set_subscription(
                user_id=user_id,
                plan=None,
                status="cancelled"
            )
            
            # Send WebSocket notification
            await send_notification(user_id, "subscription_update", {
                "status": "cancelled"
            })
            
            audit_event("subscription_cancelled", user_id, {
                "subscription_id": subscription.id
            })
    
    return {"status": "success"}
