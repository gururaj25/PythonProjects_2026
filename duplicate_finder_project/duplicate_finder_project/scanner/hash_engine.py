import hashlib

CHUNK_SIZE = 65536

def calculate_hash(file_path, algorithm="sha256"):
    hasher = hashlib.new(algorithm)

    try:
        with open(file_path, "rb") as f:
            while chunk := f.read(CHUNK_SIZE):
                hasher.update(chunk)

        return hasher.hexdigest()

    except Exception:
        return None