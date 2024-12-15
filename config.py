
global_user = None
last_history_id = None

def set_a_global_user(user):
    """
    Sets the global user instance.

    Args:
        user: The user instance to set as the global user.
    """
    global global_user
    global_user = user

def get_global_user():
    """Returns the global user instance."""
    return global_user


def set_last_history_id(new_value):
    global last_history_id
    last_history_id = new_value
    print(f"Set last_history_id to: {new_value}")

def get_last_history_id():
    return last_history_id
