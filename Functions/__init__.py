import random
import os
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, flash, session
from Forms import CreateCardForm, CreateEbookForm, CreateReviewForm
from datetime import datetime
import shelve, Card
import re
from werkzeug.utils import secure_filename
from Card import Card, Ebook, User, Review, Transaction

# Define the upload folder and allowed extensions
UPLOAD_FOLDER = 'static'
ALLOWED_EXTENSIONS = {'jpg', 'png', 'jpeg'}

app = Flask(__name__)
app.secret_key = 'secret_key'

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

with shelve.open('user.db', writeback=True) as db:
    if 'Users' not in db:
        db['Users'] = {}

    # Check if a default owner account exists
    default_owner_username = "owner"  # Change this to your desired default username
    default_owner_exists = any(user.get_username() == default_owner_username for user in db['Users'].values())

    if not default_owner_exists:
        # Create a default owner account
        default_owner = User(
            username=default_owner_username,
            email="owner@example.com",  # Change this to your desired default email
            password="owner123",       # Change this to your desired default password
            role="Owner"               # Set the role to "Owner"
        )
        db['Users'][default_owner.get_user_id()] = default_owner
        print("Default owner account created.")

    # Convert keys to integers (if necessary)
    db['Users'] = {int(k): v for k, v in db['Users'].items()}
    User.count_id = max(db['Users'].keys(), default=0)

def staff_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'role' not in session or session['role'] not in ['Staff', 'Owner', 'Co-owner']:
            flash('Access denied. Staff or Owner only.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


import shelve




@app.route('/')
def home():
    # Open the ebooks database
    ebooks_dict = {}
    db = shelve.open('ebooks.db', 'r')
    try:
        ebooks_dict = db['Ebooks']
    except KeyError:
        print("No ebooks found in the database.")
    db.close()

    # Open the reviews database
    reviews_dict = {}
    db = shelve.open('reviews.db', 'r')
    try:
        reviews_dict = db['Reviews']
    except KeyError:
        print("No reviews found in the database.")
    db.close()

    # Convert the dictionary values to a list
    ebooks_list = list(ebooks_dict.values())

    # Calculate average rating and total reviews for each book
    for ebook in ebooks_list:
        book_reviews = [review for review in reviews_dict.values() if review.get_ebook_id() == ebook.get_ebook_id()]
        total_reviews = len(book_reviews)
        if total_reviews > 0:
            average_rating = sum(review.get_stars() for review in book_reviews) / total_reviews
        else:
            average_rating = 0

        # Add the average rating and total reviews to the ebook object
        ebook.average_rating = average_rating
        ebook.total_reviews = total_reviews

    # Featured Books: Top 6 books with the highest average ratings
    featured_books = sorted(ebooks_list, key=lambda x: x.average_rating, reverse=True)[:6]

    # Random Genre Books: Select a random genre and get 6 books from that genre
    genres = set(ebook.get_genre() for ebook in ebooks_list)
    random_genre = random.choice(list(genres)) if genres else None
    random_genre_books = [ebook for ebook in ebooks_list if ebook.get_genre() == random_genre][:6]

    return render_template('home.html', featured_books=featured_books, random_genre_books=random_genre_books, random_genre=random_genre)

@app.route('/promote_user/<int:user_id>/<role>', methods=['POST'])
@staff_only  # Ensure only staff (owners/co-owners) can access this route
def promote_user(user_id, role):
    if 'role' not in session or session['role'] not in ['Owner', 'Co-owner']:
        flash('You do not have permission to perform this action.', 'error')
        return redirect(url_for('user_management'))

    with shelve.open('user.db', writeback=True) as db:
        users_dict = db['Users']
        if user_id not in users_dict:
            flash('User not found.', 'error')
            return redirect(url_for('user_management'))

        target_user = users_dict[user_id]
        current_user_role = session['role']

        # Role hierarchy rules
        if current_user_role == 'Owner':
            if role in ['Owner', 'Co-owner', 'Staff', 'User']:
                target_user.set_role(role)
                flash(f'User {target_user.get_username()} has been promoted to {role}.', 'success')
            else:
                flash('Invalid role.', 'error')
        elif current_user_role == 'Co-owner':
            if role in ['Staff', 'User']:
                target_user.set_role(role)
                flash(f'User {target_user.get_username()} has been promoted to {role}.', 'success')
            else:
                flash('You do not have permission to promote to this role.', 'error')
        else:
            flash('You do not have permission to perform this action.', 'error')

        db['Users'] = users_dict

    return redirect(url_for('user_management'))

@app.route('/promote_to_staff/<int:user_id>', methods=['POST'])
@staff_only
def promote_to_staff(user_id):
    with shelve.open('user.db', writeback=True) as db:
        users_dict = db['Users']
        if user_id in users_dict:
            user = users_dict[user_id]
            user.set_role('Staff')
            db['Users'] = users_dict
            flash(f'User {user.get_username()} has been promoted to Staff.', 'success')
        else:
            flash('User not found.', 'error')

    return redirect(url_for('user_management'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        repeat_password = request.form['repeat_password']
        role = request.form.get('role', 'User')  # Default to 'User' if role is not provided

        # Ensure only Owners and Co-owners can create Staff or Co-owner accounts
        if role in ['Staff', 'Co-owner'] and ('role' not in session or session['role'] not in ['Owner', 'Co-owner']):
            flash('You do not have permission to create this type of account.', 'error')
            return redirect(url_for('register'))

        if password != repeat_password:
            flash('Passwords do not match!', 'error')
            return redirect(url_for('register'))

        with shelve.open('user.db', writeback=True) as db:
            users_dict = db['Users']
            user = User(username, email, password, role)
            users_dict[user.get_user_id()] = user
            db['Users'] = users_dict

        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        with shelve.open('user.db') as db:
            users_dict = db['Users']
            for user in users_dict.values():
                if user.get_username() == username and user.get_password() == password:
                    session['user_id'] = user.get_user_id()
                    session['username'] = user.get_username()  # Store username in session
                    session['role'] = user.get_role()
                    return redirect(url_for('home'))

        flash('Invalid credentials, please try again.', 'error')
        return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/user_management')
@staff_only
def user_management():
    if 'user_id' not in session or session.get('role') not in ['Staff', 'Owner', 'Co-owner']:
        flash('Access denied. Staff or Owner only.', 'error')
        return redirect(url_for('login'))

    with shelve.open('user.db') as db:
        users_dict = db['Users']
        users = list(users_dict.values())

    return render_template('user_management.html', users=users)

@app.route('/create_user', methods=['GET', 'POST'])
@staff_only
def create_user():
    if 'user_id' not in session or session.get('role') not in ['Staff', 'Owner', 'Co-owner']:
        flash('Access denied. Staff or Owner only.', 'error')
        return redirect(url_for('login'))

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        with shelve.open('user.db', writeback=True) as db:
            users_dict = db['Users']
            user = User(username=username, email=email, password=password, role=role)
            users_dict[user.get_user_id()] = user
            db['Users'] = users_dict

        flash('User created successfully!', 'success')
        return redirect(url_for('user_management'))

    return render_template('create_user.html')

@app.route('/delete_user/<int:user_id>', methods=['POST'])
@staff_only
def delete_user(user_id):
    if 'role' not in session or session['role'] not in ['Staff', 'Owner', 'Co-owner']:
        flash('Access denied!', 'error')
        return redirect(url_for('home'))

    with shelve.open('user.db', writeback=True) as db:
        users_dict = db['Users']
        if user_id in users_dict:
            del users_dict[user_id]
            db['Users'] = users_dict
            flash('User deleted successfully!', 'success')
        else:
            flash('User not found.', 'error')

    return redirect(url_for('user_management'))

@app.route('/update_user/<int:user_id>', methods=['GET', 'POST'])
@staff_only
def update_user(user_id):
    if 'role' not in session or session['role'] not in ['Owner']:
        flash('Access denied!', 'error')
        return redirect(url_for('home'))

    with shelve.open('user.db', writeback=True) as db:
        users_dict = db['Users']
        if user_id not in users_dict:
            flash('User not found.', 'error')
            return redirect(url_for('user_management'))

        user = users_dict[user_id]
        if request.method == 'POST':
            user.set_username(request.form['username'])
            user.set_email(request.form['email'])
            if request.form['password']:
                user.set_password(request.form['password'])
            user.set_role(request.form['role'])
            users_dict[user_id] = user
            db['Users'] = users_dict
            flash('User updated successfully.', 'success')
            return redirect(url_for('user_management'))

        return render_template('update_user.html', user=user, user_id=user_id)

# Function to check if a file has an allowed extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/thank_you')
def thank_you():
    return render_template('thank_you.html')

@app.route('/reviews/<int:id>')
def view_reviews(id):
    reviews_list = []
    is_empty = True  # Assume there are no reviews by default

    try:
        # Open the reviews database in 'c' mode (create if it doesn't exist)
        db = shelve.open('reviews.db', 'c')
        try:
            # Try to retrieve the 'Reviews' dictionary
            reviews_dict = db.get('Reviews', {})  # Use .get() to avoid KeyError
            if not reviews_dict:  # If 'Reviews' key doesn't exist or is empty
                db['Reviews'] = {}  # Initialize an empty dictionary
                reviews_dict = db['Reviews']
            # Filter reviews for the current book
            reviews_list = [review for review in reviews_dict.values() if review.get_ebook_id() == id]
            is_empty = len(reviews_list) == 0  # Check if there are no reviews for this book
        except Exception as e:
            print(f"Error accessing reviews.db: {e}")
        finally:
            db.close()
    except Exception as e:
        print(f"An error occurred: {e}")

    return render_template('reviews.html', reviews_list=reviews_list, id=id, is_empty=is_empty)

@app.route('/submit_review/<int:id>', methods=['GET', 'POST'])
def submit_review(id):
    create_review_form = CreateReviewForm(request.form)
    if request.method == 'POST' and create_review_form.validate():
        reviews_dict = {}
        db = shelve.open('reviews.db', 'c')
        try:
            reviews_dict = db['Reviews']
        except KeyError:
            print("Error in retrieving Reviews from reviews.db.")

        # Create a new review
        review = Review(
            ebook_id=id,
            stars=create_review_form.stars.data,
            message=create_review_form.message.data,
            reviewer_name=create_review_form.reviewer_name.data
        )

        # Save the review to the database
        reviews_dict[review.get_review_id()] = review
        db['Reviews'] = reviews_dict
        db.close()

        return redirect(url_for('view_reviews', id=id))

    return render_template('submit_review.html', form=create_review_form, id=id)

@app.route('/payment', methods=['GET', 'POST'])
def payment():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    username = session.get('username', 'Unknown User')  # Get the username from the session

    if request.method == 'POST':
        # Get form data
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        card_number = request.form.get('card_number')
        expiry_date_str = request.form.get('expiry_date')
        cvc = request.form.get('cvc')

        # Validate card number
        if not re.match(r'^(4|5[1-5]|2|3)\d{15}$', card_number):
            flash('Invalid card number. It must start with 4 (VISA), 2/5 (Mastercard), or 3 (American Express) and be 16 digits long.', 'error')
            return redirect(url_for('payment'))

        # Parse and validate expiry date
        try:
            expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid expiry date format. Please use YYYY-MM-DD.', 'error')
            return redirect(url_for('payment'))

        if expiry_date.year < 2025:
            flash('Expiry date must be after 2025.', 'error')
            return redirect(url_for('payment'))

        # Validate CVC
        if not re.match(r'^\d{3}$', cvc):
            flash('Invalid CVC. It must be exactly 3 digits long.', 'error')
            return redirect(url_for('payment'))

        # Open the card database
        db = shelve.open('card.db', 'r')
        cards_dict = db.get('Cards', {})
        db.close()

        # Validate the card details
        valid_card = False
        for card_id, card in cards_dict.items():
            if (card.get_first_name() == first_name and
                card.get_last_name() == last_name and
                card.get_card_number() == card_number and
                card.get_expiry_date() == expiry_date and
                card.get_cvc_number() == cvc):
                valid_card = True
                break  # Exit the loop as soon as a valid card is found

        if valid_card:
            # Move items from cart to inventory ONLY AFTER SUCCESSFUL PAYMENT
            cart_db = shelve.open('cart.db', 'r')
            cart_dict = cart_db.get('Cart', {})
            user_cart = cart_dict.get(user_id, [])
            cart_db.close()

            # Open the inventory database
            inventory_db = shelve.open('inventory.db', 'c')
            if 'Inventory' not in inventory_db:
                inventory_db['Inventory'] = {}

            inventory_dict = inventory_db['Inventory']

            # Initialize the user's inventory if it doesn't exist
            if user_id not in inventory_dict:
                inventory_dict[user_id] = []

            # Open the ebooks database to get ebook details
            ebooks_dict = {}
            db = shelve.open('ebooks.db', 'r')
            try:
                ebooks_dict = db['Ebooks']
            except KeyError:
                flash('No ebooks found in the database.', 'error')
                return redirect(url_for('cart'))
            db.close()

            # Record the transaction in the transaction history
            transaction_db = shelve.open('transactions.db', 'c')
            if 'Transactions' not in transaction_db:
                transaction_db['Transactions'] = {}

            transactions_dict = transaction_db['Transactions']

            for ebook_id in user_cart:
                if ebook_id in ebooks_dict:
                    # Add the ebook to the user's inventory
                    inventory_dict[user_id].append(ebook_id)

                    # Create a new transaction
                    transaction = Transaction(
                        user_id=user_id,
                        username=username,
                        title=ebooks_dict[ebook_id].get_title(),
                        amount_paid=ebooks_dict[ebook_id].get_price()
                    )
                    transactions_dict[transaction.get_transaction_id()] = transaction

            # Save the updated inventory and transactions
            inventory_db['Inventory'] = inventory_dict
            inventory_db.close()

            transaction_db['Transactions'] = transactions_dict
            transaction_db.close()

            # Clear the user's cart
            cart_db = shelve.open('cart.db', 'w')
            cart_dict[user_id] = []
            cart_db['Cart'] = cart_dict
            cart_db.close()

            return redirect(url_for('thank_you'))
        else:
            # Show an error message if the card is invalid
            flash('Invalid card details. Please try again.', 'error')
            return redirect(url_for('payment'))

    # If it's a GET request, display the payment page
    cart_db = shelve.open('cart.db', 'r')
    cart_dict = cart_db.get('Cart', {})
    user_cart = cart_dict.get(user_id, [])  # Get the user's cart
    cart_db.close()

    # Get the ebooks in the user's cart
    ebooks_list = []
    db = shelve.open('ebooks.db', 'r')
    ebooks_dict = db['Ebooks']
    for ebook_id in user_cart:
        if ebook_id in ebooks_dict:
            ebooks_list.append(ebooks_dict[ebook_id])
    db.close()

    return render_template('payment.html', ebooks_list=ebooks_list)

@app.route('/delete_from_cart/<int:id>', methods=['POST'])
def delete_from_cart(id):
    if 'user_id' not in session:
        flash('You need to log in to modify your cart.', 'error')
        return redirect(url_for('login'))

    user_id = session['user_id']

    # Open the cart database
    cart_db = shelve.open('cart.db', 'w')
    if 'Cart' not in cart_db:
        cart_db['Cart'] = {}

    cart_dict = cart_db['Cart']

    # Remove the item from the user's cart
    if user_id in cart_dict and id in cart_dict[user_id]:
        cart_dict[user_id].remove(id)

    cart_db['Cart'] = cart_dict
    cart_db.close()

    return redirect(url_for('cart'))

@app.route('/add_to_cart/<int:id>', methods=['POST'])
def add_to_cart(id):
    if 'user_id' not in session:
        flash('You need to log in to add items to your cart.', 'error')
        return redirect(url_for('login'))

    user_id = session['user_id']

    # Open the ebook database to get the product details
    db = shelve.open('ebooks.db', 'r')
    ebooks_dict = db['Ebooks']
    db.close()

    # Open the cart database to add the product
    cart_db = shelve.open('cart.db', 'c')
    if 'Cart' not in cart_db:
        cart_db['Cart'] = {}

    cart_dict = cart_db['Cart']

    # Initialize the user's cart if it doesn't exist
    if user_id not in cart_dict:
        cart_dict[user_id] = []

    # Add the ebook ID to the user's cart
    if id in ebooks_dict and id not in cart_dict[user_id]:
        cart_dict[user_id].append(id)

    cart_db['Cart'] = cart_dict
    cart_db.close()

    return redirect(url_for('cart'))

@app.route('/cart', methods=['GET', 'POST'])
def cart():
    if 'user_id' not in session:
        flash('You need to log in to view your cart.', 'error')
        return redirect(url_for('login'))

    user_id = session['user_id']

    # Open the cart database (create if it doesn't exist)
    cart_dict = {}
    try:
        cart_db = shelve.open('cart.db', 'c')
        try:
            # Try to retrieve the 'Cart' dictionary
            cart_dict = cart_db.get('Cart', {})  # Use .get() to avoid KeyError
            if not cart_dict:  # If 'Cart' key doesn't exist or is empty
                cart_db['Cart'] = {}  # Initialize an empty dictionary
                cart_dict = cart_db['Cart']
        except Exception as e:
            print(f"Error accessing cart.db: {e}")
        finally:
            cart_db.close()
    except Exception as e:
        print(f"An error occurred while opening cart.db: {e}")

    # Get the user's cart
    user_cart = cart_dict.get(user_id, [])
    is_empty = len(user_cart) == 0

    # Get the ebooks in the user's cart
    ebooks_list = []
    try:
        db = shelve.open('ebooks.db', 'r')
        try:
            ebooks_dict = db['Ebooks']
            for ebook_id in user_cart:
                if ebook_id in ebooks_dict:
                    ebooks_list.append(ebooks_dict[ebook_id])
        except KeyError:
            print("No ebooks found in the database.")
        finally:
            db.close()
    except Exception as e:
        print(f"An error occurred while opening ebooks.db: {e}")

    return render_template('cart.html', ebooks_list=ebooks_list, is_empty=is_empty)


@app.route('/productpage/<int:id>', methods=['GET', 'POST'])
def productpage(id):
    ebooks_dict = {}
    db = shelve.open('ebooks.db', 'r')
    try:
        ebooks_dict = db['Ebooks']
    except KeyError:
        print("No ebooks found in the database.")
    db.close()

    ebook = ebooks_dict.get(id)
    if not ebook:
        flash('Ebook not found.', 'error')
        return redirect(url_for('store'))

    if request.method == 'POST':
        # Add the ebook to the cart
        return redirect(url_for('add_to_cart', id=id))

    return render_template('productpage.html', ebook=ebook)


@app.route("/Store")
def store():
    # Get filter parameters from the request
    selected_genre = request.args.get('genre', '')
    min_price = request.args.get('min_price', type=float, default=0.0)
    max_price = request.args.get('max_price', type=float, default=float('inf'))
    min_rating = request.args.get('min_rating', type=float, default=0.0)

    # Open the ebooks database
    ebooks_dict = {}
    db = shelve.open('ebooks.db', 'r')
    try:
        ebooks_dict = db['Ebooks']
    except KeyError:
        print("No ebooks found in the database.")
    db.close()

    # Open the reviews database (create if it doesn't exist)
    reviews_dict = {}
    is_empty = True  # Assume there are no reviews by default
    try:
        db = shelve.open('reviews.db', 'c')
        try:
            # Try to retrieve the 'Reviews' dictionary
            reviews_dict = db.get('Reviews', {})  # Use .get() to avoid KeyError
            if not reviews_dict:  # If 'Reviews' key doesn't exist or is empty
                db['Reviews'] = {}  # Initialize an empty dictionary
                reviews_dict = db['Reviews']
            is_empty = len(reviews_dict) == 0  # Check if the reviews database is empty
        except Exception as e:
            print(f"Error accessing reviews.db: {e}")
        finally:
            db.close()
    except Exception as e:
        print(f"An error occurred while opening reviews.db: {e}")

    # Filter ebooks based on genre, price range, and minimum rating
    ebooks_list = []
    for ebook in ebooks_dict.values():
        if (not selected_genre or ebook.get_genre() == selected_genre) and \
                (min_price <= ebook.get_price() <= max_price):
            # Calculate average rating and total reviews for this book
            book_reviews = [review for review in reviews_dict.values() if review.get_ebook_id() == ebook.get_ebook_id()]
            total_reviews = len(book_reviews)
            if total_reviews > 0:
                average_rating = sum(review.get_stars() for review in book_reviews) / total_reviews
            else:
                average_rating = 0

            # Apply the minimum rating filter
            if average_rating >= min_rating:
                # Add the average rating and total reviews to the ebook object
                ebook.average_rating = average_rating
                ebook.total_reviews = total_reviews
                ebooks_list.append(ebook)

    # Shuffle the ebooks_list to display books in random order
    random.shuffle(ebooks_list)

    # Get a list of unique genres for the filter dropdown
    genres = set(ebook.get_genre() for ebook in ebooks_dict.values())

    return render_template("Store.html", ebooks_list=ebooks_list, genres=genres,
                           selected_genre=selected_genre, min_price=min_price, max_price=max_price,
                           min_rating=min_rating, is_empty=is_empty)

@app.route('/book_details/<int:id>')
def display_book_details(id):
    if 'user_id' not in session:
        flash('You need to log in to view book details.', 'error')
        return redirect(url_for('login'))

    user_id = session['user_id']

    # Open the inventory database
    inventory_db = shelve.open('inventory.db', 'r')
    try:
        inventory_dict = inventory_db['Inventory']
    except KeyError:
        flash('No inventory found.', 'error')
        return redirect(url_for('inventory'))
    finally:
        inventory_db.close()

    # Get the user's inventory
    user_inventory = inventory_dict.get(user_id, [])
    if id not in user_inventory:
        flash('Ebook not found in your inventory.', 'error')
        return redirect(url_for('inventory'))

    # Open the ebooks database to get ebook details
    db = shelve.open('ebooks.db', 'r')
    try:
        ebooks_dict = db['Ebooks']
        ebook = ebooks_dict.get(id)
        if not ebook:
            flash('Ebook not found.', 'error')
            return redirect(url_for('inventory'))
    except KeyError:
        flash('No ebooks found in the database.', 'error')
        return redirect(url_for('inventory'))
    finally:
        db.close()

    return render_template("book_details.html", ebook=ebook)


@app.route('/inventory')
def inventory():
    if 'user_id' not in session:
        flash('You need to log in to view your inventory.', 'error')
        return redirect(url_for('login'))

    user_id = session['user_id']
    is_empty = True
    inventory_dict = {}

    # Open the inventory database with error handling
    try:
        inventory_db = shelve.open('inventory.db', 'r')
        try:
            inventory_dict = inventory_db.get('Inventory', {})
        except KeyError:
            print("No inventory found in the database.")
        finally:
            inventory_db.close()
    except Exception as e:
        print(f"An error occurred while opening inventory.db: {e}")

    # Get the user's inventory
    user_inventory = inventory_dict.get(user_id, [])
    is_empty = len(user_inventory) == 0

    # Get the ebooks in the user's inventory
    ebooks_list = []
    try:
        db = shelve.open('ebooks.db', 'r')
        try:
            ebooks_dict = db['Ebooks']
            for ebook_id in user_inventory:
                if ebook_id in ebooks_dict:
                    ebooks_list.append(ebooks_dict[ebook_id])
        except KeyError:
            print("No ebooks found in the database.")
        finally:
            db.close()
    except Exception as e:
        print(f"An error occurred while opening ebooks.db: {e}")

    return render_template('inventory.html', ebooks_list=ebooks_list, is_empty=is_empty)

    # Filter ebooks based on genre, price range, and minimum rating
    ebooks_list = []
    for ebook in ebooks_dict.values():
        if (not selected_genre or ebook.get_genre() == selected_genre) and \
           (min_price <= ebook.get_price() <= max_price):
            # Calculate average rating and total reviews for this book
            book_reviews = [review for review in reviews_dict.values() if review.get_ebook_id() == ebook.get_ebook_id()]
            total_reviews = len(book_reviews)
            if total_reviews > 0:
                average_rating = sum(review.get_stars() for review in book_reviews) / total_reviews
            else:
                average_rating = 0

            # Apply the minimum rating filter
            if average_rating >= min_rating:
                # Add the average rating and total reviews to the ebook object
                ebook.average_rating = average_rating
                ebook.total_reviews = total_reviews
                ebooks_list.append(ebook)

    # Shuffle the ebooks_list to display books in random order
    random.shuffle(ebooks_list)

    # Get a list of unique genres for the filter dropdown
    genres = set(ebook.get_genre() for ebook in ebooks_dict.values())

    return render_template("Store.html", ebooks_list=ebooks_list, genres=genres,
                           selected_genre=selected_genre, min_price=min_price, max_price=max_price,
                           min_rating=min_rating, is_empty=is_empty)

@app.route('/createCard', methods=['GET', 'POST'])
def create_card():
    create_card_form = CreateCardForm(request.form)
    if request.method == 'POST' and create_card_form.validate():
        cards_dict = {}
        db = shelve.open('card.db', 'c')
        try:
            cards_dict = db['Cards']
        except KeyError:
            print("Error in retrieving Cards from card.db.")

        # Create the card object
        card = Card(
            create_card_form.first_name.data,
            create_card_form.last_name.data,
            create_card_form.card_number.data,
            create_card_form.expiry_date.data,
            create_card_form.cvc_number.data
        )

        # Save the card to the database
        cards_dict[card.get_card_id()] = card
        db['Cards'] = cards_dict
        db.close()

        return redirect(url_for('retrieve_cards'))
    return render_template('createCard.html', form=create_card_form)

@app.route('/retrieveCard')
@staff_only
def retrieve_cards():
    if 'role' not in session or session['role'] not in ['Owner', 'Co-owner']:
        flash('Access denied!', 'error')
        return redirect(url_for('home'))

    cards_dict = {}
    try:
        db = shelve.open('card.db', 'c')
        try:
            # Try to retrieve the 'Cards' dictionary
            cards_dict = db.get('Cards', {})  # Use .get() to avoid KeyError
            if not cards_dict:  # If 'Cards' key doesn't exist or is empty
                db['Cards'] = {}  # Initialize an empty dictionary
                cards_dict = db['Cards']
        except Exception as e:
            print(f"Error accessing card.db: {e}")
        finally:
            db.close()
    except Exception as e:
        print(f"An error occurred while opening card.db: {e}")

    cards_list = []
    for key in cards_dict:
        card = cards_dict.get(key)
        cards_list.append(card)

    return render_template('retrieveCard.html', count=len(cards_list), cards_list=cards_list)

@app.route('/updateCard/<int:id>/', methods=['GET', 'POST'])
def update_card(id):
    update_card_form = CreateCardForm(request.form)
    if request.method == 'POST' and update_card_form.validate():
        cards_dict = {}
        db = shelve.open('card.db', 'w')
        cards_dict = db['Cards']

        card = cards_dict.get(id)
        card.set_first_name(update_card_form.first_name.data)
        card.set_last_name(update_card_form.last_name.data)
        card.set_card_number(update_card_form.card_number.data)
        card.set_expiry_date(update_card_form.expiry_date.data)
        card.set_cvc_number(update_card_form.cvc_number.data)

        db['Cards'] = cards_dict
        db.close()
        return redirect(url_for('retrieve_cards'))

    else:
        cards_dict = {}
        db = shelve.open('card.db', 'r')
        cards_dict = db['Cards']
        db.close()

        card = cards_dict.get(id)
        update_card_form.first_name.data = card.get_first_name()
        update_card_form.last_name.data = card.get_last_name()
        update_card_form.card_number.data = card.get_card_number()
        update_card_form.expiry_date.data = card.get_expiry_date()
        update_card_form.cvc_number.data = card.get_cvc_number()

        return render_template('updateCard.html', form=update_card_form)

@app.route('/deleteCard/<int:id>', methods=['POST'])
@staff_only
def delete_card(id):
    if 'role' not in session or session['role'] not in ['Staff', 'Owner', 'Co-owner']:
        flash('Access denied!', 'error')
        return redirect(url_for('home'))

    cards_dict = {}
    db = shelve.open('card.db', 'w')
    cards_dict = db['Cards']

    cards_dict.pop(id)

    db['Cards'] = cards_dict
    db.close()

    return redirect(url_for('retrieve_cards'))

@app.route('/createEbook', methods=['GET', 'POST'])
@staff_only
def create_ebook():
    if 'role' not in session or session['role'] not in ['Staff', 'Owner', 'Co-owner']:
        flash('Access denied!', 'error')
        return redirect(url_for('home'))

    create_ebook_form = CreateEbookForm(request.form)
    if request.method == 'POST' and create_ebook_form.validate():
        # Handle cover image upload
        image_file = request.files.get('image')
        image_path = None

        if image_file and allowed_file(image_file.filename):
            # Secure the filename and save it to the upload folder
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(UPLOAD_FOLDER, filename)
            image_file.save(image_path)

        # Handle book content upload
        content_file = request.files.get('content')
        content_path = None

        if content_file and content_file.filename.endswith('.pdf'):
            # Secure the filename and save it to the upload folder
            filename = secure_filename(content_file.filename)
            content_path = os.path.join(UPLOAD_FOLDER, filename)
            content_file.save(content_path)

        # Create the ebook object
        ebook = Ebook(
            create_ebook_form.title.data,
            create_ebook_form.author.data,
            create_ebook_form.description.data,
            create_ebook_form.price.data,
            create_ebook_form.genre.data,
            image_path,  # Save the cover image file path
            content_path  # Save the book content file path
        )

        # Save the ebook to the database
        ebooks_dict = {}
        db = shelve.open('ebooks.db', 'c')
        try:
            ebooks_dict = db['Ebooks']
        except KeyError:
            print("Error in retrieving Ebooks from ebooks.db.")
        ebooks_dict[ebook.get_ebook_id()] = ebook
        db['Ebooks'] = ebooks_dict
        db.close()

        return redirect(url_for('retrieve_ebooks'))
    return render_template('createEbook.html', form=create_ebook_form)

@app.route('/retrieveEbooks')
@staff_only
def retrieve_ebooks():
    if 'role' not in session or session['role'] not in ['Staff', 'Owner', 'Co-owner']:
        flash('Access denied!', 'error')
        return redirect(url_for('home'))
    ebooks_dict = {}
    db = shelve.open('ebooks.db', 'r')
    try:
        ebooks_dict = db['Ebooks']
    except KeyError:
        print("No ebooks found in the database.")
    db.close()

    ebooks_list = list(ebooks_dict.values())
    return render_template('retrieveEbooks.html', count=len(ebooks_list), ebooks_list=ebooks_list)

@app.route('/updateEbook/<int:id>/', methods=['GET', 'POST'])
@staff_only
def update_ebook(id):
    if 'role' not in session or session['role'] not in ['Staff', 'Owner', 'Co-owner']:
        flash('Access denied!', 'error')
        return redirect(url_for('home'))

    update_ebook_form = CreateEbookForm(request.form)
    if request.method == 'POST' and update_ebook_form.validate():
        ebooks_dict = {}
        db = shelve.open('ebooks.db', 'w')
        ebooks_dict = db['Ebooks']

        ebook = ebooks_dict.get(id)
        ebook.set_title(update_ebook_form.title.data)
        ebook.set_author(update_ebook_form.author.data)
        ebook.set_description(update_ebook_form.description.data)
        ebook.set_price(update_ebook_form.price.data)
        ebook.set_genre(update_ebook_form.genre.data)

        # Handle image upload
        image_file = request.files.get('image')
        if image_file and allowed_file(image_file.filename):
            # Delete the old image if it exists
            if ebook.get_image() and os.path.exists(ebook.get_image()):
                os.remove(ebook.get_image())

            # Save the new image
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(UPLOAD_FOLDER, filename)
            image_file.save(image_path)
            ebook.set_image(image_path)

        # Handle content upload
        content_file = request.files.get('content')
        if content_file and content_file.filename.endswith('.pdf'):
            # Delete the old content if it exists
            if ebook.get_content_path() and os.path.exists(ebook.get_content_path()):
                os.remove(ebook.get_content_path())

            # Save the new content
            filename = secure_filename(content_file.filename)
            content_path = os.path.join(UPLOAD_FOLDER, filename)
            content_file.save(content_path)
            ebook.set_content_path(content_path)

        db['Ebooks'] = ebooks_dict
        db.close()
        return redirect(url_for('retrieve_ebooks'))

    else:
        ebooks_dict = {}
        db = shelve.open('ebooks.db', 'r')
        ebooks_dict = db['Ebooks']
        db.close()

        ebook = ebooks_dict.get(id)
        update_ebook_form.title.data = ebook.get_title()
        update_ebook_form.author.data = ebook.get_author()
        update_ebook_form.description.data = ebook.get_description()
        update_ebook_form.price.data = ebook.get_price()
        update_ebook_form.genre.data = ebook.get_genre()

        return render_template('updateEbook.html', form=update_ebook_form, ebook=ebook)

@app.route('/deleteEbook/<int:id>', methods=['POST'])
@staff_only
def delete_ebook(id):
    if 'role' not in session or session['role'] not in ['Staff', 'Owner', 'Co-owner']:
        flash('Access denied!', 'error')
        return redirect(url_for('home'))

    ebooks_dict = {}
    db = shelve.open('ebooks.db', 'w')
    try:
        ebooks_dict = db['Ebooks']
        if id in ebooks_dict:
            # Remove the ebook from the database
            del ebooks_dict[id]
            db['Ebooks'] = ebooks_dict

        else:
            flash('Ebook not found.', 'error')
    except KeyError:
        flash('No ebooks found in the database.', 'error')
    db.close()

    return redirect(url_for('retrieve_ebooks'))

@app.route('/process_refund/<int:transaction_id>', methods=['POST'])
def process_refund(transaction_id):
    if 'user_id' not in session:
        flash('You need to log in to process a refund.', 'error')
        return redirect(url_for('login'))

    user_id = session['user_id']
    role = session.get('role', 'User')

    # Open the transactions database
    transaction_db = shelve.open('transactions.db', 'c')
    transactions_dict = transaction_db.get('Transactions', {})

    # Find the transaction
    transaction = transactions_dict.get(transaction_id)
    if not transaction:
        flash('Transaction not found.', 'error')
        return redirect(url_for('transaction_history'))

    # Check if the user is staff or the transaction belongs to the logged-in user
    if role not in ['Staff', 'Owner', 'Co-owner'] and transaction.get_user_id() != user_id:
        flash('You do not have permission to refund this transaction.', 'error')
        return redirect(url_for('transaction_history'))

    # Check if the transaction is already refunded
    if transaction.get_refund_status() == "Refunded":
        flash('This transaction has already been refunded.', 'error')
        return redirect(url_for('transaction_history'))

    # Open the inventory database
    inventory_db = shelve.open('inventory.db', 'c')
    inventory_dict = inventory_db.get('Inventory', {})

    # Remove the book from the user's inventory
    user_inventory = inventory_dict.get(transaction.get_user_id(), [])
    ebook_id_to_remove = None

    # Find the ebook ID associated with the transaction
    db = shelve.open('ebooks.db', 'r')
    ebooks_dict = db.get('Ebooks', {})
    for ebook_id, ebook in ebooks_dict.items():
        if ebook.get_title() == transaction.get_title():
            ebook_id_to_remove = ebook_id
            break
    db.close()

    if ebook_id_to_remove and ebook_id_to_remove in user_inventory:
        user_inventory.remove(ebook_id_to_remove)
        inventory_dict[transaction.get_user_id()] = user_inventory
        inventory_db['Inventory'] = inventory_dict

        # Update the transaction's refund status
        transaction.set_refund_status("Refunded")
        transactions_dict[transaction_id] = transaction
        transaction_db['Transactions'] = transactions_dict

        flash('Refund processed successfully. The book has been removed from the user\'s inventory.', 'success')
    else:
        flash('Failed to process refund. The book was not found in the user\'s inventory.', 'error')

    inventory_db.close()
    transaction_db.close()

    return redirect(url_for('transaction_history'))

@app.route('/transaction_history')
def transaction_history():
    if 'user_id' not in session:
        flash('You need to log in to view transaction history.', 'error')
        return redirect(url_for('login'))

    user_id = session['user_id']
    role = session.get('role', 'User')

    # Open the transactions database
    transaction_db = shelve.open('transactions.db', 'r')
    transactions_dict = transaction_db.get('Transactions', {})
    transaction_db.close()

    # Filter transactions based on user role
    if role in ['Staff', 'Owner', 'Co-owner']:
        # Staff can view all transactions
        transactions_list = list(transactions_dict.values())
    else:
        # Regular users can only view their own transactions
        transactions_list = [t for t in transactions_dict.values() if t.get_user_id() == user_id]

    return render_template('transaction_history.html', transactions=transactions_list, role=role)


# Load the last used ebook_id from the database
def load_last_ebook_id():
    try:
        with shelve.open('ebooks.db', 'r') as db:
            ebooks_dict = db.get('Ebooks', {})
            if ebooks_dict:
                last_id = max(ebooks_dict.keys())
                Ebook.count_id = last_id
    except Exception as e:
        print(f"Error loading last ebook_id: {e}")

# Call this function when the application starts
load_last_ebook_id()

# Load the last used card_id from the database
def load_last_card_id():
    try:
        with shelve.open('card.db', 'r') as db:
            cards_dict = db.get('Cards', {})
            if cards_dict:
                last_id = max(cards_dict.keys())
                Card.count_id = last_id
    except Exception as e:
        print(f"Error loading last card_id: {e}")

# Call this function when the application starts
load_last_card_id()

def load_last_review_id():
    try:
        with shelve.open('reviews.db', 'r') as db:
            reviews_dict = db.get('Reviews', {})
            if reviews_dict:
                last_id = max(reviews_dict.keys())
                Review.count_id = last_id
    except Exception as e:
        print(f"Error loading last review_id: {e}")

# Call this function when the application starts
load_last_review_id()


if __name__ == "__main__":
    app.run()
