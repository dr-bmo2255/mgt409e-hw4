"""API checks against the local backend (no paid calls; creates one throwaway local account).
Run from hw4/ with the backend running:  backend/.venv/bin/python scripts/api_test.py
 Prints PASS/FAIL lines and a JSON summary."""
import json, secrets, sys
import httpx

B = "http://localhost:8000"
results = []


def check(name, ok, detail=""):
    results.append({"name": name, "ok": bool(ok), "detail": str(detail)[:200]})
    print(("PASS " if ok else "FAIL ") + name + (f"  ({detail})" if detail and not ok else ""))


c = httpx.Client(base_url=B, timeout=30)
h = c.get("/api/health").json()
check("health ok", h.get("status") == "ok", h)
check("health 102 products", h.get("products") == 102, h.get("products"))

prods = c.get("/api/products").json()
check("products list 102", len(prods) == 102, len(prods))
check("every product has an image", all(p.get("image_url") for p in prods))
mism = []
for p in prods:
    d = c.get(f"/api/products/{p['product_id']}").json()
    if sum(s["quantity"] for s in d.get("inventory", [])) != p["total_stock"]:
        mism.append(p["product_id"])
check("all 102 detail pages: size stock adds up to total_stock", not mism, mism[:5])
check("every product has a Dan image", all(p.get("dan") for p in prods), sum(1 for p in prods if not p.get("dan")))
cats = c.get("/api/categories").json()
check("categories non-empty", len(cats) > 0, len(cats))

# images reachable (sample: every product photo + every colorway + every Dan image used)
urls = set()
for p in prods:
    urls.add(p["image_url"])
    urls.update((p.get("color_images") or {}).values())
    urls.add(p["dan"]["image_url"]); urls.add(p["dan"]["thumb_url"])
for d in ["welcome_dan", "avatar_dan"] + [f"rival_{r}" for r in "harvard princeton brown columbia cornell dartmouth penn".split()] \
        + [f"dan_{y}s" for y in range(1920, 2030, 10)]:
    urls.add(f"/media/dan/{d}.webp")
bad = [u for u in sorted(urls) if c.get(u).status_code != 200]
check(f"all {len(urls)} images load", not bad, bad[:5])

one = c.get("/api/products/champion-full-zip-hood")
check("product detail 200", one.status_code == 200)
check("unknown product 404", c.get("/api/products/nope-nope").status_code == 404)
check("Problem 2 fixes applied", "Vision blocked" not in json.dumps(prods))

# deep links served by the SPA in dev are Vite's job; here check API catalogue search
q = c.get("/api/products", params={"q": "hoodie"}).json()
check("search 'hoodie' returns results", len(q) > 0, len(q))

# custom gear
cp = c.get("/api/custom/products").json()
check("custom products 7", len(cp.get("products", [])) == 7, len(cp.get("products", [])))
st = c.get("/api/custom/status").json()
check("custom status reports mode", "mock" in st, st)

# guest: server bag empty, adding custom gear needs sign-in
check("guest bag empty", c.get("/api/bag").json().get("count") == 0)
r = c.post("/api/bag", json={"product_key": cp["products"][0]["key"], "design_ref": "starter:welcome_dan", "size": "M", "quantity": 1})
check("guest can't add custom gear (401)", r.status_code == 401, r.status_code)
check("guest chat history empty/401", c.get("/api/chat/history").status_code in (200, 401))

# auth round trip with a throwaway local test account
email = f"sitetest+{secrets.token_hex(4)}@example.test"
pw = "T3st-" + secrets.token_urlsafe(10)
r = c.post("/api/auth/signup", json={"first_name": "Site", "last_name": "Test", "email": email, "password": pw, "confirm_password": pw})
check("signup 201", r.status_code == 201, r.text)
check("me after signup", (c.get("/api/auth/me").json().get("user") or {}).get("email") == email)
r = c.post("/api/auth/signup", json={"first_name": "Site", "last_name": "Test", "email": email, "password": pw, "confirm_password": pw})
check("duplicate signup 409", r.status_code == 409, r.status_code)
c.post("/api/auth/logout")
check("logged out", not c.get("/api/auth/me").json().get("user"))
check("wrong password 401", c.post("/api/auth/login", json={"email": email, "password": "wrong"}).status_code == 401)
r = c.post("/api/auth/login", json={"email": email, "password": pw})
check("login 200", r.status_code == 200, r.status_code)

# signed in: custom bag add / qty / remove
key = cp["products"][0]["key"]
size = cp["products"][0]["sizes"][0]
r = c.post("/api/bag", json={"product_key": key, "design_ref": "starter:welcome_dan", "size": size, "quantity": 2})
check("signed-in custom bag add", r.status_code == 201 and r.json()["count"] == 2, r.text)
item = r.json()["items"][0]["id"]
check("bag qty update", c.patch(f"/api/bag/{item}", json={"quantity": 3}).json()["count"] == 3)
check("bag remove", c.delete(f"/api/bag/{item}").json()["count"] == 0)
check("bad size rejected 422", c.post("/api/bag", json={"product_key": key, "design_ref": "starter:welcome_dan", "size": "XXXXL", "quantity": 1}).status_code == 422)
check("designs list", c.get("/api/custom/designs").status_code == 200)
c.post("/api/auth/logout")

ok = sum(r["ok"] for r in results)
print(json.dumps({"passed": ok, "total": len(results), "failed": [r for r in results if not r["ok"]]}, indent=1))
sys.exit(0 if ok == len(results) else 1)
