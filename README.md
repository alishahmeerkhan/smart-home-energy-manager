# ⚡ Flux: Smart Energy Dashboard

Flux is a full-stack web application designed to help homeowners track their energy usage, manage smart appliances, and set monthly utility budgets.

## 🛠️ Tech Stack
* **Backend:** Python (Flask)
* **Database:** Oracle Database (cx_Oracle/oracledb)
* **Frontend:** HTML5, CSS3 (Flexbox/Grid), Jinja2 Templating
* **Architecture:** Separation of Concerns (Routing vs. DB Logic)

## ✨ Key Features
* **Secure Authentication:** Session-based user logins.
* **Live Dashboard:** Monitors 24-hour hourly usage charts.
* **Smart Device Management:** Add appliances by wattage, and assign them to specific rooms.
* **Budget Tracking:** Set and update monthly financial limits.
* **Relational Integrity:** Utilizes Oracle `ON DELETE CASCADE` and strict Foreign Key constraints to ensure data purity when removing devices or homes.

## 🚀 How to Run Locally
1. Clone the repository.
2. Install the required Python packages:
   `pip install flask oracledb`
3. Update the `database.py` file with your Oracle DB credentials (`DB_USER`, `DB_PASS`, `DB_DSN`).
4. Run the Flask server:
   `python main.py`
5. Open your browser and navigate to `http://localhost:5000`.
