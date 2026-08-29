import base64
import hashlib
import json
import random
from datetime import datetime, timezone

def generate_proof_token(required: bool, seed: str = "", difficulty: str = "", user_agent: str | None = None) -> str | None:
    if not required:
        return None
    
    screen = random.choice([3008, 4010, 6000]) * random.choice([1, 2, 4])
    parse_time = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
    proof = [
        screen, parse_time, None, 0, user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "https://tcr9i.chat.openai.com/v2/35536E1E-65B4-4D96-9D97-6ADB7EFF8147/api.js",
        "dpl=1440a687921de39ff5ee56b92807faaadce73f13",
        "en", "en-US", None, "plugins−[object PluginArray]",
        random.choice(["_reactListeningcfilawjnerp", "_reactListening9ne2dfo1i47"]),
        random.choice(["alert", "ontransitionend", "onprogress"]),
    ]
    
    diff_len = len(difficulty)
    for attempt in range(100000):
        proof[3] = attempt
        proof_json = json.dumps(proof, separators=(",", ":"))
        proof_base = base64.b64encode(proof_json.encode()).decode()
        hash_value = hashlib.sha3_512((seed + proof_base).encode()).hexdigest()
        if hash_value[:diff_len] <= difficulty:
            return "gAAAAAB" + proof_base

    return None
