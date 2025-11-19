import pandas as pd
import bcrypt
import random

NUM_USERS = 5000
SEED = 42   # <-- reproducibility seed

random.seed(SEED)

ADJECTIVES = [
    "Ancient", "Apex", "Arcane", "Atomic", "Binary", "Blazing", "Blue", "Brave",
    "Bright", "Burning", "Chaotic", "Clever", "Cosmic", "Cracked", "Crimson",
    "Cyber", "Darkened", "Deathless", "Desert", "Dire", "Dusty", "Electric",
    "Emerald", "Encrypted", "Eternal", "Faint", "Fatal", "Feral", "Frozen",
    "Fractured", "Fuzzy", "Galactic", "Gentle", "Glacial", "Golden", "Grim",
    "Hardcore", "Hollow", "Infernal", "Iron", "Legendary", "Lucky", "Majestic",
    "Metallic", "Mystic", "Mythic", "Neon", "Nimble", "Nocturnal", "Nuclear",
    "Obliterated", "Obsidian", "Oceanic", "Omega", "Overclocked", "Phantom",
    "Pixelated", "Prime", "Quantum", "Radiant", "Radiated", "Rapid", "Rogue",
    "Royal", "Ruthless", "Savage", "Scarlet", "Shadow", "Shadowed", "Shiny",
    "Silent", "Silver", "Sinister", "Solar", "Spectral", "Stealth", "Stealthy",
    "Stormforged", "Stormy", "Swift", "Thunderous", "Toxic", "Turbocharged",
    "Ultra", "Undead", "Vibrant", "Viral", "Vortex", "Wild"
]

VERBS = [
    # 100 verbs (same list as earlier)
    "Runner","Jumper","Walker","Coder","Rider","Charger","Hunter","Thinker",
    "Builder","Wanderer","Pilot","Striker","Wizard","Guardian","Dancer",
    "Breaker","Seeker","Reader","Fighter","Crafter","Smasher","Painter","Gamer",
    "Singer","Climber","Ranger","Tinkerer","Shaper","Warrior","Ravager",
    "Scholar","Explorer","Miner","Diver","Sailor","Hacker","Lurker","Keeper",
    "Maker","Founder","Invoker","Caster","Ripper","Drifter","Nomad","Harvester",
    "Sprinter","Glider","Brawler","Crusher","Slicer","Sharpshooter","Defender",
    "Artist","Prowler","Sculptor","Prodigy","Champion","Overseer","Scout",
    "Stormbringer","Tamer","Reaper","Reaver","Voyager","Navigator","Fletcher",
    "Tensor","Bruiser","Laser","Tracker","Handler","Pioneer","Spinner","Forger",
    "Wielder","Operator","Chaser","Stalker","Warden","Lancer","Monitor",
    "Scrapper","Sniper","Recycler","Commander","Architect","Sentry","Observer",
    "Herald"
]

def generate_username():
    adj = random.choice(ADJECTIVES)
    verb = random.choice(VERBS)
    num = random.randint(1000, 9999)
    return f"{adj}{verb}{num}"

def generate_users():
    # password = "password"
    PASSWORD_HASH = bcrypt.hashpw("password".encode(), bcrypt.gensalt()).decode()

    print(f"[INFO] Using password hash: {PASSWORD_HASH}")

    users = []

    for uid in range(1, NUM_USERS + 1):
        user_id = f"{uid:04d}"
        username = generate_username()

        users.append({
            "userId": user_id,
            "username": username,
            "email": f"{username.lower()}@example.com",
            "name": f"User {user_id}",
            "bio": f"This is user {user_id}",
            "passwordHash": PASSWORD_HASH
        })

        if uid % 100 == 0:
            print(f"[INFO] Created {uid} users so far...")

    pd.DataFrame(users).to_csv("users.csv", index=False)
    print("[OK] users.csv generated.")

if __name__ == "__main__":
    generate_users()
