# Blood Donation Management System (BDMS) — Sargodha

A working web app: **MySQL** database + **Python (Flask)** backend + **HTML/CSS** light-mode interface.
**Three separate roles**, each with its own login, menu, and pages: **Admin, Donor, Recipient**.

---

## HOW TO RUN (do this once)

### 1. Load the database
1. Open **XAMPP** → Start **Apache** and **MySQL**.
2. Go to **http://localhost/phpmyadmin**
3. Click **Import** → choose **schema.sql** → **Go**.
   (If a `bdms` database already exists from before, this replaces it — that's fine.)

### 2. Install Python libraries
1. Open the **bdms** folder in **VS Code**.
2. Terminal → New Terminal → run:
   ```
   pip install -r requirements.txt
   ```

### 3. Start the app
```
python app.py
```
Then open **http://127.0.0.1:5000**

### Logins
| Role      | Username | Password   | What they can do                                        |
|-----------|----------|------------|---------------------------------------------------------|
| Admin     | admin    | admin123   | Manage donors, recipients, inventory, requests, reports |
| Donor     | ahmed    | ahmed123   | See own profile + donation history, book appointment    |
| Recipient | imran    | imran123   | Submit and track own blood requests                     |

(Other accounts: donor `fatima`/`fatima123`, recipient `saima`/`saima123`.)

To stop the app: **Ctrl + C** in the terminal.

---

## THE THREE ROLES (for your viva)

**Admin** logs in → full control panel: add/delete donors and recipients,
add blood units, approve/reject requests, record donations, view reports.

**Donor** logs in → personal portal: their profile, their donation history,
and a page to book their own donation appointment.

**Recipient** logs in → personal portal: submit a blood request (their blood
group fills in automatically) and track the status of their requests.

This matches the **Donor** and **Recipient** entities in your ER diagram — they
are separate tables (`donor`, `recipient`) and separate logins, not mixed together.

---

## WHICH CHAPTER IS PROVEN WHERE

**Chapter 2 / 3 — ER & EER diagram**
9 tables from your ERD/EERD: donor, recipient, blood_bank, hospital, blood_unit,
blood_request, appointment, donation_history, users. The `users` table with a
`role` column (admin/donor/recipient) reflects the supertype/subtype idea.
`blood_request` links a **recipient** to a **hospital** (associative relationship).

**Chapter 4 — Normalization**
Every table is in 3NF and connected through **foreign keys** (see every `FOREIGN KEY`).

**Chapter 5 — Physical design**
**Indexes** on the most-searched columns (blood_group, status) — see `CREATE INDEX`.

**Chapter 11 — Security**
- Passwords are **hashed** (pbkdf2), never plain text — look at the `users` table.
- **Login sessions** + **role-based access**: `role_required("admin"/"donor"/"recipient")` in `app.py`.
- Every query uses **parameterized queries** (`%s`) → safe from **SQL injection**.

**Chapter 11 — Concurrency (star feature)**
Admin clicks **Approve** on a request → `approve_request()` in `app.py`:
- runs inside a **transaction** (autocommit off → COMMIT / ROLLBACK),
- uses **`SELECT ... FOR UPDATE`** to **lock** a blood unit so two admins can't take the same one,
- reserves the unit and approves the request **together** = **ACID atomicity**.

---

## If something breaks
- *"Access denied for user root"* → your MySQL has a password. In `app.py` put it inside `password=""`.
- *"Unknown database bdms"* → import schema.sql (Step 1).
- *"No module named flask/pymysql"* → run `pip install -r requirements.txt`.
- Page looks unstyled → keep the `static` folder next to `app.py`.
