from flask import Flask, render_template, request, redirect, url_for
from Forms import CreateUserForm, CreateCustomerForm, CreateEbookForm

import shelve, User, Customer

import uuid

app = Flask(__name__)
app.debug = True


@app.route('/')
def home():
    return render_template('home.html')
@app.route('/createEbook', methods=['GET', 'POST'])
def create_ebook():
    form = CreateEbookForm(request.form)
    if request.method == 'POST' and form.validate():
        ebooks_dict = {}
        db = shelve.open('ebooks.db', 'c')

        try:
            ebooks_dict = db['Ebooks']
        except KeyError:
            print("Error in retrieving Ebooks from ebooks.db.")

        ebook_id = str(uuid.uuid4())  # Unique ID for the ebook
        ebook = {
            'title': form.title.data,
            'description': form.description.data,
            'author': form.author.data,
            'ebook_id': ebook_id,
            'genre': form.genre.data,
        }

        ebooks_dict[ebook_id] = ebook
        db['Ebooks'] = ebooks_dict

        db.close()

        return redirect(url_for('retrieve_ebooks'))
    return render_template('createEbook.html', form=form)
@app.route('/ebooks')
def retrieving_ebooks():
    with shelve.open('ebooks.db', 'r') as db:
        ebooks_dict = db.get('Ebooks', {})
        ebooks_list = list(ebooks_dict.values())  # Convert dictionary values to a list
    return render_template('ebook.html', ebooks_list=ebooks_list)
@app.route('/retrieveEbooks')
def retrieve_ebooks():
    ebooks_dict = {}
    db = shelve.open('ebooks.db', 'r')
    ebooks_dict = db['Ebooks']
    db.close()

    ebooks_list = []
    for key in ebooks_dict:
        ebook = ebooks_dict.get(key)
        ebooks_list.append(ebook)

    return render_template('retrieveEbooks.html', ebooks_list=ebooks_list)

@app.route('/deleteEbook/<ebook_id>', methods=['POST'])
def delete_ebook(ebook_id):
    with shelve.open('ebooks.db', writeback=True) as db:
        ebooks_dict = db.get('Ebooks', {})
        if ebook_id in ebooks_dict:
            del ebooks_dict[ebook_id]
            db['Ebooks'] = ebooks_dict  # Update the shelve database
    return redirect(url_for('retrieve_ebooks'))



@app.route('/contactUs')
def contact_us():
    return render_template('contactUs.html')
@app.route('/ebooks')
def ebooks():
    return render_template('ebook.html')


@app.route('/createUser', methods=['GET', 'POST'])
def create_user():
    create_user_form = CreateUserForm(request.form)
    if request.method == 'POST' and create_user_form.validate():
        users_dict = {}
        db = shelve.open('user.db', 'c')

        try:
            users_dict = db['Users']
        except:
            print("Error in retrieving Users from user.db.")

        user = User.User(create_user_form.first_name.data, create_user_form.last_name.data, create_user_form.gender.data, create_user_form.membership.data, create_user_form.remarks.data)
        users_dict[user.get_user_id()] = user
        db['Users'] = users_dict

        db.close()

        return redirect(url_for('retrieve_users'))
    return render_template('createUser.html', form=create_user_form)

@app.route('/createCustomer', methods=['GET', 'POST'])
def create_customer():
    create_customer_form = CreateCustomerForm(request.form)
    if request.method == 'POST' and create_customer_form.validate():
        customers_dict = {}
        db = shelve.open('customer.db', 'c')

        try:
            customers_dict = db['Customers']
        except:
            print("Error in retrieving Customers from customer.db.")

        customer = Customer.Customer(create_customer_form.first_name.data, create_customer_form.last_name.data,
                                     create_customer_form.gender.data, create_customer_form.membership.data,
                                     create_customer_form.remarks.data, create_customer_form.email.data,
                                     create_customer_form.date_joined.data, create_customer_form.address.data)
##        customers_dict[customer.get_customer_id()] = customer
        customers_dict[customer.get_user_id()] = customer
        db['Customers'] = customers_dict

        db.close()

        return redirect(url_for('retrieve_customers'))
    return render_template('createCustomer.html', form=create_customer_form)

@app.route('/retrieveUsers')
def retrieve_users():
    users_dict = {}
    db = shelve.open('user.db', 'r')
    users_dict = db['Users']
    db.close()

    users_list = []
    for key in users_dict:
        user = users_dict.get(key)
        users_list.append(user)

    return render_template('retrieveUsers.html', count=len(users_list), users_list=users_list)

@app.route('/retrieveCustomers')
def retrieve_customers():
    customers_dict = {}
    db = shelve.open('customer.db', 'r')
    customers_dict = db['Customers']
    db.close()

    customers_list = []
    for key in customers_dict:
        customer = customers_dict.get(key)
        customers_list.append(customer)

    return render_template('retrieveCustomers.html', count=len(customers_list), customers_list=customers_list)


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
            ebook['genre'] = request.form['genre']
            db['Ebooks'] = ebooks_dict
            return redirect(url_for('retrieve_ebooks'))

    return render_template('updateEbook.html', ebook=ebook)

@app.route('/updateUser/<int:id>/', methods=['GET', 'POST'])
def update_user(id):
    update_user_form = CreateUserForm(request.form)
    if request.method == 'POST' and update_user_form.validate():
        users_dict = {}
        db = shelve.open('user.db', 'w')
        users_dict = db['Users']

        user = users_dict.get(id)
        user.set_first_name(update_user_form.first_name.data)
        user.set_last_name(update_user_form.last_name.data)
        user.set_gender(update_user_form.gender.data)
        user.set_membership(update_user_form.membership.data)
        user.set_remarks(update_user_form.remarks.data)

        db['Users'] = users_dict
        db.close()

        return redirect(url_for('retrieve_users'))
    else:
        users_dict = {}
        db = shelve.open('user.db', 'r')
        users_dict = db['Users']
        db.close()

        user = users_dict.get(id)
        update_user_form.first_name.data = user.get_first_name()
        update_user_form.last_name.data = user.get_last_name()
        update_user_form.gender.data = user.get_gender()
        update_user_form.membership.data = user.get_membership()
        update_user_form.remarks.data = user.get_remarks()

        return render_template('updateUser.html', form=update_user_form)

@app.route('/updateCustomer/<int:id>/', methods=['GET', 'POST'])
def update_customer(id):
    update_customer_form = CreateCustomerForm(request.form)
    if request.method == 'POST' and update_customer_form.validate():
        customers_dict = {}
        db = shelve.open('customer.db', 'w')
        customers_dict = db['Customers']

        customer = customers_dict.get(id)
        customer.set_first_name(update_customer_form.first_name.data)
        customer.set_last_name(update_customer_form.last_name.data)
        customer.set_gender(update_customer_form.gender.data)
        customer.set_email(update_customer_form.email.data)
        customer.set_date_joined(update_customer_form.date_joined.data)
        customer.set_address(update_customer_form.address.data)
        customer.set_membership(update_customer_form.membership.data)
        customer.set_remarks(update_customer_form.remarks.data)

        db['Customers'] = customers_dict
        db.close()

        return redirect(url_for('retrieve_customers'))
    else:
        customers_dict = {}
        db = shelve.open('customer.db', 'r')
        customers_dict = db['Customers']
        db.close()

        customer = customers_dict.get(id)
        update_customer_form.first_name.data = customer.get_first_name()
        update_customer_form.last_name.data = customer.get_last_name()
        update_customer_form.gender.data = customer.get_gender()
        update_customer_form.email.data = customer.get_email()
        update_customer_form.date_joined.data = customer.get_date_joined()
        update_customer_form.address.data = customer.get_address()
        update_customer_form.membership.data = customer.get_membership()
        update_customer_form.remarks.data = customer.get_remarks()

        return render_template('updateCustomer.html', form=update_customer_form)

@app.route('/deleteUser/<int:id>', methods=['POST'])
def delete_user(id):
    users_dict = {}
    db = shelve.open('user.db', 'w')
    users_dict = db['Users']

    users_dict.pop(id)

    db['Users'] = users_dict
    db.close()

    return redirect(url_for('retrieve_users'))

@app.route('/deleteCustomer/<int:id>', methods=['POST'])
def delete_customer(id):
    customers_dict = {}
    db = shelve.open('customer.db', 'w')
    customers_dict = db['Customers']
    customers_dict.pop(id)

    db['Customers'] = customers_dict
    db.close()

    return redirect(url_for('retrieve_customers'))

if __name__ == '__main__':
    app.run()

