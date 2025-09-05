import httpx
from typing import List, Optional
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ..services.db import db
from ..settings import settings
from ..utils.audit import audit_event
from ..utils.security import get_current_user
from ..utils.storage import generate_result_path
from .websocket import send_notification

router = APIRouter()

class EditRequest(BaseModel):
    prompt: str = Field(..., description="Natural language edit request")

class EditResponse(BaseModel):
    id: str = Field(..., description="Edit request ID")
    image_id: str = Field(..., description="Source image ID")
    prompt: str = Field(..., description="Edit prompt")
    status: str = Field(..., description="Processing status")
    result_path: Optional[str] = Field(None, description="Path to result image if complete")
    created_at: str = Field(..., description="Request timestamp")
    updated_at: str = Field(..., description="Last update timestamp")

async def process_edit(user_id: str, edit_id: str, image_path: str, prompt: str):
    """Background task to process edit via Google Nano Banana API."""
    try:
        # Call Google Nano Banana API
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.GOOGLE_NANO_BANANA_API_URL}/enhance",
                headers={"Authorization": f"Bearer {settings.GOOGLE_NANO_BANANA_API_KEY}"},
                files={"image": open(image_path, "rb")},
                data={"prompt": prompt}
            )
            response.raise_for_status()
            result = response.json()
            
            # Download result image
            result_url = result["image_url"]
            img_response = await client.get(result_url)
            img_response.raise_for_status()
            
            # Save result image
            abs_path, rel_path = generate_result_path("enhanced.jpg")
            with open(abs_path, "wb") as f:
                f.write(img_response.content)
            
            # Update edit record
            db.update_edit(edit_id, status="completed", result_path=rel_path)
            
            # Send WebSocket notification
            await send_notification(user_id, "edit_status", {
                "edit_id": edit_id,
                "status": "completed",
                "result_path": rel_path
            })
            
            # Track usage and check trial status
            usage = db.increment_usage(user_id, "edits_completed")
            
            # Check if user is on trial and running low on credits
            sub = db.get_subscription(user_id)
            if not sub and usage >= 8:  # Alert when 2 or fewer trial edits remain
                await send_notification(user_id, "usage_alert", {
                    "message": "You have only 2 trial edits remaining. Subscribe to continue using the service.",
                    "remaining": 10 - usage
                })
            
            audit_event("edit_completed", user_id, {
                "edit_id": edit_id,
                "image_path": rel_path
            })
    
    except Exception as e:
        db.update_edit(edit_id, status="failed")
        await send_notification(user_id, "edit_status", {
            "edit_id": edit_id,
            "status": "failed",
            "error": str(e)
        })
        audit_event("edit_failed", user_id, {
            "edit_id": edit_id,
            "error": str(e)
        })

@router.post("/{image_id}", response_model=EditResponse,
             summary="Request image edit",
             description="Submit a natural language edit request for an image.")
async def create_edit(
    image_id: str,
    edit: EditRequest,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user)
):
    # PUBLIC_INTERFACE
    """Create new edit request.
    
    Args:
        image_id: ID of image to edit
        edit: Edit request details
        background_tasks: FastAPI background tasks
        user: Current authenticated user
        
    Returns:
        Edit request details
        
    Raises:
        HTTPException: If image not found or user exceeded quota
    """
    # Verify image exists and user owns it
    image = db.get_image(user["id"], image_id)
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )
    
    # Create edit record
    edit_record = db.create_edit(user["id"], image_id, edit.prompt)
    
    # Queue background processing
    background_tasks.add_task(
        process_edit,
        user["id"],
        edit_record["id"],
        image["path"],
        edit.prompt
    )
    
    audit_event("edit_requested", user["id"], {
        "edit_id": edit_record["id"],
        "image_id": image_id,
        "prompt": edit.prompt
    })
    
    return EditResponse(**edit_record)

@router.get("/{image_id}/list", response_model=List[EditResponse],
            summary="List image edits",
            description="List all edit requests for an image.")
async def list_edits(
    image_id: str,
    user: dict = Depends(get_current_user)
):
    # PUBLIC_INTERFACE
    """List edits for an image.
    
    Args:
        image_id: ID of image to get edits for
        user: Current authenticated user
        
    Returns:
        List of edit requests
        
    Raises:
        HTTPException: If image not found
    """
    # Verify image exists and user owns it
    if not db.get_image(user["id"], image_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )
    
    edits = db.list_edits_for_image(user["id"], image_id)
    return [EditResponse(**edit) for edit in edits]
