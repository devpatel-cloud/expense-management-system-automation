from ..models import Category


DEFAULT_CATEGORIES = [
    {"name": "Food", "icon": "utensils", "color": "#ef4444"},
    {"name": "Shopping", "icon": "shopping-bag", "color": "#8b5cf6"},
    {"name": "Transport", "icon": "car", "color": "#3b82f6"},
    {"name": "Bills", "icon": "receipt", "color": "#f59e0b"},
    {"name": "Health", "icon": "heart-pulse", "color": "#10b981"},
    {"name": "Entertainment", "icon": "film", "color": "#ec4899"},
    {"name": "Travel", "icon": "plane", "color": "#06b6d4"},
    {"name": "Other", "icon": "circle-dot", "color": "#64748b"},
]


def create_default_categories(db, user_id: int) -> None:
    for category in DEFAULT_CATEGORIES:
        db.add(Category(user_id=user_id, is_default=True, **category))
