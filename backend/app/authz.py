from functools import wraps
from flask import jsonify
from flask_login import current_user


def roles_required(*allowed_roles):
    """Protect an API route using the signed-in user's role."""
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({"error": "Authentication required"}), 401
            if not current_user.active:
                return jsonify({"error": "Account is inactive"}), 403
            if current_user.role not in allowed_roles:
                return jsonify({"error": "You do not have permission to access this resource"}), 403
            return view(*args, **kwargs)
        return wrapped
    return decorator
