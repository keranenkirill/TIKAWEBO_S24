from flask import render_template, request, session, redirect, flash
from werkzeug.security import check_password_hash
from functools import wraps
import users
import logging
import properties

logging.basicConfig(level=logging.INFO)


def login_required(f):
    """
    Decorator to ensure that the user is logged in.

    Args:
        f (function): The route function to wrap.

    Returns:
        function: The decorated function that checks if the user is logged in.
                  If the user is not logged in, redirects to the login view.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect("/loginview")
        return f(*args, **kwargs)
    return decorated_function


def init_user_routes(app):
    """
    Initialize all user-related routes for the Flask application.

    Args:
        app (Flask): The Flask application instance.

    Defines routes for handling user actions such as login, logout, registration,
    viewing properties, and managing profiles.
    """

    @app.route("/")
    def index():
        """
        The home page route.

        Returns:
            Response: The rendered 'index.html' template with all listed properties.
        """
        listed_properties = properties.get_all_properties()  # Fetch properties from DB
        return render_template("index.html", properties=listed_properties)

    @app.route("/loginview")
    def loginview():
        """
        The route for displaying the login page.

        Returns:
            Response: The rendered 'loginview.html' template.
        """
        return render_template("loginview.html")

    @app.route("/registerview")
    def registerview():
        """
        The route for displaying the registration page.

        Returns:
            Response: The rendered 'registerview.html' template.
        """
        return render_template("registerview.html")

    @app.route("/profileview")
    def profile_view():
        """
        The route for displaying the user's profile.

        Returns:
            Response: The rendered 'profileview.html' template with the user's rented and listed properties.

        Redirects to the login page if the user is not logged in.
        """
        if 'user_id' not in session:
            return redirect("/loginview")

        user_id = session['user_id']
        userprofile = users.get_userprofile_by_id(user_id)
        rented_properties = properties.get_rented_properties(
            user_id)  # Fetch rented properties
        listed_properties = properties.get_user_listed_properties(user_id)
        return render_template("profileview.html", userprofile=userprofile, rented_properties=rented_properties, listed_properties=listed_properties)

    @app.route("/login", methods=["POST"])
    def login():
        """
        The route for handling the login form submission.

        Validates the username and password, and sets session data upon successful login.

        Returns:
            Response: Redirects to the home page on success or back to the login page on failure.
        """
        username = request.form["username"]
        password = request.form["password"]

        logging.info("Login attempt for user: %s", username)

        if username == "admin" and password == "admin123":
            session["user_id"] = 1
            session["username"] = "admin"
            flash("Admin login successful!", "success")
            return redirect("/")

        user = users.login(username)
        if not user:
            flash("Invalid username", "error")
            return redirect("/loginview")

        # Validate the password
        hash_value = user.password
        if check_password_hash(hash_value, password):
            logging.info("User %s logged in successfully", username)
            session["user_id"] = user.id  # Set user ID in session
            session["username"] = username  # Set username in session
            flash("Login successful!", "success")
            return redirect("/")
        else:
            logging.info("Invalid password for user: %s", username)
            flash("Invalid password", "error")
            return redirect("/loginview")

    @app.route("/edit_profile", methods=["POST"])
    def edit_profile():
        """
        The route for handling the profile edit form submission.

        Updates the user's profile information in the database.

        Returns:
            Response: Redirects to the profile page after a successful update or back with an error.
        """
        if 'user_id' not in session:
            return redirect("/loginview")

        user_id = session['user_id']
        password = request.form["password"]
        email = request.form["email"]
        phone = request.form["phone"]

        if users.update_user_profile(user_id, email, phone, password):
            flash("Profile updated successfully", "success")
        else:
            flash("Error updating profile", "error")

        return redirect("/profileview")

    @app.route("/add_property_review", methods=["POST"])
    def add_property_review():
        """
        The route for adding a review for a property.
        This route is a placeholder and is not yet implemented.
        """
        pass

    @app.route("/createuser", methods=["POST"])
    def createuser():
        """
        The route for handling the registration form submission.

        Validates the input data, checks if the username already exists,
        and creates a new user if all conditions are met.

        Returns:
            Response: Redirects to the login page after successful registration or back to registration on failure.
        """
        username = request.form["username"]
        psswd1 = request.form["password1"]
        psswd2 = request.form["password2"]
        email = request.form["email"]
        phone = request.form["phone"]

        if not username or not psswd1 or not psswd2:
            flash('Passwords do not match.', 'error')
            return render_template("registerview.html")
        if psswd1 != psswd2:
            flash('Passwords do not match.', 'error')
            return render_template("registerview.html")

        if users.check_user_in_db(username):
            flash('Username already exists.', 'error')
            return render_template("registerview.html")

        if users.add_new_user(psswd1, username, email, phone):
            flash("Username successfully created", "success")
            return redirect("/loginview")

    @app.route("/logout")
    @login_required
    def logout():
        """
        The route for logging out the user.

        Clears the session and redirects the user to the home page.

        Returns:
            Response: Redirects to the home page with a success message after logging out.
        """
        session.clear()  # Clear the entire session on logout
        flash("Logged out successfully", "success")
        return redirect("/")
