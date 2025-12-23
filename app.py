import asyncio
import httpx
import json
from fastapi import FastAPI, HTTPException
from datetime import datetime, timedelta

# -----------------------
# إعدادات API
# -----------------------
app = FastAPI(title="Ultra-Fast Spammer", description="API to send friend requests at maximum speed")

# -----------------------
# تحميل الحسابات من ملف JSON
# -----------------------
def load_accounts():
    try:
        with open("accounts.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("Error: accounts.json not found. Please create it.")
        return {}
    except json.JSONDecodeError:
        print("Error: accounts.json is not a valid JSON file.")
        return {}

SPAM_TOKENS = load_accounts()

# -----------------------
# تخزين مؤقت لمعمومات اللاعبين
# -----------------------
PLAYER_INFO_CACHE = {}

# -----------------------
# دالة للتحقق من معلومات اللاعب (بكاش)
# -----------------------
async def get_player_info(uid: str):
    if uid in PLAYER_INFO_CACHE:
        cached_data = PLAYER_INFO_CACHE[uid]
        if datetime.now() - cached_data['timestamp'] < timedelta(minutes=5):
            return cached_data['info']

    api_url = f"https://ff-api-anis.onrender.com/check?uid={uid}"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(api_url)
            if response.status_code == 200:
                info = response.json()
                PLAYER_INFO_CACHE[uid] = {'info': info, 'timestamp': datetime.now()}
                return info
            return None
    except:
        return None

# -----------------------
# دالة لإرسال طلب صداقة واحد (سريعة وخفيفة)
# -----------------------
async def send_one_request(uid: str, password: str, target_uid: str, client: httpx.AsyncClient):
    api_url = "https://anis-add-remove-api.onrender.com/add_friend"
    params = {"uid": uid, "password": password, "player_id": target_uid}
    try:
        # لا ننتظر الرد، فقط أرسل الطلب
        await client.get(api_url, params=params, timeout=5)
        return True
    except:
        return False

# -----------------------
# نقاط نهاية API (Endpoints)
# -----------------------
@app.route('/ping')
def ping():
    return jsonify({"status": "alive"}), 200
@app.get("/")
async def root():
    return {"message": "Ultra-Fast Spammer is running"}

@app.get("/spam")
async def spam_friend_requests(uid: str):
    if not uid:
        raise HTTPException(status_code=400, detail="uid parameter is required")

    if not SPAM_TOKENS:
        raise HTTPException(status_code=503, detail="No accounts loaded. Check accounts.json file.")

    print(f"🚀 Starting ultra-fast spam on uid: {uid} with {len(SPAM_TOKENS)} accounts.")

    # إنشاء عميل HTTP واحد
    async with httpx.AsyncClient(timeout=10) as client:
        # إرسال جميع الطلبات في نفس اللحظة
        tasks = [
            send_one_request(acc_uid, acc_pw, uid, client)
            for acc_uid, acc_pw in SPAM_TOKENS.items()
        ]
        # نستخدم return_exceptions=False لنجعل gather يتوقف عند أول خطأ،
        # ولكن بما أن دالتنا تُرجع True/False ولا تطلق استثناء، فهذا آمن وسريع.
        results = await asyncio.gather(*tasks)
        
    successful_count = sum(1 for result in results if result)
    print(f"✅ Spamming finished. {successful_count}/{len(SPAM_TOKENS)} requests were sent.")

    # جلب معلومات اللاعب
    player_info = await get_player_info(uid)

    # بناء الرسالة المختصرة
    if player_info and player_info.get("name"):
        player_name = player_info.get("name")
        player_level = player_info.get("level", "N/A")
        response_message = f"success - {player_name} - Level {player_level}"
    else:
        response_message = f"success - UID: {uid}"

    return {
        "status": "success",
        "message": response_message
    }

@app.get("/add_friend")
async def add_friend_single(uid: str, password: str, player_id: str):
    if not uid or not password or not player_id:
        raise HTTPException(status_code=400, detail="uid, password, and player_id are required")
    
    async with httpx.AsyncClient(timeout=30) as client:
        success = await send_one_request(uid, password, player_id, client)
    
    return {"status": "success" if success else "failed"}

@app.post("/accounts")
async def update_accounts(accounts: dict):
    global SPAM_TOKENS
    SPAM_TOKENS = accounts
    return {"status": "success", "message": "Accounts updated", "total": len(accounts)}

@app.get("/accounts")
async def get_accounts():
    return SPAM_TOKENS

# -----------------------
# تشغيل الخادم
# -----------------------
if __name__ == "__main__":

    uvicorn.run(app, host="0.0.0.0", port=8000)

