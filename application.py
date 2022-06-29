import os

from cs50 import SQL
from flask import Flask, Markup, flash, redirect, jsonify, render_template, url_for, request, session
from flask_session import Session
from flask_mail import Mail, Message
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from datetime import datetime
from random import sample

from helpers import login_required, login_required_plus, reauth_required, verification_required, apology, product_info, basket_total, gbp, concatenate, last_interaction, average_rating, censor_number, credit

# Configure application
app = Flask(__name__)

# Secret key for serializer
s = URLSafeTimedSerializer(os.environ["SECRET_KEY"])

# Custom filter
app.jinja_env.filters["gbp"] = gbp

# Configure mail server
app.config["MAIL_DEFAULT_SENDER"] = os.environ["MAIL_USERNAME"]
app.config["MAIL_PASSWORD"] = os.environ["MAIL_PASSWORD"]
app.config["MAIL_PORT"] = 587
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.environ["MAIL_USERNAME"]
mail = Mail(app)

# Ensure templates are auto-reloaded
app.config["TEMPLATE_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///food.db")


@app.route("/")
def index():
    """ Homepage """

    # Randomise 3 products for shop showcase
    items = db.execute("SELECT id FROM products WHERE stock > 0")
    random_items = sample(items, 3)
    products_list = []
    for i in range(len(random_items)):
        products_list.append(random_items[i]["id"])

    # Star rating display
    products = db.execute("SELECT * FROM products WHERE id IN (?)", products_list)
    for product in products:
        product["rounded_rating"] = int((round(product["avg_rating"]* 2) / 2) * 10)

    return render_template("index.html", products=products)

@app.route("/login", defaults={'destination': None, 'optional': None}, methods=["GET","POST"])
@app.route("/login/<destination>", defaults={'optional': None}, methods=["GET","POST"])
@app.route("/login/<destination>/<optional>", methods=["GET","POST"])
def login(destination, optional):
    """ Log user in """

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("email"):
            return apology("must provide email address", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for email address
        rows = db.execute("SELECT * FROM users WHERE email = ?", request.form.get("email"))

        # Ensure that the user exists and that the password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Create access token for the user
        token = s.dumps(request.form.get("email"), salt="access")

        # Store user specific session variables
        session["user_id"] = rows[0]["id"]
        session["name"] = rows[0]["first_name"]
        session["token"] = token

        # Check if user is verified
        check = db.execute("SELECT verified FROM users WHERE id = ?", session["user_id"])[0]["verified"]

        # Create appropriate session variable and message
        if check == 1:
            session["verified"] = True
            flash(f'Welcome back {session["name"]}.')
        else:
            session["verified"] = False
            flash(Markup('Please verify your email address. Check your email or click <a href="/verify_request">here</a> for a new link.'))

        # If user was forced to login return them to old page
        if destination and optional:
            return redirect(f"/{destination}/{optional}")
        elif destination:
            return redirect(f"/{destination}")

        # Take user to homepage
        else:
            return redirect("/")

    # User reached route via GET
    else:

        # Return destination for links with dynamic urls (forced login)
        if destination and optional:
            return render_template("account/login.html", destination=destination, optional=optional)

        # Return destination for regular links (forced login)
        elif destination:
            return render_template("account/login.html", destination=destination)

        # Regular login (user clicked login)
        else:
            return render_template("account/login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/login")

@app.route("/register", defaults={'destination': None, 'optional': None}, methods=["GET","POST"])
@app.route("/register/<destination>", defaults={'optional': None}, methods=["GET","POST"])
@app.route("/register/<destination>/<optional>", methods=["GET","POST"])
def register(destination, optional):
    """ Register a new user """

    #Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure full name has been entered
        if not request.form.get("first_name") or not request.form.get("last_name"):
            return apology("please provide your name in full", 400)

        # Ensure valid email address was submitted
        if not request.form.get("email"):
            return apology("must provide valid email address", 400)

        # Ensure password was submitted
        if not request.form.get("password"):
            return apology("must provide a password", 400)

        # Check password has been confirmed
        if not request.form.get("password") == request.form.get("confirm"):
            return apology("password does not match", 400)

        # Check to see if email address in already in use
        rows = db.execute("SELECT * FROM users WHERE email = ?", request.form.get("email"))

        # If query returns any rows, email is already in use
        if len(rows) != 0:
            return apology("an account is already registered to this email address", 400)

        # Otherwise create an account for the user
        email = request.form.get("email")

        # Generate a hash for the provided password
        password_hash = generate_password_hash(request.form.get("password"))

        # Insert new user into the database
        db.execute("INSERT INTO users (email, hash, first_name, last_name) VALUES (?, ?, ?, ?)", email, password_hash, request.form.get("first_name"), request.form.get("last_name"))

        # Create access token for the user
        access_token = s.dumps(request.form.get("email"), salt="access")

        # Log user in
        rows = db.execute("SELECT id, first_name FROM users WHERE email = ?", email)
        session["user_id"] = rows[0]["id"]
        session["name"] = rows[0]["first_name"]
        session["token"] = access_token
        session["verified"] = False

        # Create unique token for email verification
        token = s.dumps(email, salt="email_verify")

        # Send email verification message
        msg = Message("Budget Eats: Email Verification", recipients=[email])
        link_suffix = url_for("verify", token=token)
        link = os.environ["URL_PREFIX"] + link_suffix
        msg.body = f"Your email verification link is {link}"
        mail.send(msg)

        # Inform user of successful register and prompt them to verify email
        flash(f'Welcome {session["name"]}. Please check your email address for a verification email.')

        # Return user to page they came from if relevant
        if destination and optional:
            return redirect(f"/{destination}/{optional}")
        elif destination:
            return redirect(f"/{destination}")
        else:
            return redirect("/")

    # User reached route via GET
    else:

        # Return destination for links with dynamic urls (forced login)
        if destination and optional:
            return render_template("account/register.html", destination=destination, optional=optional)

        # Return destination for regular links (forced login)
        elif destination:
            return render_template("account/register.html", destination=destination)

        # Regular login (user clicked login)
        else:
            return render_template("account/register.html")


@app.route("/verify/<token>")
def verify(token):
    """ Destination for email verification links """

    # Obtain email back from token
    try:
        email = s.loads(token, salt="email_verify", max_age=3600)

    # Prompt user to request another token if time limit is exceeded
    except SignatureExpired:

        # Inform user of expired token
        flash("This verification link has expired. Please log in and request a new link.")
        return redirect("/")

    # If token is still valid verify the user
    else:
        db.execute("UPDATE users SET verified = 1 WHERE email = ?", email)
        if "user_id" in session:
            session["verified"] = True

        # Inform user of successful email verification
        flash("Your email address has now been verified and you have full access to website facilities.")
        return redirect("/")


@app.route("/verify_request", methods=["GET","POST"])
@login_required("/verify_request")
def verify_request():
    """ Prompt unverified users to verify or resend verification email """

    # Resend verification email to user
    if request.method == "POST":

        # Query for users email
        email = db.execute("SELECT email FROM users WHERE id = ?", session["user_id"])[0]["email"]

        # Create unique token for email verification
        token = s.dumps(email, salt="email_verify")

        # Send email verification message
        msg = Message("Budget Eats: Email Verification", recipients=[email])
        link_suffix = url_for("verify", token=token)
        link = os.environ["URL_PREFIX"] + link_suffix
        msg.body = f"Your email verification link is {link}"
        mail.send(msg)

        # Inform user that new verification email has been sent
        flash("A new verification email has been sent to your email address.")
        return redirect("/")

    # Route reached via GET
    else:
        return render_template("account/verify_prompt.html")


@app.route("/reset_request", methods=["GET","POST"])
def reset_request():
    """ Request password reset to be sent to an email address """

    # Form submission via POST
    if request.method == "POST":

        email = request.form.get("email")
        rows = db.execute("SELECT * FROM users WHERE email = ?", email)

        # Check that a user exists with the email provided
        if len(rows) != 1:
            flash("No account registered to email address provided.")
            return redirect("/reset_request")

        # Generate token for password reset link
        token = s.dumps(email, salt="pass_reset")

        # Send email with password reset link
        msg = Message("Budget Eats: Password Reset", recipients=[email])
        link_suffix = url_for("reset", token=token)
        link = os.environ["URL_PREFIX"] + link_suffix
        msg.body = f"Your password reset link is {link}"
        mail.send(msg)

        # Inform user of successful reset request
        flash("Password reset link has been sent to the provided address.")
        return redirect("/login")

    # User reached route via GET
    else:
        return render_template("account/reset_request.html")


@app.route("/reset/<token>", methods=["GET","POST"])
def reset(token):
    """ Destination for password reset links"""

    # Form submission via POST
    if request.method == "POST":

        # Obtain email back from token
        email = s.loads(token, salt="pass_reset")

        # Check new password matches
        if not request.form.get("new_pass") == request.form.get("new_pass_confirm"):
            return apology("Passwords do not match")

        # Generate new password hash and store
        new_hash = generate_password_hash(request.form.get("new_pass"))
        db.execute("UPDATE users SET hash = ? WHERE email = ?", new_hash, email)

        # Send the user an email informing them of the password change
        msg = Message("Budget Eats: Your password has been changed", recipients=[email])
        msg.body = "Your password was recently changed."
        mail.send(msg)

        # Inform user that password reset has been successful
        flash("Your password has successfully been reset. Please login to access website features.")
        return redirect("/login")

    # User route reached via GET
    else:

        # Obtain email back from token
        try:
            email = s.loads(token, salt="pass_reset", max_age=3600)

        # If token is expired prompt user to request another
        except SignatureExpired:
            flash("Your password reset token has expired. Please request another.")
            return redirect("/reset_request")

        # If token is still valid render password change form
        else:
            return render_template("account/reset.html", token=token)


@app.route("/account")
@login_required("/account")
@reauth_required("account")
def account():
    """ Account hub """

    return render_template("account/account.html")


@app.route("/reauthenticate/<url>", methods=["GET","POST"])
@login_required_plus("/reauthenticate/")
def reautheticate(destination):
    """ Re-enter account information for account security """

    # Post request
    if request.method == "POST":

        # Ensure valid email address was submitted
        if not request.form.get("email"):
            return apology("must provide valid email address", 400)

        # Ensure password was submitted
        if not request.form.get("password"):
            return apology("must provide a password", 400)

        # Query database for email address
        rows = db.execute("SELECT * FROM users WHERE email = ?", request.form.get("email"))

        # Ensure that the user exists and that the password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Issue another 10 minute token
        session["token"] = s.dumps(request.form.get("email"), salt="access")

        return redirect(f"/{destination}")

    # User reached route via GET
    else:
        return render_template("account/reauth.html", destination=destination)


@app.route("/password_change", methods=["GET","POST"])
@login_required("/password_change")
@reauth_required("password_change")
def password_change():
    """ Change password from account hub """

    # If form is submitted via POST
    if request.method == "POST":

        # Check that current password has been entered correctly
        rows = db.execute("SELECT email, hash FROM users where id = ?", session["user_id"])
        if not check_password_hash(rows[0]["hash"], request.form.get("current_pass_confirm")):
            return apology("incorrect current password")

        # Check that new passwords match
        if not request.form.get("new_pass") == request.form.get("new_pass_confirm"):
            return apology("new password must be entered twice correctly")

        # If all information is valid hash the new password and store
        new_hash = generate_password_hash(request.form.get("new_pass"))
        db.execute("UPDATE users SET hash = ? WHERE id = ?", new_hash, session["user_id"])

        # Send email informing of password change for security
        email = rows[0]["email"]
        msg = Message("Budget Eats: Your password has been changed", recipients=[email])
        msg.body = "Your password has been changed."
        mail.send(msg)

        # Inform user that password has been successfully changed
        flash("Your password has been successfully changed.")
        return redirect("/account")

    # User reached route via GET
    else:
        return render_template("account/password_change.html")


@app.route("/email_change", methods=["GET","POST"])
@login_required("/email_change")
@reauth_required("email_change")
def email_change():
    """ Request email change from account hub """

    # If form is submitted via POST
    if request.method == "POST":

        # Check that all fields have been filled
        if not request.form.get("email") or not request.form.get("email_confirm") or not request.form.get("password"):
            return apology("please fill in all required fields")

        # Check email matches
        if not request.form.get("email") == request.form.get("email_confirm"):
            return apology("email does not match")

        # Check for null character (could interfere with further validation)
        for c in request.form.get("email"):
            if c == "\0":
                return apology("invalid email address")

        # Check that password has been entered correctly
        rows = db.execute("SELECT hash FROM users WHERE id = ?", session["user_id"])
        if not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("incorrect password")

        # Create token containing both old and new email adresses
        old_email = db.execute("SELECT email FROM users WHERE id = ?", session["user_id"])
        new_email = request.form.get("email")
        email_string = old_email[0]["email"] + "\0" + new_email
        token = s.dumps(email_string, salt="email_change")

        # Send email to proposed new email address
        msg = Message("Budget Eats: Email change request", recipients=[new_email])
        link_suffix = url_for("email_changed", token=token)
        link = os.environ["URL_PREFIX"] + link_suffix
        msg.body = f"Please follow the link to complete your email change: {link}"
        mail.send(msg)

        # Instruct the user on how to complete the email change
        flash("An email has been sent to the desired address, please follow the link provided to complete the switch.")
        return redirect("/account")

    # User reached route via GET
    else:
        return render_template("account/email_change.html")


@app.route("/email_changed/<token>")
def email_changed(token):
    """ Complete email change """

    # Get both old and new email back from the token
    email_string = s.loads(token, salt="email_change")
    x = email_string.partition("\0")
    old_email = x[0]
    new_email = x[2]

    # Complete email change in database
    db.execute("UPDATE users SET email = ? WHERE email = ?", new_email, old_email)

    # Send email to old email address for security purposes
    msg = Message("Budget Eats: Email Changed", recipients=[old_email])
    msg.body = "Your email has been changed. If this was not you, please contact our support."
    mail.send(msg)

    # Inform user of completed change
    flash("Your email address has been successfully changed.")
    return redirect("/account")


@app.route("/my_preferences")
@login_required("/my_preferences")
def my_preferences():
    """ Allow user to review their current dietary preferences """

    # Query for users dietary preferences
    row = db.execute("SELECT vegan, vegetarian FROM preferences WHERE user_id = ?", session["user_id"])[0]

    if row["vegetarian"] == 1:
        diet = "Vegetarian"
    elif row["vegan"] == 1:
        diet = "Vegan"
    else:
        diet = "None"

    # Query for meal volume
    preferences = db.execute("SELECT meals, people FROM preferences WHERE user_id = ?", session["user_id"])[0]

    # Query for any allergies the user has flagged
    allergens = db.execute("SELECT allergen FROM allergens WHERE id IN (SELECT allergen_id FROM users_allergens WHERE user_id = ?)", session["user_id"])

    # Display all preferences data
    return render_template("account/my_preferences.html", diet=diet, allergens=allergens, preferences=preferences)


@app.route("/quote_change", methods=["GET","POST"])
@login_required("/quote_change")
def quote_change():
    """ Change the number of servings per week """

    # Form submitted via POST
    if request.method == "POST":

        # Check to see if user already has a preferences profile
        check = db.execute("SELECT * FROM preferences WHERE user_id = ?", session["user_id"])

        # If profile exists update with new values
        if len(check) != 0:
            db.execute("UPDATE preferences SET people = ?, meals = ? WHERE user_id = ?", request.form.get("people"), request.form.get("meals"), session["user_id"])

        # If not create new entry into preferences table
        else:
            db.execute("INSERT INTO preferences (user_id, people, meals) VALUES (?, ?, ?)", session["user_id"], request.form.get("people"), request.form.get("meals"))

        # Continue to next stage
        return redirect("/preferences_change")

    # Route reached via GET
    else:

        # Check if user is revisiting page
        check = db.execute("SELECT * FROM preferences WHERE user_id = ?", session["user_id"])

        # If user is revisiting the page load their current preferences on the sliders
        if len(check) != 0 and (check[0]["people"] and check[0]["meals"]) is not None:
            cost = check[0]["people"] * check[0]["meals"] * 3
            return render_template("account/quote.html", people=check[0]["people"], meals=check[0]["meals"], cost=cost)

        # If this is the first time use default values
        else:
            return render_template("account/quote.html")


@app.route("/preferences_change", methods=["GET","POST"])
@login_required("/preferences_change")
def preferences_change():
    """ Change the dietary and allergy preferences attached to the account """

    # Form submitted via POST
    if request.method == "POST":

        # Get dietary preferences from form
        if request.form.get("dietary") == "vegetarian":
            vegetarian = 1
            vegan = 0
        elif request.form.get("dietary") == "vegan":
            vegetarian = 0
            vegan = 1
        else:
            vegetarian = vegan = 0

        # Update database with relevant information
        db.execute("UPDATE preferences SET vegetarian = ?, vegan = ? WHERE user_id = ?", vegetarian, vegan, session["user_id"])

        # Store all allergy information in the user profile
        allergens = db.execute("SELECT * FROM allergens")

        # Iterate through each allergen
        for allergen in allergens:

            # If allergen is selected
            if request.form.get(f'{allergen["allergen"]}') != None:
                check = db.execute("SELECT * FROM users_allergens WHERE user_id = ? AND allergen_id = ?", session["user_id"], allergen["id"])

                # If allergen is not already recorded in users_allergen table create a new entry
                if len(check) == 0:
                    db.execute("INSERT INTO users_allergens (user_id, allergen_id) VALUES (?, ?)", session["user_id"], allergen["id"])

            # If allergen is not selected
            else:
                check = db.execute("SELECT * FROM users_allergens WHERE user_id = ? AND allergen_id = ?", session["user_id"], allergen["id"])
                # If allergen was previously selected, remove entry in table
                if len(check) != 0:
                    db.execute("DELETE FROM users_allergens WHERE user_id = ? AND allergen_id = ?", session["user_id"], allergen["id"])

        # Inform user of successfully updated preferences
        flash("Your preferences have been updated.")
        return redirect("/my_preferences")


    # Route reached via GET
    else:

        allergens = db.execute("SELECT allergen FROM allergens")
        return render_template("account/preferences.html", allergens=allergens)


@app.route("/shop", methods=["GET","POST"])
def shop():
    """Display products for sale"""

    # POST request via buy now
    if request.method ==  "POST":

        # Ensure shopping basket exists
        if "basket" not in session:
            session["basket"] = []

        # Create basket entry
        id = int(request.form.get("id"))
        entry = {
            "product_id": id,
            "quantity": 1
        }
        if entry:
            session["basket"].append(entry)

        return redirect("/basket")

    # User reached route via GET
    else:
        products = db.execute("SELECT * FROM products")
        for product in products:
            product["rounded_rating"] = int((round(product["avg_rating"]* 2) / 2) * 10)

        return render_template("shop/shop.html", products=products)


@app.route("/shop/<product_id>", methods=["GET","POST"])
def product(product_id):
    """Page with product specific information"""

    # Add to basket or delete review via POST
    if request.method == "POST":

        # Add to basket
        if request.form.get("type") == "add":

            # Ensure user is logged in
            if "user_id" not in session:
                return redirect(f"/login/shop/{product_id}")

            # Ensure shopping basket exists
            if "basket" not in session:
                session["basket"] = []

            # Store response from form
            item_id = int(request.form.get("id"))
            item_quantity = int(request.form.get("quantity"))
            product_name = db.execute("SELECT name FROM products WHERE id = ?", item_id)[0]["name"]

            # If basket contains selected item already, add the new quantity
            for i in range(len(session["basket"])):
                if session["basket"][i]["product_id"] == item_id:
                    session["basket"][i]["quantity"] += item_quantity
                    flash(Markup(f'Quantity of {product_name} has been updated for your <a href="/basket">basket</a>.'))
                    return redirect("/shop")

            # Create dictionary entry for required amount
            entry = {
                "product_id": item_id,
                "quantity": item_quantity
            }

            # Store dict in session
            if entry:
                session["basket"].append(entry)

            # Redirect user to continue browsing
            flash(Markup(f'{product_name} has been added to your <a href="/basket">basket</a>.'))
            return redirect("/shop")

        # Delete review
        if request.form.get("type") == "delete":

            review_id = request.form.get("review_id")
            db.execute("DELETE FROM reviews WHERE id = ?", review_id)

            avg = average_rating(product_id)
            db.execute("UPDATE products SET avg_rating = ? WHERE id = ?", avg, product_id)

            flash("You have successfully deleted your review for this product.")
            return redirect(f"/shop/{product_id}")


    # User reached route via GET
    else:

        rows = db.execute("SELECT * FROM products WHERE id = ?", product_id)
        rows[0]["rounded_rating"] = int((round(rows[0]["avg_rating"]* 2) / 2) * 10)

        all_ratings = db.execute("SELECT rating FROM reviews WHERE product_id = ?", product_id)
        ratings_length = len(all_ratings)
        star_ratings = []
        if ratings_length != 0:
            for i in range(5,0,-1):
                counter = 0
                for j in range(ratings_length):
                    if all_ratings[j]["rating"] == i:
                        counter += 1
                entry = {
                    "stars" : i,
                    "total" : counter,
                    "percentage" : round(counter / ratings_length * 100)
                }
                star_ratings.append(entry)
        else:
            for i in range(5,0,-1):
                entry = {
                    "stars" : i,
                    "total" : 0,
                    "percentage" : 0
                }
                star_ratings.append(entry)

        if session.get("user_id"):
            reviews = db.execute("SELECT reviews.id, rating, title, content, date, first_name, last_name FROM reviews JOIN users ON user_id = users.id WHERE product_id = ? AND reviews.user_id != ? ORDER BY rating DESC", product_id, session["user_id"])
            user_review = db.execute("SELECT reviews.id, rating, title, content, date, first_name, last_name FROM reviews JOIN users ON user_id = users.id WHERE product_id = ? AND reviews.user_id = ?", product_id, session["user_id"])

            if len(user_review) != 1:
                return render_template("shop/product.html", product=rows[0], reviews=reviews, star_ratings=star_ratings)
            else:
                return render_template("shop/product.html", product=rows[0], reviews=reviews, star_ratings=star_ratings, user_review=user_review[0])

        else:
            reviews = db.execute("SELECT reviews.id, rating, title, content, date, first_name, last_name FROM reviews JOIN users ON user_id = users.id WHERE product_id = ? ORDER BY rating DESC", product_id)
            return render_template("shop/product.html", product=rows[0], reviews=reviews, star_ratings=star_ratings)


@app.route("/create_review/<url>", methods=["GET","POST"])
@login_required_plus("/create_review/")
@verification_required
def review(product_id):
    """ Leave a review on a product that you have purchased """

    # Create review form via POST
    if request.method == "POST":

        if not request.form.get("rating") or not request.form.get("title") or not request.form.get("review"):
            return apology("please fill in all required fields")

        # Add review to database
        db.execute("INSERT INTO reviews (user_id, product_id, rating, title, content, date) VALUES (?, ?, ?, ?, ?, date('now'))",
                   session["user_id"], product_id, request.form.get("rating"), request.form.get("title"), request.form.get("review"))

        # Update average rating for product
        avg = average_rating(product_id)
        db.execute("UPDATE products SET avg_rating = ? WHERE id = ?", avg, product_id)

        flash('Thank you for reviewing this product.')
        return redirect(f"/shop/{product_id}")

    # GET
    else:

        # Name of product for response
        product = db.execute("SELECT name FROM products WHERE id = ?", product_id)
        if len(product) == 0:
            flash("This product does not exist.")
            return redirect("/")
        name = product[0]["name"]

        # Check that user has purchased the product
        check = db.execute("SELECT * FROM orders JOIN products_orders ON order_id = id WHERE product_id = ? AND user_id = ?", product_id, session["user_id"])

        # User has not purchased this product
        if len(check) == 0:
            return render_template("shop/create_review.html", product_id=product_id, name=name, status=1)

        # User has purchased but already reviewed the product
        check = db.execute("SELECT id FROM reviews WHERE user_id = ? AND product_id = ?", session["user_id"], product_id)
        if len(check) != 0:
            return render_template("shop/create_review.html", product_id=product_id,  name=name, review_id=check[0]["id"], status=2)

        # User can proceed to review the product
        return render_template("shop/create_review.html", product_id=product_id, name=name, status=0)


@app.route("/edit_review/<url>", methods=["GET","POST"])
@login_required_plus("/edit_review/")
@verification_required
def edit_review(review_id):
    """ Edit an already existing review """

    if request.method == "POST":

        if not request.form.get("rating") or not request.form.get("title") or not request.form.get("review"):
            return apology("please fill in all required fields")

        product_id = request.form.get("product_id")

        # Update existing db entry
        db.execute("UPDATE reviews SET rating = ?, title = ?, content = ?, date = date('now') WHERE id = ?", request.form.get("rating"), request.form.get("title"), request.form.get("review"), review_id)

        # Update products average rating
        avg = average_rating(product_id)
        db.execute("UPDATE products SET avg_rating = ? WHERE id = ?", avg, product_id)

        flash("You have successfully edited your review for this product.")
        return redirect(f"/shop/{product_id}")

    else:
        author = db.execute("SELECT user_id FROM reviews WHERE id = ?", review_id)

        if len(author) == 0:
            return apology("review does not exist")
        elif author[0]["user_id"] != session["user_id"]:
            return apology("you do not have access to this page")
        else:
            review = db.execute("SELECT reviews.id, user_id, product_id, rating, title, content, name FROM reviews JOIN products ON product_id = products.id WHERE reviews.id = ?", review_id)
            return render_template("shop/edit_review.html", review=review[0])


@app.route("/review_history")
@login_required("/review_history")
def review_history():
    """ Display table of users reviews """

    reviews = db.execute("SELECT reviews.id, product_id, date, rating, name, image FROM reviews JOIN products ON product_id = products.id WHERE user_id = ? ORDER BY date DESC", session["user_id"])
    print(reviews)
    return render_template("shop/review_history.html", reviews=reviews)


@app.route("/basket", methods=["GET","POST"])
@login_required("/basket")
def basket():
    """Shopping basket"""

    # Delete item from basket via POST
    if request.method == "POST":

        # Get ID of product to be removed from basket
        id = int(request.form.get("id"))

        # Remove product from basket
        for i in range(len(session["basket"])):
            if session["basket"][i]["product_id"] == id:
                del session["basket"][i]
                break

        # Query for name of the deleted item for flashed messages
        productName = db.execute("SELECT name FROM products WHERE id = ?", id)[0]["name"]
        message = f'<a href="/shop/{id}">{productName}</a> has been removed from your basket.'

        # Check if basket is now empty
        if "basket" not in session or len(session["basket"]) == 0:
            total_cost = 0
            flash(Markup(message))
            return render_template("shop/basket.html", total_cost=total_cost)

        # Get product information for new basket items
        contents = product_info(session["basket"])

        # Calculate total cost of proposed order
        total_cost = basket_total(contents)

        # Load basket with new contents and total cost
        flash(Markup(message))
        return render_template("shop/basket.html", contents=contents, total_cost=total_cost)

    # User reached route via GET
    else:

        # Check that basket has contents
        if "basket" not in session or len(session["basket"]) == 0:
            total_cost = 0
            return render_template("shop/basket.html", total_cost=total_cost)

        # Get product information from database and append desired quantity
        contents = product_info(session["basket"])

        # Calculate total cost of proposed order
        total_cost = basket_total(contents)

        # Load basket
        return render_template("shop/basket.html", contents=contents, total_cost=total_cost)


@app.route("/basket_change", methods=["POST"])
def change():
    """AJAX call for basket total cost"""

    # Get data from AJAX call
    json = request.get_json()

    # Find the new quantity and which item has been changed
    quantity = int(json["quantity"])
    product_id = int(json["product_id"])

    # Update session basket variable with new quantity
    for i in range(len(session["basket"])):
        if session["basket"][i]["product_id"] == product_id:
            session["basket"][i]["quantity"] = quantity

    # Get product information
    contents = product_info(session["basket"])

    # Calculate total cost of proposed order
    total_cost = basket_total(contents)

    # Update total cost of the basket
    return jsonify(total_cost)


@app.route("/checkout", methods=["GET","POST"])
@login_required("/checkout")
def checkout():
    """Finalise purchase"""

    # Form submitted with delivery address and payment method via POST
    if request.method == "POST":

        # Ensure all delivery information has been provided
        if not request.form.get("phone_number"):
            return apology("please provide a contact number")

        if not request.form.get("address"):
            return apology("no address provided")

        if not request.form.get("city"):
            return apology("no town/city provided")

        if not request.form.get("postcode"):
            return apology("no postcode provided")

        # Convert checkbox response to binary for SQLite boolean storage
        if request.form.get("rememberDestination") == None:
            rememberDestination = 0
        else:
            rememberDestination = 1

        if request.form.get("rememberPayment") ==  None:
            rememberPayment = 0
        else:
            rememberPayment = 1

        # Check if delivery address already exists on the system
        rows = db.execute("SELECT * FROM destination WHERE address = ? AND city = ? AND postcode = ?",
                          request.form.get("address"), request.form.get("city"), request.form.get("postcode"))

        # If address already exists and user set this address as default, update preference in database
        if len(rows) != 0:
            if rows[0]["remember"] == 0 and rememberDestination == 1:
                db.execute("UPDATE destination SET remember = 1 WHERE id = ?", rows[0]["id"])
            deliveryID = rows[0]["id"]

        # If address is new to the system, submit destination data to database
        else:
            deliveryID = db.execute("INSERT INTO destination (address, city, postcode, remember) VALUES (?, ?, ?, ?)",
                   request.form.get("address"), request.form.get("city"), request.form.get("postcode"), rememberDestination)

        # Ensure all payment information has been provided
        if not request.form.get("cardNumber"):
            return apology("no card number provided")

        # Check validity of card and insert into database if cleared
        cardType = credit(int(request.form.get("cardNumber")))
        if cardType == "INVALID":
            return apology("card number is invalid")
        else:
            check = db.execute("SELECT * FROM payment WHERE card_number = ? AND card_type = ?",
                               request.form.get("cardNumber"), cardType)
            if len(check) != 0:
                paymentID = check[0]["id"]
            else:
                paymentID = db.execute("INSERT INTO payment (card_number, card_type, remember) VALUES (?, ?, ?)",
                           request.form.get("cardNumber"), cardType, rememberPayment)

        # Calculate total cost of order
        contents = product_info(session["basket"])
        for content in contents:
            content["sub_total"] = int(content["price"]) * int(content["quantity"])
        total_cost = basket_total(contents)

        # Create order with links to relevant data on database
        orderID = db.execute("INSERT INTO orders (user_id, destination_id, payment_id, phone_number, total_cost, timestamp, total_items) VALUES (?, ?, ?, ?, ?, datetime('now'), ?)",
                   session["user_id"], deliveryID, paymentID, request.form.get("phone_number"), total_cost, len(session["basket"]))
        timestamp = db.execute("SELECT timestamp FROM orders WHERE id = ?", orderID)[0]["timestamp"]

        # Create products_orders join table entries
        for s in session["basket"]:
            db.execute("INSERT INTO products_orders (product_id, order_id, quantity) VALUES (?, ?, ?)", s["product_id"], orderID, s["quantity"])

        # Update stock for each item in the order
        for s in session["basket"]:
            current_stock = db.execute("SELECT stock FROM products WHERE id = ?", s["product_id"])
            new_stock = current_stock[0]["stock"] - s["quantity"]
            db.execute("UPDATE products SET stock = ? WHERE id = ?", new_stock, s["product_id"])

        # Get order information together for view and email
        number = request.form.get("phone_number")
        address = db.execute("SELECT address, city, postcode FROM destination WHERE id = ?", deliveryID)
        payment = db.execute("SELECT card_number, card_type FROM payment WHERE id = ?", paymentID)

        # Scramble all but last 4 digits of card number
        card_number = str(payment[0]["card_number"])
        censored = censor_number(card_number)

        # Send an email to the user with invoice
        email = db.execute("SELECT email FROM users WHERE id = ?", session["user_id"])[0]["email"]
        msg = Message(f"Order Number: {orderID}", recipients=[email])
        msg.html = render_template("emails/shop_invoice.html", contents=contents, total_cost=total_cost, number=number, address=address[0], payment=payment[0], order_number=orderID, censored=censored, timestamp=timestamp)
        mail.send(msg)

        # Clear basket now order is complete
        session["basket"] = []

        # Display confirmed order invoice
        flash("Order Complete. An email has been sent to your linked email address with a copy of this invoice.")
        return render_template("shop/order_complete.html", contents=contents, total_cost=total_cost, number=number, address=address[0], payment=payment[0], order_number=orderID, censored=censored, timestamp=timestamp)

    # Route reached via GET
    else:

        # Check basket exists
        if "basket" not in session or len(session["basket"]) == 0:
            flash("Cannot checkout with an empty basket.")
            return redirect("/shop")

        # Get product information
        contents = product_info(session["basket"])
        for content in contents:
            content["sub_total"] = int(content["price"]) * int(content["quantity"])

        # Calculate total cost of proposed order
        total_cost = basket_total(contents)

        # Load checkout page with order
        return render_template("shop/checkout.html", contents=contents, total_cost=total_cost)


@app.route("/order_history")
@login_required("/order_history")
def my_orders():
    """ Display users food and shop order history """

    orders = db.execute("SELECT * FROM orders WHERE user_id = ? ORDER BY timestamp DESC", session["user_id"])
    food_orders = db.execute("SELECT id, total_cost, timestamp, servings FROM food_orders WHERE user_id = ? ORDER BY timestamp DESC", session["user_id"])
    return render_template("account/order_history.html", orders=orders, food_orders=food_orders)


@app.route("/order/<url>")
@login_required_plus("/order/")
def order(order_id):
    """ Provide user with detailed breakdown of specific order """

    # Obtain the user_id for the order
    orderID = db.execute("SELECT user_id FROM orders WHERE id = ?", order_id)

    # Check that the order exists
    if len(orderID) == 0:
        return apology("you do not have access to this page")

    # Check that user is the owner of this order
    if orderID[0]["user_id"] != session["user_id"]:
        return apology("you do not have access to this page")

    # Query for product information and quantity
    contents = db.execute("SELECT * FROM products WHERE id IN (SELECT product_id FROM products_orders WHERE order_id = ?)", order_id)
    quantities = db.execute("SELECT product_id, quantity FROM products_orders WHERE order_id = ?", order_id)

    # Append quantity of each item in the order to the respective product data
    for i in range(len(contents)):
        for j in range(len(quantities)):
            if contents[i]["id"] == quantities[j]["product_id"]:
                contents[i]["quantity"] = quantities[j]["quantity"]
    for content in contents:
        content["sub_total"] = int(content["price"]) * int(content["quantity"])

    # Query for delivery address
    address = db.execute("SELECT * FROM destination WHERE id = (SELECT destination_id FROM orders WHERE id = ?)", order_id)[0]

    # Query for payment details
    payment = db.execute("SELECT * FROM payment WHERE id = (SELECT payment_id FROM orders WHERE id = ?)", order_id)[0]
    censored = censor_number(str(payment["card_number"]))

    # Query for total cost and date of the order
    order = db.execute("SELECT id, phone_number, total_cost, timestamp FROM orders WHERE id = ?", order_id)[0]

    # Render invoice view with all relevant information
    return render_template("shop/invoice.html", contents=contents, address=address, payment=payment, order=order, censored=censored)


@app.route("/food_order/<url>")
@login_required_plus("/food_order/")
def food_order(order_id):
    """ Provide user with history of their shop orders """

    # Obtain the user_id for the order
    orderID = db.execute("SELECT user_id FROM food_orders WHERE id = ?", order_id)

    # Check that the order exists
    if len(orderID) == 0:
        return apology("you do not have access to this page")

    # Check that user is the owner of this order
    if orderID[0]["user_id"] != session["user_id"]:
        return apology("you do not have access to this page")

    # Query for meals in order
    meals = db.execute("SELECT * FROM recipes WHERE id IN (SELECT recipe_id FROM food_orders_meals WHERE food_order_id = ?)", order_id)
    servings = db.execute("SELECT servings FROM food_orders WHERE id = ?", order_id)[0]["servings"]

    preferences = {
        "meals": len(meals),
        "people": servings
    }

    # Query for delivery address
    address = db.execute("SELECT * FROM destination WHERE id = (SELECT destination_id FROM food_orders WHERE id = ?)", order_id)[0]

    # Query for payment details
    payment = db.execute("SELECT * FROM payment WHERE id = (SELECT payment_id FROM food_orders WHERE id = ?)", order_id)[0]

    # Query for total cost and date of the order
    order = db.execute("SELECT id, total_cost, timestamp FROM food_orders WHERE id = ?", order_id)[0]

    # Render invoice view with all relevant information
    return render_template("subscription/invoice.html", meals=meals, address=address, payment=payment, order=order, preferences=preferences)


@app.route("/quote", methods=["GET","POST"])
def quote():
    """Quote subscription price"""

    # Form submitted via POST
    if request.method == "POST":

        # If user is not logged in force them to login or register
        if session.get("user_id") is None:
            return redirect("/login/quote")

        # Check to see if user already has a preferences profile
        check = db.execute("SELECT * FROM preferences WHERE user_id = ?", session["user_id"])

        # If profile exists update with new values
        if len(check) != 0:
            db.execute("UPDATE preferences SET people = ?, meals = ? WHERE user_id = ?", request.form.get("people"), request.form.get("meals"), session["user_id"])

        # If not create new entry into preferences table
        else:
            db.execute("INSERT INTO preferences (user_id, people, meals) VALUES (?, ?, ?)", session["user_id"], request.form.get("people"), request.form.get("meals"))

        # Continue to next stage
        return redirect("/preferences")

    # Route reached via GET
    else:

        # If user is not logged start food sequence from the start
        if session.get("user_id") is None:
            return render_template("subscription/quote.html")

        # Check if user is revisiting page
        check = db.execute("SELECT * FROM preferences WHERE user_id = ?", session["user_id"])

        # If user has already selected number of weekly servings skip page
        if len(check) != 0 and (check[0]["people"] and check[0]["meals"] is not None):
            return redirect("/preferences")

        # If this is the first time start food sequence from the start
        else:
            return render_template("subscription/quote.html")


@app.route("/AJAX_quote", methods=["POST"])
def AJAX_quote():
    """AJAX call to provide dynamic quote to user"""

    # Get data from AJAX call
    json = request.get_json()

    # Find newly selected number of people and meals
    people = int(json["peopleValue"])
    meals = int(json["mealsValue"])

    # Calculate the cost of that number of servings
    servings = people * meals
    price = servings * 3

    # Return the price estimate
    return jsonify(price)


@app.route("/preferences", methods=["GET","POST"])
@login_required("/preferences")
def preferences():
    """Log users dietary and allergy preferences"""

    # Form submitted via POST
    if request.method == "POST":

        # Get dietary preferences from form
        if request.form.get("dietary") == "vegetarian":
            vegetarian = 1
            vegan = 0
        elif request.form.get("dietary") == "vegan":
            vegetarian = 0
            vegan = 1
        else:
            vegetarian = vegan = 0

        # Update database with relevant information
        db.execute("UPDATE preferences SET vegetarian = ?, vegan = ? WHERE user_id = ?", vegetarian, vegan, session["user_id"])

        # Store all allergy information in the user profile
        allergens = db.execute("SELECT * FROM allergens")

        # Iterate through each allergen
        for allergen in allergens:

            # If allergen is selected
            if request.form.get(f'{allergen["allergen"]}') != None:
                check = db.execute("SELECT * FROM users_allergens WHERE user_id = ? AND allergen_id = ?", session["user_id"], allergen["id"])

                # If allergen is not already recorded in users_allergen table create a new entry
                if len(check) == 0:
                    db.execute("INSERT INTO users_allergens (user_id, allergen_id) VALUES (?, ?)", session["user_id"], allergen["id"])

            # If allergen is not selected
            else:
                check = db.execute("SELECT * FROM users_allergens WHERE user_id = ? AND allergen_id = ?", session["user_id"], allergen["id"])
                # If allergen was previously selected, remove entry in table
                if len(check) != 0:
                    db.execute("DELETE FROM users_allergens WHERE user_id = ? AND allergen_id = ?", session["user_id"], allergen["id"])

        # Redirect to recipe list
        return redirect("/menu")

    # Route reached via GET
    else:

        # Check if user has already completed form before
        check = db.execute("SELECT * FROM preferences WHERE user_id = ?", session["user_id"])[0]

        # If user has vegetarian and vegan preferences form has been completed before
        if (check["vegetarian"] and check["vegan"]) != None:
            return redirect("/menu")

        # Otherwise load preferences form
        else:
            allergens = db.execute("SELECT allergen FROM allergens")
            return render_template("subscription/preferences.html", allergens=allergens)


@app.route("/menu", methods=["GET","POST"])
@login_required("/menu")
def menu():
    """ Display this weeks meal options to the user """

    # Form submitted via POST
    if request.method == "POST":

        # Retrieve chosen meals from form and convert to integers
        session["meals"] = request.form.getlist("meal")
        for i in range(len(session["meals"])):
            session["meals"][i] = int(session["meals"][i])

        return redirect("/menu_checkout")

    # Route is reached via GET
    else:

        # Find number of people and meals per week from database
        preferences = db.execute("SELECT * FROM preferences WHERE user_id = ?", session["user_id"])

        # Find dietary preferences for use in SQL query
        if preferences[0]["vegetarian"] == 1:
            diet = "vegetarian"
        elif preferences[0]["vegan"] == 1:
            diet = "vegan"
        else:
            diet="none"

        # Find meals from recipe table that fulfil users diet and allergy criteria
        # Display all meal types
        if diet == "none":
            meals = db.execute("SELECT * FROM recipes WHERE id NOT IN (SELECT recipe_id FROM recipes_ingredients WHERE ingredient_id IN (SELECT ingredient_id FROM ingredients_allergens WHERE allergen_id IN (SELECT allergen_id FROM users_allergens WHERE user_id = ?)))", session["user_id"])

        # Display both vegetarian and vegan options
        elif diet == "vegetarian":
            meals = db.execute("SELECT * FROM recipes WHERE dietary != 'none' AND id NOT IN (SELECT recipe_id FROM recipes_ingredients WHERE ingredient_id IN (SELECT ingredient_id FROM ingredients_allergens WHERE allergen_id IN (SELECT allergen_id FROM users_allergens WHERE user_id = ?)))", session["user_id"])

        # Display just vegan options
        else:
            meals = db.execute("SELECT * FROM recipes WHERE dietary = ? AND id NOT IN (SELECT recipe_id FROM recipes_ingredients WHERE ingredient_id IN (SELECT ingredient_id FROM ingredients_allergens WHERE allergen_id IN (SELECT allergen_id FROM users_allergens WHERE user_id = ?)))", diet, session["user_id"])

        # Display all relevant meal options
        return render_template("subscription/menu.html", preferences=preferences[0], meals=meals)


@app.route("/menu_checkout", methods=["GET","POST"])
@login_required("/menu_checkout")
def menu_checkout():
    """ Complete weekly meal delivery order """

    if request.method == "POST":

        # Ensure all delivery information has been provided
        if not request.form.get("phone_number"):
            return apology("please provide a contact number")

        if not request.form.get("address"):
            return apology("no address provided")

        if not request.form.get("city"):
            return apology("no town/city provided")

        if not request.form.get("postcode"):
            return apology("no postcode provided")

        # Convert checkbox response to binary for SQLite boolean storage
        if request.form.get("rememberDestination") == None:
            rememberDestination = 0
        else:
            rememberDestination = 1

        if request.form.get("rememberPayment") ==  None:
            rememberPayment = 0
        else:
            rememberPayment = 1

        # Check if delivery address already exists on the system
        rows = db.execute("SELECT * FROM destination WHERE address = ? AND city = ? AND postcode = ?",
                          request.form.get("address"), request.form.get("city"), request.form.get("postcode"))

        # If address already exists and user set this address as default, update preference in database
        if len(rows) != 0:
            if rows[0]["remember"] == 0 and rememberDestination == 1:
                db.execute("UPDATE destination SET remember = 1 WHERE id = ?", rows[0]["id"])
            deliveryID = rows[0]["id"]

        # If address is new to the system, submit destination data to database
        else:
            deliveryID = db.execute("INSERT INTO destination (address, city, postcode, remember) VALUES (?, ?, ?, ?)",
                   request.form.get("address"), request.form.get("city"), request.form.get("postcode"), rememberDestination)

        # Ensure all payment information has been provided
        if not request.form.get("cardNumber"):
            return apology("no card number provided")

        # Check validity of card and insert into database if cleared
        cardType = credit(int(request.form.get("cardNumber")))
        if cardType == "INVALID":
            return apology("card number is invalid")
        else:
            check = db.execute("SELECT * FROM payment WHERE card_number = ? AND card_type = ?",
                               request.form.get("cardNumber"), cardType)
            if len(check) != 0:
                paymentID = check[0]["id"]
            else:
                paymentID = db.execute("INSERT INTO payment (card_number, card_type, remember) VALUES (?, ?, ?)",
                           request.form.get("cardNumber"), cardType, rememberPayment)

        # Calculate order cost
        row = db.execute("SELECT meals, people FROM preferences WHERE user_id = ?", session["user_id"])
        servings = row[0]["meals"] * row[0]["people"]
        cost = servings * 3

        # Record food order in database
        orderID = db.execute("INSERT INTO food_orders (user_id, destination_id, payment_id, phone_number, total_cost, timestamp, servings) VALUES (?, ?, ?, ?, ?, datetime('now'), ?)",
                             session["user_id"], deliveryID, paymentID, request.form.get("phone_number"), cost, row[0]["people"])

        # Fill out food order join table
        for s in session["meals"]:
            db.execute("INSERT INTO food_orders_meals (recipe_id, food_order_id) VALUES (?, ?)", s, orderID)

        # Allow access to relevant recipes
        for s in session["meals"]:
            access_check = db.execute("SELECT * FROM recipe_access WHERE user_id = ? AND recipe_id = ?", session["user_id"], s)
            if len(access_check) == 0:
                db.execute("INSERT INTO recipe_access (user_id, recipe_id) VALUES (?, ?)", session["user_id"], s)

        # Get order information together for view and email
        number = request.form.get("phone_number")
        meals = db.execute("SELECT * FROM recipes WHERE id IN (?)", session["meals"])
        address = db.execute("SELECT address, city, postcode FROM destination WHERE id = ?", deliveryID)[0]
        payment = db.execute("SELECT card_number, card_type FROM payment WHERE id = ?", paymentID)[0]
        order = db.execute("SELECT id, total_cost, timestamp FROM food_orders WHERE id = ?", orderID)[0]

        # Censor number for invoices
        card_number = str(payment["card_number"])
        censored = censor_number(card_number)

        # Send an email to the user with invoice
        email = db.execute("SELECT email FROM users WHERE id = ?", session["user_id"])[0]["email"]
        msg = Message(f"Order Number: {orderID}", recipients=[email])
        msg.html = render_template("emails/food_invoice.html", meals=meals, preferences=row[0], number=number, address=address, payment=payment, order=order, censored=censored)
        mail.send(msg)

        # Clear meals session variable now order is complete
        session["meals"] = []

        return render_template("subscription/invoice.html", meals=meals, preferences=row[0], number=number, address=address, payment=payment, order=order, censored=censored)

    # Display page through GET
    else:

        # Find weekly number of meals selected by the user
        pref = db.execute("SELECT meals, people FROM preferences WHERE user_id = ?", session["user_id"])

        # If user has not selected correct number of meals redirect them to the menu
        if "meals" not in session or len(session["meals"]) != pref[0]["meals"]:
            flash("Please select this weeks meals before checking out.")
            return redirect("/menu")

        # Query database to access information about relevant meals
        meals = db.execute("SELECT * FROM recipes WHERE id IN (?)", session["meals"])

        # Cost of order
        total_cost = pref[0]["people"] * pref[0]["meals"] * 3

        # Visually confirm order to user and prompt for delivery/payment information
        return render_template("subscription/checkout.html", meals=meals, preferences=pref[0], total_cost=total_cost)


@app.route("/my_recipes")
@login_required("/my_recipes")
def my_recipes():
    """ Display all recipes that the user has access to """

    meals = db.execute("SELECT name, image, duration, page_reference FROM recipes WHERE id IN (SELECT recipe_id FROM recipe_access WHERE user_id = ?)", session["user_id"])
    return render_template("subscription/my_recipes.html", meals=meals)


@app.route("/my_recipes/<url>")
@login_required_plus("/my_recipes/")
def recipe(recipe_name):
    """ Location of recipe page for each meal """

    # Check that user has access to the requested recipe
    rows = db.execute("SELECT * FROM recipe_access WHERE user_id = ? AND recipe_id = (SELECT id FROM recipes WHERE page_reference = ?)", session["user_id"], recipe_name)
    if len(rows) == 0:
        return apology("you do not have access to this page")

    # Display recipe page
    return render_template(f"recipes/{recipe_name}.html")


@app.route("/blog")
def blog():
    """ View all food blog posts """

    # Query for post data
    posts = db.execute("SELECT posts.id, title, timestamp, first_name, last_name FROM posts JOIN users ON posts.user_id = users.id ORDER BY last_action DESC")

    # If there are no posts render empty view
    if len(posts) == 0:
        return render_template("blog/blog_browse.html")

    # Current time as datetime
    now = datetime.now().isoformat(' ', 'seconds')
    current_time = datetime.strptime(now, '%Y-%m-%d %H:%M:%S')

    # Total number of comments for each post  ! What if 0 comments ??  !
    for i in range(len(posts)):
        post_id = posts[i]["id"]
        comments = db.execute("SELECT id FROM comments WHERE post_id = ?", post_id)
        posts[i]["total_comments"] = len(comments)

    # Datetime of last interaction for each post
    for i in range(len(posts)):
        post_id = posts[i]["id"]
        timestamp = db.execute("SELECT last_action FROM posts WHERE id = ?", post_id)
        last_action = datetime.strptime(timestamp[0]["last_action"], '%Y-%m-%d %H:%M:%S')
        difference = current_time - last_action
        view_str = last_interaction(difference)
        posts[i]["view_string"] = view_str

    return render_template("blog/blog_browse.html", posts=posts)


@app.route("/blog/<post_id>", methods=["GET","POST"])
def blog_post(post_id):
    """ Render individual blog posts and comments """

    # Create, edit, or delete a comment via POST
    if request.method == "POST":

        # Comment create form submission
        if request.form.get("type") == "create":
            db.execute("INSERT INTO comments (user_id, post_id, content, karma, timestamp) VALUES (?, ?, ?, ?, datetime('now'))",
                       session["user_id"], post_id, request.form.get("comment"), 0)
            db.execute("UPDATE posts SET last_action = datetime('now') WHERE id = ?", post_id)

            flash("Successfully created comment.")

        # Edit comment form submission
        elif request.form.get("type") == "edit":
            db.execute("UPDATE comments SET content = ?, edit = datetime('now') WHERE id = ?", request.form.get("content"), request.form.get("comment_id"))

            flash("Your comment has been successfully updated.")

        # Delete comment form submission
        elif request.form.get("type") == "delete":
            db.execute("DELETE FROM comments_karma WHERE comment_id = ?", request.form.get("comment_id"))
            db.execute("DELETE FROM comments WHERE id = ?", request.form.get("comment_id"))

            # Find new most recent action and update
            timestamp = db.execute("SELECT timestamp FROM comments WHERE post_id = ? ORDER BY timestamp DESC", post_id)

            # If no comments exist, set last interaction to post timestamp
            if len(timestamp) == 0:
                post_timestamp = db.execute("SELECT timestamp FROM posts WHERE id = ?", post_id)
                db.execute("UPDATE posts SET last_action = ? WHERE id = ?", post_timestamp[0]["timestamp"], post_id)

            # Find most recent comment to become last interaction
            else:
                db.execute("UPDATE posts SET last_action = ? WHERE id = ?", timestamp[0]["timestamp"], post_id)

            flash("Your comment has been successfully deleted.")

        # Delete post form submission
        elif request.form.get("type") == "postDelete":
            db.execute("DELETE FROM comments_karma WHERE comment_id IN (SELECT id FROM comments WHERE post_id = ?)", post_id)
            db.execute("DELETE FROM comments WHERE post_id = ?", post_id)
            db.execute("DELETE FROM posts WHERE id = ?", post_id)

            flash("Your blog post has been successfully deleted.")
            return redirect("/blog")

        else:
            return apology("something went wrong")

        # Reload page with new comments
        return redirect(f"/blog/{post_id}")

    # Route reached via GET
    else:

        # Query database for post specific data
        post = db.execute("SELECT * FROM posts WHERE id = ?", post_id)[0]
        name = db.execute("SELECT first_name, last_name FROM users WHERE id = ?", post["user_id"])
        author = concatenate(name[0]["first_name"], name[0]["last_name"])

        # Query database for comments
        comments = db.execute("SELECT * FROM comments WHERE post_id = ? ORDER BY karma DESC", post_id)

        # Iterate through all comments
        for i in range(len(comments)):

            # Add full name of commenter
            names = db.execute("SELECT first_name, last_name FROM users WHERE id = ?", comments[i]["user_id"])
            full_name = concatenate(names[0]["first_name"], names[0]["last_name"])
            comments[i]["username"] = full_name

            # If user is a guest voting is disabled
            if session.get("user_id") is None:
                comments[i]["voteStatus"] = 0

            # Add vote status of current user for each comment
            else:
                voteStatus = db.execute("SELECT status FROM comments_karma WHERE user_id = ? AND comment_id = ?", session["user_id"], comments[i]["id"])
                if len(voteStatus) != 0:
                    if voteStatus[0]["status"] == 1:
                        comments[i]["voteStatus"] =  1
                    else:
                        comments[i]["voteStatus"] =  -1
                else:
                    comments[i]["voteStatus"] =  0

        # Display limited view for guest
        if session.get("user_id") is None:
            return render_template("blog/post.html", post=post, author=author, comments=comments)

        # Display full access view for logged in user
        return render_template("blog/post.html", post=post, author=author, comments=comments, verified=session["verified"])


@app.route("/blog/AJAX_post", methods=["POST"])
def AJAX_post():
    """ AJAX call for comment upvotes and downvotes """

    # Get data from AJAX call
    json = request.get_json()
    commentID = int(json["commentID"])

    # Check if current user already voted on this comment previously
    check = db.execute("SELECT status FROM comments_karma WHERE user_id = ? AND comment_id = ?",
                    session["user_id"], commentID)

    # Vote type is upvote
    if json["voteType"] == "upvote":
        voteStatus = 1
        # Update already existing db entry (i.e. existing downvote)
        if check:
            karmaChange = 2
            db.execute("UPDATE comments_karma SET status = ? WHERE user_id = ? AND comment_id = ?",
                       voteStatus, session["user_id"], commentID)

        # Add new vote to db if user has no current vote status
        else:
            karmaChange = 1
            db.execute("INSERT INTO comments_karma (user_id, comment_id, status) VALUES (?, ?, ?)",
                    session["user_id"], commentID, voteStatus)

    # Vote type is downvote
    elif json["voteType"] == "downvote":
        voteStatus = -1
        # Update already existing db entry (i.e. existing upvote)
        if check:
            karmaChange = -2
            db.execute("UPDATE comments_karma SET status = ? WHERE user_id = ? AND comment_id = ?",
                       voteStatus, session["user_id"], commentID)

        # Add new vote to db if user has no current vote status
        else:
            karmaChange = -1
            db.execute("INSERT INTO comments_karma (user_id, comment_id, status) VALUES (?, ?, ?)",
                    session["user_id"], commentID, voteStatus)

    # Vote type is remove upvote
    elif json["voteType"] == "remove-upvote":
        voteStatus = 0
        karmaChange = -1
        db.execute("DELETE FROM comments_karma WHERE user_id = ? AND comment_id = ?", session["user_id"], commentID)

    # Vote type is remove downvote
    elif json["voteType"] == "remove-downvote":
        voteStatus = 0
        karmaChange = 1
        db.execute("DELETE FROM comments_karma WHERE user_id = ? AND comment_id = ?", session["user_id"], commentID)

    else:
        return apology("voting error")

    # Query for current comment karma
    karma = db.execute("SELECT karma FROM comments WHERE id = ?", commentID)

    # Change karma and update database
    karma = karma[0]["karma"] + karmaChange
    db.execute("UPDATE comments SET karma = ? WHERE id = ?", karma, commentID)

    # Create dictionary of response for view
    data = {
        "commentID" : commentID,
        "karma" : karma,
        "voteStatus" : voteStatus
    }

    # Return the data
    return jsonify(data)


@app.route("/blog/create_post", methods=["GET","POST"])
@login_required("/blog/create_post")
@verification_required
def create_post():
    """ Create blog post """

    # Blog post created via POST
    if request.method == "POST":

        # Input new post into the database
        id = db.execute("INSERT INTO posts (user_id, title, content, timestamp, last_action) VALUES (?, ?, ? , datetime('now'), datetime('now'))",
                        session["user_id"], request.form.get("title"), request.form.get("content"))

        # Redirect user to their post
        return redirect(f"/blog/{id}")

    # Route reached via GET
    else:
        return render_template("blog/create_post.html", verified=session["verified"])


@app.route("/blog/edit_post/<url>", methods=["GET", "POST"])
@login_required_plus("/blog/edit_post/")
@verification_required
def edit_post(post_id):
    """ Edit blog post """

    if request.method == "POST":
        db.execute("UPDATE posts SET title = ?, content = ?, edit = datetime('now') WHERE id = ?", request.form.get("title"), request.form.get("content"), post_id)
        return redirect(f"/blog/{post_id}")
    else:
        author = db.execute("SELECT user_id FROM posts WHERE id = ?", post_id)

        if len(author) == 0:
            return apology("post does not exist")
        elif author[0]["user_id"] != session["user_id"]:
            return apology("you do not have access to this page")
        else:
            post = db.execute("SELECT * FROM posts WHERE id = ?", post_id)
            return render_template("blog/edit_post.html", post=post[0])


@app.route("/account/blog_history")
@login_required("/account/blog_history")
def blog_history():
    """ Display users post and comment history """

    posts = db.execute("SELECT id, title, timestamp FROM posts WHERE user_id = ? ORDER BY timestamp DESC", session["user_id"])

    # Append total comments for each post to dictionary
    for i in range(len(posts)):
        post_id = posts[i]["id"]
        comments = db.execute("SELECT id FROM comments WHERE post_id = ?", post_id)
        posts[i]["total_comments"] = len(comments)

    comments = db.execute("SELECT posts.id, title, karma, comments.timestamp FROM comments JOIN posts ON comments.post_id = posts.id WHERE comments.user_id = ? ORDER BY comments.timestamp DESC", session["user_id"])
    return render_template("blog/blog_history.html", posts=posts, comments=comments)


def errorhandler(e):
    """ Handle error """

    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)