from flask import Flask, render_template, request, redirect, url_for
from Forms import CreateUserForm

import shelve, User

app = Flask(__name__)
app.debug = True


@app.route('/')
def home():
    return render_template('home.html')

@app.route('/createUser', methods=['GET', 'POST'])
def create_user():
    create_user_form = CreateUserForm(request.form)
    if request.method == 'POST' and create_user_form.validate():
        users_dict = {}
        db = shelve.open('user.db', 'c')

        try:
            users_dict = db['Users']
        except KeyError:
            print("Error in retrieving Users from user.db.")

        user = User.User(
            create_user_form.name.data,
            create_user_form.title.data,
            create_user_form.amount_paid.data,
            "Yes"  # Default refund status set to "Yes"
        )

        user_id = user.get_user_id()
        users_dict[user_id] = user
        db['Users'] = users_dict

        db.close()
        return redirect(url_for('customerTransactionHistory'))
    return render_template('createUser.html', form=create_user_form)

@app.route('/toggleRefund/<int:id>', methods=['POST'])
def toggle_refund(id):
    db = shelve.open('user.db', 'w')
    users_dict = db.get('Users', {})

    user = users_dict.get(id)
    if user:
        # Toggle refund status
        current_status = user.get_refund_status()
        new_status = "Not Refunded" if current_status == "Refunded" else "Refunded"
        user.set_refund_status(new_status)
        users_dict[id] = user

        db['Users'] = users_dict

    db.close()
    return redirect(url_for('customerTransactionHistory'))

@app.route('/customerTransactionHistory', methods=['GET'])
def customerTransactionHistory():
    # Get the query parameters from the URL
    name_filter = request.args.get('name_filter', '')
    user_id_filter = request.args.get('user_id_filter', '')

    # Open the database (shelve)
    db = shelve.open('user.db', 'r')

    try:
        users_dict = db['Users']
    except KeyError:
        users_dict = {}

    db.close()

    # Apply filtering if filters are provided
    if name_filter:
        users_list = [user for user in users_dict.values() if name_filter.lower() in user.get_name().lower()]
    else:
        users_list = list(users_dict.values())

    if user_id_filter:
        users_list = [user for user in users_list if str(user.get_user_id()) == user_id_filter]

    return render_template('customerTransactionHistory.html', users_list=users_list)

@app.route('/updateEbook/<ebook_id>', methods=['GET', 'POST'])
def update_ebook(ebook_id):
    with shelve.open('ebooks.db', 'c') as db:
        ebooks_dict = db.get('Ebooks', {})

        ebook = ebooks_dict.get(ebook_id)
        if not ebook:
            return "eBook not found.", 404

        if request.method == 'POST':
            ebook['title'] = request.form['title']
            ebook['description'] = request.form['description']
            ebook['author'] = request.form['author']
            ebooks_dict[ebook_id] = ebook
            db['Ebooks'] = ebooks_dict
            return redirect(url_for('retrieve_ebooks'))

    return render_template('updateEbook.html', ebook=ebook)

@app.route('/updateUser/<int:id>/', methods=['GET', 'POST'])
def update_user(id):
    update_user_form = CreateUserForm(request.form)
    if request.method == 'POST' and update_user_form.validate():
        users_dict = {}
        db = shelve.open('user.db', 'w')
        users_dict = db.get('Users', {})

        user = users_dict.get(id)
        if user:
            # Update user attributes from the form
            user.set_name(update_user_form.name.data)
            user.set_title(update_user_form.title.data)
            user.set_amount_paid(update_user_form.amount_paid.data)
            user.set_refund_status(update_user_form.refund_status.data)

            # Save the updated users dictionary back to the database
            db['Users'] = users_dict

        db.close()
        return redirect(url_for('customerTransactionHistory'))
    else:
        users_dict = {}
        db = shelve.open('user.db', 'r')
        users_dict = db.get('Users', {})
        db.close()

        user = users_dict.get(id)
        if user:
            # Populate the form with the user's existing data
            update_user_form.name.data = user.get_name()
            update_user_form.title.data = user.get_title()
            update_user_form.amount_paid.data = user.get_amount_paid()
            update_user_form.refund_status.data = user.get_refund_status()

        return render_template('updateUser.html', form=update_user_form)

@app.route('/deleteUser/<int:id>', methods=['POST'])
def delete_user(id):
    users_dict = {}
    db = shelve.open('user.db', 'w')
    users_dict = db['Users']

    users_dict.pop(id)

    db['Users'] = users_dict
    db.close()

    return redirect(url_for('retrieve_users'))


if __name__ == '__main__':
    app.run()


