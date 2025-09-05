from typing import Dict, Any, Optional, List
import uuid
from datetime import datetime


class InMemoryDB:
    """Temporary in-memory store to mimic DatabaseService interactions."""

    def __init__(self):
        self.users: Dict[str, Dict[str, Any]] = {}
        self.images: Dict[str, Dict[str, Any]] = {}
        self.edits: Dict[str, Dict[str, Any]] = {}
        self.subscriptions: Dict[str, Dict[str, Any]] = {}
        self.usage: Dict[str, Dict[str, int]] = {}

    # Users
    def create_user(self, email: str, hashed_password: str) -> Dict[str, Any]:
        user_id = str(uuid.uuid4())
        record = {
            "id": user_id,
            "email": email.lower(),
            "password": hashed_password,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "role": "user",
            "profile": {},
        }
        self.users[user_id] = record
        return record

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        email = email.lower()
        for u in self.users.values():
            if u["email"] == email:
                return u
        return None

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        return self.users.get(user_id)

    # Images
    def create_image(self, user_id: str, filename: str, path: str, mime: str) -> Dict[str, Any]:
        img_id = str(uuid.uuid4())
        rec = {
            "id": img_id,
            "user_id": user_id,
            "filename": filename,
            "path": path,
            "mime": mime,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "status": "uploaded",
        }
        self.images[img_id] = rec
        return rec

    def list_images(self, user_id: str) -> List[Dict[str, Any]]:
        return [i for i in self.images.values() if i["user_id"] == user_id]

    def get_image(self, user_id: str, image_id: str) -> Optional[Dict[str, Any]]:
        img = self.images.get(image_id)
        if img and img["user_id"] == user_id:
            return img
        return None

    # Edits
    def create_edit(self, user_id: str, image_id: str, prompt: str) -> Dict[str, Any]:
        edit_id = str(uuid.uuid4())
        rec = {
            "id": edit_id,
            "user_id": user_id,
            "image_id": image_id,
            "prompt": prompt,
            "status": "queued",
            "result_path": None,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z",
        }
        self.edits[edit_id] = rec
        return rec

    def get_edit(self, user_id: str, edit_id: str) -> Optional[Dict[str, Any]]:
        ed = self.edits.get(edit_id)
        if ed and ed["user_id"] == user_id:
            return ed
        return None

    def update_edit(self, edit_id: str, **fields) -> Optional[Dict[str, Any]]:
        ed = self.edits.get(edit_id)
        if not ed:
            return None
        ed.update(fields)
        ed["updated_at"] = datetime.utcnow().isoformat() + "Z"
        return ed

    def list_edits_for_image(self, user_id: str, image_id: str) -> List[Dict[str, Any]]:
        return [e for e in self.edits.values() if e["user_id"] == user_id and e["image_id"] == image_id]

    # Subscriptions & Usage
    def set_subscription(self, user_id: str, plan: str, status: str) -> Dict[str, Any]:
        rec = {"user_id": user_id, "plan": plan, "status": status}
        self.subscriptions[user_id] = rec
        return rec

    def get_subscription(self, user_id: str) -> Optional[Dict[str, Any]]:
        return self.subscriptions.get(user_id)

    def increment_usage(self, user_id: str, metric: str, amount: int = 1) -> int:
        if user_id not in self.usage:
            self.usage[user_id] = {}
        self.usage[user_id][metric] = self.usage[user_id].get(metric, 0) + amount
        return self.usage[user_id][metric]

    def get_usage(self, user_id: str) -> Dict[str, int]:
        return self.usage.get(user_id, {})


# Singleton in-memory DB for this template
db = InMemoryDB()
