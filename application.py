import os
import sys

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for, make_response
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required


# Configure application
app = Flask(__name__)

selected = []
total_amount = None


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
db = SQL("sqlite:///store2door.db")


@app.route("/")
@login_required
def index():
    return redirect("/portfolio")
    
@app.route("/portfolio", methods=["GET", "POST"])    
@login_required
def portfolio():
    selected.clear()
    total_amount = 0    
    if request.method == "GET":
        return render_template("portfolio.html")
    else:    
        for i in range(1, 11):
            if not request.form.get(f"item{i}"):
                pass
            else:
                item = {"item_id": None, "item_quantity": None, "item_name": None, "item_price": None, "item_amount": None}
                item["item_id"] = request.form.get(f"item{i}")
                item_list = db.execute("SELECT price,item_name FROM items WHERE item_id = :item_id",
                                       item_id=request.form.get(f"item{i}"))
                if request.form.get(f"item{i}-quantity"):
                    item["item_quantity"] = int(request.form.get(f"item{i}-quantity"))
                else:
                    item["item_quantity"] = 1
                item["item_price"] = item_list[0]["price"]
                item["item_name"] = item_list[0]["item_name"]
                item["item_amount"] = (item["item_price"] * item["item_quantity"])
                total_amount = (total_amount + item["item_amount"])
                selected.append(item)
        if selected:
            session["total_amount"] = total_amount
            session["selected"] = selected
            return render_template("cart.html", selected=selected, total_amount=session["total_amount"])
        else:
            flash("No Items Were Selected!")
            return redirect("/")    


@app.route("/cart", methods=["GET", "POST"])
@login_required
def cart():
    if request.method == "GET":
        if selected == []:
            flash("Select items and Click add to cart!")
            return redirect("/")
    else:     
        if not(request.form.get("name") or request.form.get("mobile") or request.form.get("address")):
            flash("error: form wasn't filled!")
            return redirect("/")
        order_for = request.form.get("name")
        mobile = request.form.get("moblie")
        address = request.form.get("address")
        if session["selected"] and session["total_amount"]:
            order = db.execute("INSERT INTO orders (user_id,total_amount,order_for,address) VALUES (:user_id,:total_amount,:order_for,:address)",
                              user_id=session["user_id"], total_amount=session["total_amount"], order_for=order_for, address=address)
            session.pop('selected', None)
            session.pop('total_amount', None)
            flash("Order Placed!")
            return redirect("/")
    
    
@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            flash("must provide username")
            return redirect("/")

        # Ensure password was submitted
        elif not request.form.get("password"):
            flash("must provide password")
            return redirect("/")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            flash("invalid username and/or password")
            return redirect("/")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        flash("Logged In")

        # Redirect user to home page
        return redirect("/")
        
    else:
        return render_template("login.html")
        
@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if (request.method == "POST"):

        if not (request.form.get("username") or request.form.get("email") or request.form.get("password") or request.form.get("confirmation")):
            flash("Please Fill the Form")
            return redirect("/")

        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if (password != confirmation):
            flash("Password not match")
            return redirect("/")

        checkusername = db.execute("SELECT username FROM users WHERE username = :username", username=username)

        if (checkusername != []):
            flash("username already exists")
            return redirect("/")

        hashed = generate_password_hash(password)
        new_user = db.execute("INSERT INTO users (username,email,hash) VALUES (:username,:email,:hashed)", username=username, email=email, hashed=hashed)

        session["user_id"] = new_user

        flash("Registered!")

        return redirect("/")

    else:
        return render_template("register.html")
        

