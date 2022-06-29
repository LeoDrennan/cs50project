import os
import math

from cs50 import SQL
from flask import flash, redirect, render_template, session
from functools import wraps
from itsdangerous import URLSafeTimedSerializer, SignatureExpired

# Secret key for serializer
s = URLSafeTimedSerializer(os.environ["SECRET_KEY"])

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///food.db")


def login_required(destination):
    """
    Decorate routes to require login.

    https://pythonise.com/series/learning-flask/custom-flask-decorators
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if session.get("user_id") is None:
                return redirect(f"/login{destination}")
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def login_required_plus(destination):
    """
    Decorate routes to require login for dynamic routes.

    https://pythonise.com/series/learning-flask/custom-flask-decorators
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(url, *args, **kwargs):
            if session.get("user_id") is None:
                return redirect(f"/login{destination}{url}")
            return f(url, *args, **kwargs)
        return decorated_function
    return decorator


def reauth_required(destination):
    """
    Decorate routes to require reauthentication.

    https://pythonise.com/series/learning-flask/custom-flask-decorators
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                s.loads(session.get("token"), salt="access", max_age=600)
            except SignatureExpired:
                return redirect(f"/reauthenticate/{destination}")
            else:
                return f(*args, **kwargs)
        return decorated_function
    return decorator


def verification_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("verified") == False:
            flash("You must verify your email address to access this feature. Please follow the instructions below.")
            return redirect("/verify_request")
        else:
            return f(*args, **kwargs)
    return decorated_function


def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def product_info(basket):
    """Find product information from database and append desired quantity"""

    # Create a list of product ids for the basket contents
    items = []
    for b in basket:
        items.append(b["product_id"])

    # Execute query
    contents = db.execute("SELECT * FROM products WHERE id IN (?)", items)

    # Append quantity to database output
    for i in range(len(contents)):
        for j in range(len(basket)):
            if contents[i]["id"] == basket[j]["product_id"]:
                contents[i]["quantity"] = basket[j]["quantity"]

    # Return product information
    return (contents)


def basket_total(contents):
    """Given an input shopping basket return total cost"""
    total_cost = 0
    for content in contents:
        sub_total = content["quantity"] * content["price"]
        total_cost += sub_total
    return total_cost


def gbp(value):
    """Format value as GBP."""
    return f"£{value:,.2f}"


def concatenate(first_name, last_name):
    """ Format name for post and comment authors """

    author = first_name + " " + last_name
    return author


def last_interaction(difference):
    """ Format datetime difference to string format for blog (e.g. "2 days ago") """

    # Determine if timedelta object is datetime or time
    days = False
    diff_str = str(difference)
    for i in range(len(diff_str)):
        if diff_str[i] == ",":
            days = True
            break

    # If input is datetime convert days to string
    if days == True:
        total_days = ""
        for i in range(len(diff_str)):
            if diff_str[i] == " ":
                break
            else:
                total_days += diff_str[i]
        days_int = int(total_days)
        statement = date_string(days_int)
        return statement

    # If input is time only convert time to string
    else:
        diff_sec = int(difference.total_seconds())
        statement = time_string(diff_sec)
        return statement


def date_string(days):
    """ Convert days to weeks, months, or years """

    if days >= 730:
        years = math.floor(days/365)
        statement = f"Over {years} years ago"
    elif days >= 365:
        statement = "Over 1 year ago"
    elif days >= 60:
        months = math.floor(days/30)
        statement = f"Over {months} months ago"
    elif days >= 28:
        statement = "Over 1 month ago"
    elif days >= 14:
        weeks = math.floor(days/7)
        statement = f"Over {weeks} weeks ago"
    elif days >= 7:
        statement = "Over 1 week ago"
    elif days != 1:
        statement = f"Over {days} days ago"
    else:
        statement = "Over 1 day ago"

    return statement


def time_string(time):
    """ Convert time object to seconds, minutes, or hours """

    if time >= 7200:
        hours = math.floor(time/3600)
        statement = f"Over {hours} hours ago"
    elif time >= 3600:
        statement = "Over 1 hour ago"
    elif time >= 120:
        minutes = math.floor(time/60)
        statement = f"Over {minutes} minutes ago"
    elif time >= 60:
        statement = "Over 1 minute ago"
    else:
        statement = "A few seconds ago"

    return statement


def average_rating(product_id):
    """ Find the new average rating for the product in question """

    rows = db.execute("SELECT rating FROM reviews WHERE product_id = ?", product_id)
    length = len(rows)

    if length == 0:
        return(0)

    else:
        total = 0
        for row in rows:
            total += row["rating"]

        avg = round((total / length), 1)
        return(avg)


def censor_number(card_number):
    """ Censor credit card number for invoices """

    length = len(card_number)
    censored = "*" * (length - 4) + card_number[length-4:length]
    return censored


def credit(card_num):
    """ Validate credit card number"""

    # Start Lunh's algorithm calculation
    x = math.floor(card_num / 10)
    sum1 = 0

    # Loop through card number for first half of calculation
    while x > 0:
        digit = x % 10
        x = math.floor(x / 100)
        digit *= 2

        if digit > 9:
            digit1 = digit % 10
            digit2 = math.floor(digit / 10)
            digit = digit1 + digit2

        sum1 += digit

    y = card_num
    sum2 = 0

    # Loop through card number for second half of calculation
    while y > 0:
        digit = y % 10
        y = math.floor(y / 100)
        sum2 += digit

    # Add both values together to finish Lunh's Algorithm
    total = sum1 + sum2

    # Store end number for validation
    end = total % 10

    # Find length of number by converting to a string
    s = str(card_num)
    length = len(s)

    # Find the two digit prefix of the card number
    # Store the first digit for VISA check
    prefix_str = s[0] + s[1]
    prefix = int(prefix_str)
    prefix_visa = int(s[0])

    # Check conditions
    if end != 0:
        return("INVALID")

    elif length == 15 and (prefix == 34 or prefix == 37):
        return("AMEX")

    elif length == 16 and (prefix >= 51 and prefix <= 55):
        return("MASTERCARD")

    elif (length == 13 or length == 16) and prefix_visa == 4:
        return("VISA")

    else:
        return("INVALID")