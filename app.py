"""
Blood Donation Management System (BDMS) - Sargodha
Backend: Python (Flask) + MySQL (XAMPP)

THREE ROLES, each with its own portal:
  admin     -> manages donors, recipients, inventory, requests, appointments, donations, reports
  donor     -> own profile, own donation history, book own appointment
  recipient -> own profile, submit and track own blood requests

Chapter concepts:
  Ch 4  -> normalized tables + foreign keys
  Ch 5  -> indexes (schema.sql)
  Ch 11 -> security  : password hashing, login sessions, role-based access,
                       parameterized queries (SQL-injection safe)
           concurrency: transaction + row locking (SELECT ... FOR UPDATE)
                        when an admin approves a blood request
"""

from flask import (Flask, render_template, request, redirect,
                   url_for, session, flash)
from werkzeug.security import check_password_hash
from functools import wraps
from datetime import date, datetime
import pymysql

app = Flask(__name__)
app.secret_key = "bdms-sargodha-secret-key-2026"

DB = dict(
    host="localhost", user="root", password="", database="bdms",
    cursorclass=pymysql.cursors.DictCursor, autocommit=True,
)
def get_db():
    return pymysql.connect(**DB)

GROUPS = ['A+','A-','B+','B-','AB+','AB-','O+','O-']


# ---------------- ACCESS CONTROL (Chapter 11) ----------------
def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if "user_id" not in session:
                flash("Please log in first.", "error")
                return redirect(url_for("login"))
            if session.get("role") not in roles:
                flash("You don't have access to that page.", "error")
                return redirect(url_for("home"))
            return f(*args, **kwargs)
        return wrapper
    return decorator


# ---------------- LOGIN / LOGOUT ----------------
@app.route("/")
def home():
    role = session.get("role")
    if role == "admin":     return redirect(url_for("dashboard"))
    if role == "donor":     return redirect(url_for("donor_home"))
    if role == "recipient": return redirect(url_for("recipient_home"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        conn = get_db(); cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cur.fetchone(); conn.close()
        if user and check_password_hash(user["password"], password):
            session["user_id"]      = user["user_id"]
            session["username"]     = user["username"]
            session["role"]         = user["role"]
            session["donor_id"]     = user["donor_id"]
            session["recipient_id"] = user["recipient_id"]
            flash("Logged in successfully.", "success")
            return redirect(url_for("home"))
        flash("Wrong username or password.", "error")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


# =====================================================================
#  ADMIN PORTAL
# =====================================================================
@app.route("/dashboard")
@role_required("admin")
def dashboard():
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT COUNT(*) c FROM donor");      donors = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) c FROM recipient");  recipients = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) c FROM blood_unit WHERE status='available'"); available = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) c FROM blood_request WHERE status='pending'"); pending = cur.fetchone()["c"]
    cur.execute("""SELECT blood_group, COUNT(*) units FROM blood_unit
                   WHERE status='available' GROUP BY blood_group ORDER BY blood_group""")
    by_group = cur.fetchall(); conn.close()
    stats = dict(donors=donors, recipients=recipients, available=available, pending=pending)
    return render_template("dashboard.html", stats=stats, by_group=by_group)

# ----- Donors -----
@app.route("/donors")
@role_required("admin")
def donors():
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT * FROM donor ORDER BY donor_id DESC")
    rows = cur.fetchall(); conn.close()
    return render_template("donors.html", donors=rows, groups=GROUPS)

@app.route("/donors/add", methods=["POST"])
@role_required("admin")
def add_donor():
    f = request.form; conn = get_db(); cur = conn.cursor()

    # CHECK 1: donor must be at least 18 years old
    try:
        d = datetime.strptime(f["dob"], "%Y-%m-%d").date()
    except ValueError:
        conn.close(); flash("Invalid date of birth.", "error")
        return redirect(url_for("donors"))
    today = date.today()
    age = today.year - d.year - ((today.month, today.day) < (d.month, d.day))
    if age < 18:
        conn.close(); flash(f"Donor must be at least 18 years old (this person is {age}).", "error")
        return redirect(url_for("donors"))

    # CHECK 3: a person already registered as a recipient cannot be a donor
    cur.execute("SELECT 1 FROM recipient WHERE cnic=%s", (f["cnic"],))
    if cur.fetchone():
        conn.close(); flash("This CNIC is already registered as a recipient. A donor cannot be their own recipient.", "error")
        return redirect(url_for("donors"))

    try:
        cur.execute("""INSERT INTO donor
            (full_name,cnic,gender,dob,blood_group,phone,email,address,city,last_donation_date)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'Sargodha',%s)""",
            (f["full_name"], f["cnic"], f["gender"], f["dob"], f["blood_group"],
             f["phone"], f.get("email") or None, f["address"], f.get("last_donation_date") or None))
        flash("Donor added.", "success")
    except pymysql.err.IntegrityError:
        flash("That CNIC already exists.", "error")
    except pymysql.err.OperationalError as e:
        flash(str(e.args[1]) if len(e.args) > 1 else "Could not add donor.", "error")
    conn.close(); return redirect(url_for("donors"))

@app.route("/donors/delete/<int:donor_id>", methods=["POST"])
@role_required("admin")
def delete_donor(donor_id):
    conn = get_db(); cur = conn.cursor()
    cur.execute("DELETE FROM donor WHERE donor_id=%s", (donor_id,))
    conn.close(); flash("Donor deleted.", "success")
    return redirect(url_for("donors"))

# ----- Recipients -----
@app.route("/recipients")
@role_required("admin")
def recipients():
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT * FROM recipient ORDER BY recipient_id DESC")
    rows = cur.fetchall(); conn.close()
    return render_template("recipients.html", recipients=rows, groups=GROUPS)

@app.route("/recipients/add", methods=["POST"])
@role_required("admin")
def add_recipient():
    f = request.form; conn = get_db(); cur = conn.cursor()

    # CHECK 3: a person already registered as a donor cannot be a recipient
    cur.execute("SELECT 1 FROM donor WHERE cnic=%s", (f["cnic"],))
    if cur.fetchone():
        conn.close(); flash("This CNIC is already registered as a donor. A donor cannot be their own recipient.", "error")
        return redirect(url_for("recipients"))

    try:
        cur.execute("""INSERT INTO recipient
            (full_name,cnic,gender,dob,blood_group,phone,email,address,city)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'Sargodha')""",
            (f["full_name"], f["cnic"], f["gender"], f["dob"], f["blood_group"],
             f["phone"], f.get("email") or None, f["address"]))
        flash("Recipient added.", "success")
    except pymysql.err.IntegrityError:
        flash("That CNIC already exists.", "error")
    except pymysql.err.OperationalError as e:
        flash(str(e.args[1]) if len(e.args) > 1 else "Could not add recipient.", "error")
    conn.close(); return redirect(url_for("recipients"))

@app.route("/recipients/delete/<int:recipient_id>", methods=["POST"])
@role_required("admin")
def delete_recipient(recipient_id):
    conn = get_db(); cur = conn.cursor()
    cur.execute("DELETE FROM recipient WHERE recipient_id=%s", (recipient_id,))
    conn.close(); flash("Recipient deleted.", "success")
    return redirect(url_for("recipients"))

# ----- Inventory -----
@app.route("/inventory")
@role_required("admin")
def inventory():
    group = request.args.get("group", "")
    conn = get_db(); cur = conn.cursor()
    base = """SELECT u.*, b.bank_name, d.full_name donor_name
              FROM blood_unit u
              JOIN blood_bank b ON u.bank_id=b.bank_id
              LEFT JOIN donor d ON u.donor_id=d.donor_id"""
    if group:
        cur.execute(base + " WHERE u.blood_group=%s ORDER BY u.unit_id DESC", (group,))
    else:
        cur.execute(base + " ORDER BY u.unit_id DESC")
    units = cur.fetchall()
    cur.execute("SELECT bank_id,bank_name FROM blood_bank ORDER BY bank_name")
    banks = cur.fetchall(); conn.close()
    return render_template("inventory.html", units=units, banks=banks, group=group, groups=GROUPS)

@app.route("/inventory/add", methods=["POST"])
@role_required("admin")
def add_unit():
    f = request.form; conn = get_db(); cur = conn.cursor()
    cur.execute("""INSERT INTO blood_unit (blood_group,bank_id,status,collected_date)
                   VALUES (%s,%s,'available',%s)""",
                (f["blood_group"], f["bank_id"], f["collected_date"]))
    conn.close(); flash("Blood unit added to inventory.", "success")
    return redirect(url_for("inventory"))

# ----- Requests (admin sees all; approve = concurrency demo) -----
@app.route("/requests")
@role_required("admin")
def requests_page():
    conn = get_db(); cur = conn.cursor()
    cur.execute("""SELECT r.*, h.hospital_name FROM blood_request r
                   JOIN hospital h ON r.hospital_id=h.hospital_id
                   ORDER BY r.request_id DESC""")
    rows = cur.fetchall(); conn.close()
    return render_template("requests.html", requests=rows)

@app.route("/requests/approve/<int:request_id>", methods=["POST"])
@role_required("admin")
def approve_request(request_id):
    """CHAPTER 11 - TRANSACTION + ROW LOCKING.
    Reserve a unit AND approve the request together (atomic). FOR UPDATE locks
    the chosen unit so two admins cannot grab the same one."""
    conn = get_db(); conn.autocommit(False); cur = conn.cursor()
    try:
        cur.execute("SELECT blood_group FROM blood_request WHERE request_id=%s", (request_id,))
        req = cur.fetchone()
        if not req:
            conn.rollback(); flash("Request not found.", "error")
            return redirect(url_for("requests_page"))
        cur.execute("""SELECT unit_id FROM blood_unit
                       WHERE blood_group=%s AND status='available'
                       ORDER BY collected_date ASC LIMIT 1 FOR UPDATE""", (req["blood_group"],))
        unit = cur.fetchone()
        if not unit:
            conn.rollback()
            flash(f"No available {req['blood_group']} unit in stock.", "error")
            return redirect(url_for("requests_page"))
        cur.execute("UPDATE blood_unit SET status='reserved' WHERE unit_id=%s", (unit["unit_id"],))
        cur.execute("UPDATE blood_request SET status='approved' WHERE request_id=%s", (request_id,))
        conn.commit()
        flash(f"Request approved. {req['blood_group']} unit reserved.", "success")
    except Exception:
        conn.rollback(); flash("Something went wrong, request not approved.", "error")
    finally:
        conn.autocommit(True); conn.close()
    return redirect(url_for("requests_page"))

@app.route("/requests/reject/<int:request_id>", methods=["POST"])
@role_required("admin")
def reject_request(request_id):
    conn = get_db(); cur = conn.cursor()
    cur.execute("UPDATE blood_request SET status='rejected' WHERE request_id=%s", (request_id,))
    conn.close(); flash("Request rejected.", "success")
    return redirect(url_for("requests_page"))

# ----- Appointments (admin sees all) -----
@app.route("/appointments")
@role_required("admin")
def appointments():
    conn = get_db(); cur = conn.cursor()
    cur.execute("""SELECT a.*, d.full_name, b.bank_name FROM appointment a
                   JOIN donor d ON a.donor_id=d.donor_id
                   JOIN blood_bank b ON a.bank_id=b.bank_id
                   ORDER BY a.appointment_date DESC""")
    rows = cur.fetchall(); conn.close()
    return render_template("appointments.html", appointments=rows)

# ----- Donations (admin records; transaction adds stock too) -----
@app.route("/donations")
@role_required("admin")
def donations():
    conn = get_db(); cur = conn.cursor()
    cur.execute("""SELECT dh.*, d.full_name, b.bank_name FROM donation_history dh
                   JOIN donor d ON dh.donor_id=d.donor_id
                   JOIN blood_bank b ON dh.bank_id=b.bank_id
                   ORDER BY dh.donation_date DESC""")
    rows = cur.fetchall()
    cur.execute("SELECT donor_id,full_name,blood_group FROM donor ORDER BY full_name")
    donor_list = cur.fetchall()
    cur.execute("SELECT bank_id,bank_name FROM blood_bank ORDER BY bank_name")
    banks = cur.fetchall(); conn.close()
    return render_template("donations.html", donations=rows, donor_list=donor_list, banks=banks)

@app.route("/donations/add", methods=["POST"])
@role_required("admin")
def add_donation():
    f = request.form; conn = get_db(); cur = conn.cursor()

    # CHECK 2: a donor must wait at least 2 months between donations
    cur.execute("""SELECT MAX(donation_date) AS last,
                          (%s < DATE_ADD(MAX(donation_date), INTERVAL 2 MONTH)) AS too_soon
                   FROM donation_history WHERE donor_id=%s""",
                (f["donation_date"], f["donor_id"]))
    chk = cur.fetchone()
    if chk and chk["too_soon"] == 1:
        conn.close()
        flash(f"This donor last donated on {chk['last']}. A donor must wait 2 months between donations.", "error")
        return redirect(url_for("donations"))

    conn.autocommit(False)
    try:
        cur.execute("SELECT blood_group FROM donor WHERE donor_id=%s", (f["donor_id"],))
        bg = cur.fetchone()["blood_group"]
        cur.execute("""INSERT INTO donation_history (donor_id,bank_id,donation_date,blood_group,units)
                       VALUES (%s,%s,%s,%s,1)""", (f["donor_id"], f["bank_id"], f["donation_date"], bg))
        cur.execute("""INSERT INTO blood_unit (blood_group,bank_id,donor_id,status,collected_date)
                       VALUES (%s,%s,%s,'available',%s)""", (bg, f["bank_id"], f["donor_id"], f["donation_date"]))
        cur.execute("UPDATE donor SET last_donation_date=%s WHERE donor_id=%s", (f["donation_date"], f["donor_id"]))
        conn.commit(); flash("Donation recorded and added to inventory.", "success")
    except Exception:
        conn.rollback(); flash("Could not record donation.", "error")
    finally:
        conn.autocommit(True); conn.close()
    return redirect(url_for("donations"))

# ----- Reports -----
@app.route("/reports")
@role_required("admin")
def reports():
    conn = get_db(); cur = conn.cursor()
    cur.execute("""SELECT blood_group,
                     SUM(status='available') available,
                     SUM(status='reserved')  reserved,
                     SUM(status='used')      used,
                     COUNT(*) total
                   FROM blood_unit GROUP BY blood_group ORDER BY blood_group""")
    stock = cur.fetchall()
    cur.execute("SELECT blood_group, COUNT(*) donors FROM donor GROUP BY blood_group ORDER BY blood_group")
    donor_groups = cur.fetchall(); conn.close()
    return render_template("reports.html", stock=stock, donor_groups=donor_groups)


# =====================================================================
#  DONOR PORTAL
# =====================================================================
@app.route("/donor")
@role_required("donor")
def donor_home():
    did = session["donor_id"]; conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT * FROM donor WHERE donor_id=%s", (did,)); me = cur.fetchone()
    cur.execute("SELECT COUNT(*) c FROM donation_history WHERE donor_id=%s", (did,)); total = cur.fetchone()["c"]
    cur.execute("""SELECT a.appointment_date, b.bank_name FROM appointment a
                   JOIN blood_bank b ON a.bank_id=b.bank_id
                   WHERE a.donor_id=%s AND a.status='scheduled' AND a.appointment_date>=CURDATE()
                   ORDER BY a.appointment_date ASC LIMIT 1""", (did,))
    nxt = cur.fetchone(); conn.close()
    return render_template("donor_home.html", me=me, total=total, nxt=nxt)

@app.route("/donor/profile")
@role_required("donor")
def donor_profile():
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT * FROM donor WHERE donor_id=%s", (session["donor_id"],))
    me = cur.fetchone(); conn.close()
    return render_template("donor_profile.html", me=me)

@app.route("/donor/donations")
@role_required("donor")
def donor_donations():
    conn = get_db(); cur = conn.cursor()
    cur.execute("""SELECT dh.*, b.bank_name FROM donation_history dh
                   JOIN blood_bank b ON dh.bank_id=b.bank_id
                   WHERE dh.donor_id=%s ORDER BY dh.donation_date DESC""", (session["donor_id"],))
    rows = cur.fetchall(); conn.close()
    return render_template("donor_donations.html", donations=rows)

@app.route("/donor/book", methods=["GET", "POST"])
@role_required("donor")
def donor_book():
    did = session["donor_id"]; conn = get_db(); cur = conn.cursor()
    if request.method == "POST":
        cur.execute("""INSERT INTO appointment (donor_id,bank_id,appointment_date,status)
                       VALUES (%s,%s,%s,'scheduled')""",
                    (did, request.form["bank_id"], request.form["appointment_date"]))
        flash("Appointment booked.", "success")
        conn.close(); return redirect(url_for("donor_book"))
    cur.execute("SELECT bank_id,bank_name FROM blood_bank ORDER BY bank_name"); banks = cur.fetchall()
    cur.execute("""SELECT a.*, b.bank_name FROM appointment a
                   JOIN blood_bank b ON a.bank_id=b.bank_id
                   WHERE a.donor_id=%s ORDER BY a.appointment_date DESC""", (did,))
    appts = cur.fetchall(); conn.close()
    return render_template("donor_book.html", banks=banks, appointments=appts)


# =====================================================================
#  RECIPIENT PORTAL
# =====================================================================
@app.route("/recipient")
@role_required("recipient")
def recipient_home():
    rid = session["recipient_id"]; conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT * FROM recipient WHERE recipient_id=%s", (rid,)); me = cur.fetchone()
    cur.execute("SELECT COUNT(*) c FROM blood_request WHERE recipient_id=%s", (rid,)); total = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) c FROM blood_request WHERE recipient_id=%s AND status='pending'", (rid,)); pending = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) c FROM blood_unit WHERE blood_group=%s AND status='available'", (me["blood_group"],)); avail = cur.fetchone()["c"]
    conn.close()
    return render_template("recipient_home.html", me=me, total=total, pending=pending, avail=avail)

@app.route("/recipient/profile")
@role_required("recipient")
def recipient_profile():
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT * FROM recipient WHERE recipient_id=%s", (session["recipient_id"],))
    me = cur.fetchone(); conn.close()
    return render_template("recipient_profile.html", me=me)

@app.route("/recipient/requests", methods=["GET", "POST"])
@role_required("recipient")
def recipient_requests():
    rid = session["recipient_id"]; conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT * FROM recipient WHERE recipient_id=%s", (rid,)); me = cur.fetchone()
    if request.method == "POST":
        cur.execute("""INSERT INTO blood_request
                       (recipient_id,hospital_id,patient_name,blood_group,units_required,status,request_date)
                       VALUES (%s,%s,%s,%s,%s,'pending',CURDATE())""",
                    (rid, request.form["hospital_id"], me["full_name"],
                     me["blood_group"], request.form["units_required"]))
        flash("Blood request submitted.", "success")
        conn.close(); return redirect(url_for("recipient_requests"))
    cur.execute("SELECT hospital_id,hospital_name FROM hospital ORDER BY hospital_name"); hospitals = cur.fetchall()
    cur.execute("""SELECT r.*, h.hospital_name FROM blood_request r
                   JOIN hospital h ON r.hospital_id=h.hospital_id
                   WHERE r.recipient_id=%s ORDER BY r.request_id DESC""", (rid,))
    rows = cur.fetchall(); conn.close()
    return render_template("recipient_requests.html", me=me, hospitals=hospitals, requests=rows)


if __name__ == "__main__":
    app.run(debug=True)
