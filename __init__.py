from flask import Flask, render_template, request, redirect, url_for
from Forms import CreateCardForm
import shelve, Card

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def create_card():
    create_card_form = CreateCardForm(request.form)
    if request.method == 'POST' and create_card_form.validate():
        cards_dict = {}
        db = shelve.open('card.db', 'c')
        try:
            cards_dict = db['Cards']
        except:
            print("Error in retrieving Cards from card.db.")
        card = Card.Card(create_card_form.first_name.data, create_card_form.last_name.data,
                         create_card_form.card_number.data, create_card_form.expiry_date.data, create_card_form.cvc_number.data)
        cards_dict[card.get_card_id()] = card
        db['Cards'] = cards_dict
        
        db.close()
        return redirect(url_for('retrieve_cards'))
    return render_template('createCard.html', form=create_card_form)

@app.route('/retrieveCard')
def retrieve_cards():
    cards_dict = {}
    db = shelve.open('card.db', 'r')
    cards_dict = db['Cards']
    db.close()

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

@app.route('/deleteUser/<int:id>', methods=['POST'])
def delete_card(id):
    cards_dict = {}
    db = shelve.open('card.db', 'w')
    cards_dict = db['Cards']

    cards_dict.pop(id)

    db['Cards'] = cards_dict
    db.close()

    return redirect(url_for('retrieve_cards'))

if __name__=='__main__':
    app.run()