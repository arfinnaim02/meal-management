# Mess Meal Manager

This is a complete plug‑and‑play Django project for managing meals and expenses in a shared mess (household). It focuses on meal tracking and financial calculations for bachelors in Bangladesh but can be adapted for any context.

## Features

* **User registration and authentication** – users can sign up, log in and out.
* **Mess management** – each user owns a mess; super admins can add members, record expenses and deposits, adjust breakfast rules and assign meal managers.
* **Meal tracking** – record breakfasts, lunches, dinners and extra meals per member per day. Meal managers can only edit meals within their assigned dates.
* **Meal manager assignments** – super admins can assign any user to manage meals for 1–4 weeks, 15 or 30 days, or custom ranges. The dashboard summarizes how many days each person has managed meals.
* **Dashboard** – interactive overview showing meal rate, total meals, expenses, collections, balance, per‑member dues/advances and manager duty stats.
* **Modern UI** – Tailwind CSS is used via CDN to provide a clean, mobile‑friendly interface.

## Getting Started

1. **Install dependencies**:

    ```sh
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

2. **Run migrations**:

    ```sh
    python manage.py migrate
    ```

3. **Create a superuser (optional)**:

    ```sh
    python manage.py createsuperuser
    ```

4. **Start the development server**:

    ```sh
    python manage.py runserver
    ```

5. **Sign up**: Open `http://localhost:8000/register/` in your browser and create a new account. The system automatically creates a mess for you and assigns you as super admin.

6. **Use the app**:
   * Add members from the **Members** tab.
   * Use **Meals** to record daily meals.
   * Add **Expenses** and **Deposits** to track finances.
   * Use **Meal Managers** to assign responsibility for meal entry to others.
   * Adjust breakfast rules in **Settings**.

## Customization

* **Multi‑mess support** – although each user can create one mess by default, the underlying data model supports multiple messes per user. Adjust the registration flow if you need to support multiple messes per account.
* **Currency** – the `Mess.currency` field can be changed to reflect other currencies (default is BDT).
* **Extending the model** – you can add fixed expenses (rent, utilities) and incorporate them into the cost calculation.

## License

This project is provided as is without any warranty. You are free to modify and distribute it for personal or commercial use.