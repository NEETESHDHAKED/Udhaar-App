from flask import Flask, render_template, request, redirect
import json, os
from datetime import date
import urllib.parse

app = Flask(__name__)
FILE = "kirana.json"

def load():
    if os.path.exists(FILE):
        try:
            with open(FILE) as f:
                data = json.load(f)
                for i, c in enumerate(data):
                    c["id"] = i
                    if "khata" not in c: c["khata"] = []
                    if "total" not in c: c["total"] = 0
                    if "photo" not in c: c["photo"] = ""
                return data
        except: return []
    return []

def save(d):
    for c in d:
        if "id" in c: del c["id"]
    with open(FILE,"w") as f:
        json.dump(d,f)

@app.route("/")
def home():
    customers = load()
    q = request.args.get("q","")
    search_result = []
    if q:
        search_result = [c for c in customers if q.lower() in c['name'].lower() or q in c['phone']]
    total_udhaar = sum(int(c['total']) for c in customers)
    # Top defaulter
    sorted_c = sorted(customers, key=lambda x: int(x['total']), reverse=True)
    top = sorted_c[:3] if sorted_c else []
    today_udhaar = 0
    today_jama = 0
    today_str = str(date.today())
    for c in customers:
        for k in c.get("khata",[]):
            if k["date"] == today_str:
                if k["type"]=="UDHAAR": today_udhaar+=int(k["amount"])
                else: today_jama+=int(k["amount"])
    return render_template("kirana.html", customers=customers, search_result=search_result, q=q, total_udhaar=total_udhaar, total_customers=len(customers), top=top, today_udhaar=today_udhaar, today_jama=today_jama)

@app.route("/add", methods=["POST"])
def add():
    c = load()
    c.append({"name": request.form["name"], "phone": request.form["phone"], "photo": request.form.get("photo",""), "total":0, "khata":[]})
    save(c)
    return redirect("/")

@app.route("/delete/<int:id>")
def delete(id):
    c = load()
    if id < len(c): c.pop(id); save(c)
    return redirect("/")

@app.route("/customer/<int:id>")
def customer(id):
    all_c = load()
    if id >= len(all_c): return redirect("/")
    c = all_c[id]
    # WhatsApp msg ready
    msg = f"Namaste {c['name']} ji 🙏 Sharma Kirana Store se - Aapka total udhaar ₹{c['total']} baki hai. Kripya jald jama kar de. Dhanyawad!"
    wa_link = "https://wa.me/91" + c['phone'] + "?text=" + urllib.parse.quote(msg)
    return render_template("customer.html", c=c, id=id, wa_link=wa_link)

@app.route("/udhaar/<int:id>", methods=["POST"])
def udhaar(id):
    c = load()
    amount = int(request.form["amount"])
    c[id]["khata"].append({"date": str(date.today()), "item": request.form["item"], "type":"UDHAAR", "amount": amount})
    c[id]["total"] = int(c[id]["total"]) + amount
    save(c)
    return redirect(f"/customer/{id}")

@app.route("/jama/<int:id>", methods=["POST"])
def jama(id):
    c = load()
    amount = int(request.form["amount"])
    c[id]["khata"].append({"date": str(date.today()), "item":"JAMA - Paise Diye", "type":"JAMA", "amount": amount})
    c[id]["total"] = int(c[id]["total"]) - amount
    save(c)
    return redirect(f"/customer/{id}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
