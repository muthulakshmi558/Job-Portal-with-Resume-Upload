from django.core.exceptions import PermissionDenied

def user_is_employer(user):
    return hasattr(user, 'profile') and user.profile.role == 'employer'
