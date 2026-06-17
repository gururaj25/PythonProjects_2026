from send2trash import send2trash

def safe_delete(path):
    try:
        send2trash(path)
        return True
    except Exception:
        return False