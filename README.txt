Stage 8.1 — guest booking bugfix + customer registration

Fixes:
- Fix TypeError: 'bool' object is not callable in guest booking by avoiding shadowing gettext alias `_`.
- Adds independent customer registration at /accounts/register/
- Customer signup fields: full name, phone, password, optional email.
- New customer is logged in for 30 days after signup.
- Adds customer signup entry points on login and guest home.
- No database migration required.

After replacing files:
python manage.py check
python manage.py runserver

If a CSRF 403 remains from a stale page after the previous 500, refresh the booking page once and submit again.
