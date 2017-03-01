import random, string, httplib2
import unirest
import json
import uuid
from flask import Flask, render_template, url_for, request, session as login_session, make_response, abort, json, redirect
from flask import flash
app = Flask(__name__)
from sqlalchemy import create_engine, update
from sqlalchemy.orm import sessionmaker
from checkstubdb import Check,Check_2, User, Base
from cred import location_id, access_token

# engine and db connection
engine = create_engine('postgresql://daniel:Seven11ok@localhost/stub')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

app.secret_key = 'super duper key'

@app.route('/testlogin/')
def test_login():
    # create anti-forgery state token
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('fblogin.html',state=state)

@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print "access token received %s " % access_token

    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
        app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.4/me"
    # strip expire tag from access token
    token = result.split("&")[0]


    url = 'https://graph.facebook.com/v2.4/me?%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    # print "url sent for API access:%s"% url
    # print "API JSON result: %s" % result
    data = json.loads(result)
#    login_session['provider'] = 'facebook'
#    login_session['username'] = data["name"]
#    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to properly logout, let's strip out the information before the equals sign in our token
    stored_token = token.split("=")[1]
    login_session['access_token'] = stored_token
    login_session['facebook_id'] = data["id"]
    login_session['state'] = state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))

    # see if user exists
    try:
        user = session.query(User).filter_by(f_id=data['id']).one()
        login_session['email'] = data['email']
    # if user doesnt exist create user
    except:
        email = data['email']
        new_user = User(name=email,f_id=data['id'])
        session.add(new_user)
        session.commit()
        login_session['email'] = email

    # Get user picture
    url = 'https://graph.facebook.com/v2.4/me/picture?%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]
#    login_session['user_id'] = user_id

    output = ''
#    output += '<h1>Welcome, '
#    output += login_session['email']

#    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 200px; height: 200px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '

    # flash("Now logged in as %s" % login_session['username'])
    return output

@app.route('/')
@app.route('/checkstub/', methods=['GET','POST'])
def check_stub():
    """ view for creating and editing a stub
        visitors are first redirected to fb login
        In POST membership and check count are checked. If complementary check
        has been used, users are redirected to square payment ui.
        After verification, membership is set to True.
    """
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    
    if request.method == 'POST':
        if 'facebook_id' not in login_session or 'state' not in login_session:
            return redirect(url_for('test_login'))
        
        user = session.query(User).filter_by(name=login_session['email']).one()

        # if a user is not a member and has made thier first complimentary statement
        # they are redirected to the square checkout ui
        if user.is_member == False and user.check_count >= 1:
            # eventually put this in a helper function
            response = unirest.post('https://connect.squareup.com/v2/locations/' + location_id + '/checkouts',
                                headers={'Accept': 'appication/json',
                                         'Content-Type': 'application/json',
                                         'Authorization': 'Bearer ' + access_token,
                                         },
                                params = json.dumps({
                                    
                                    #'redirect_url': '',
                                    'idempotency_key': str(uuid.uuid1()),
                                    'ask_for_shipping_address': True,
                                    'merchant_support_email': 'dannyglv182@gmail.com',
                                    'order': {
                                        'reference_id': "089ab4dc",
                                        #'reference_id': "".join(random.choice(string.ascii_uppercase + \
                                        #                                      string.digits) for i in range(20)),
                                        'line_items': [
                                            {
                                                'name': "stub",
                                                'quantity': '1',
                                                'base_price_money':{
                                                    'amount': 400,
                                                    'currency': 'USD'

                                                    }

                                                },
                                            ]
                                        },
                                    
                                    "pre_populate_buyer_email": "prepopemail@gmail.com",
                                    "pre_populate_shipping_address": {
                                        "first_name": "first name",
                                        "last_name": "last name"
                                    }
                                    }))
            
            result = response.body['checkout']
            checkout_page = result['checkout_page_url']
            checkout_id = result['id']
            print result['checkout_page_url']
            print result['id']
            return redirect(checkout_page)
        else:
            # user is a member and can create stubs or user is making
            # complimentary statements
            newCheck = Check(emp_name=request.form['emp_name'],
                             social=request.form['social'],
                             rep_period=request.form['rep_period'],
                             pay_date=request.form['pay_date'],
                             emp_num=request.form['emp_num'],
                             rate=request.form['rate'],
                             hours=request.form['hours'],
                             current_pay=request.form['current_pay'],
                             fica_medi=request.form['fica_medi'],
                             fica_social=request.form['fica_social'],
                             fica_medi_ytd=request.form['fica_medi_ytd'],
                             fica_social_ytd=request.form['fica_social_ytd'],
                             fed_tax=request.form['fed_tax'],
                             fed_ytd=request.form['fed_ytd'],
                             state_tax=request.form['state_tax'],
                             state_ytd=request.form['state_ytd'],
                             creator=user.id)
            user.check_count +=1
            session.add(newCheck)
            session.add(user)
            session.commit()
            return redirect(url_for('my_home'))
    if 'facebook_id' in login_session and 'state' in login_session:
        return render_template('loggedinfront.html')
    return render_template('checkstub.html',state=state)

@app.route('/templateone')
def main_template():
    """ Page for creating stubs with template one for
        members
    """
    if 'facebook_id' in login_session and 'state' in login_session:
        return render_template('templateone.html')
    else:
        abort(403)

@app.route('/fullpageprint')
def full_page_print():
    """ full page print """
    return render_template('fullpage.html')

@app.route('/templatethree', methods=['GET','POST'])
def full_page_template():
    """
    if 'facebook_id' in login_session and 'state' in login_session:
        return render_template('templatethree.html')
    else:
        abort(403)
    """
    if request.method == 'POST':
        new_statement = Check_2(creator=1,
                               company_name=request.form['company_name'],
                               company_address=request.form['company_address'],
                               company_city=request.form['company_city'],
                               pay_period=request.form['pay_period'],
                               pay_date=request.form['pay_date'],
                               status=request.form['status'],
                               exemptions=request.form['exemptions'],
                               emp_name=request.form['emp_name'],
                               emp_address=request.form['emp_address'],
                               emp_city_state_zip=request.form['emp_city_state_zip'],
                               reg_rate=request.form['reg_rate'],
                               reg_hours=request.form['reg_hours'],
                               reg_period=request.form['reg_period'],
                               reg_ytd=request.form['reg_ytd'],
                               ov_rate=request.form['ov_rate'],
                               ov_period=request.form['ov_period'],
                               ov_ytd=request.form['ov_ytd'],
                               vac_rate=request.form['vac_rate'],
                               vac_hours=request.form['vac_hours'],
                               vac_period=request.form['vac_period'],
                               vac_ytd=request.form['vac_ytd'],
                               gross_period=request.form['gross_period'],
                               gross_ytd=request.form['gross_ytd'],
                               fed_period=request.form['fed_period'],
                               fed_ytd=request.form['fed_ytd'],
                               soc_period=request.form['soc_period'],
                               soc_ytd=request.form['soc_ytd'],
                               state_selection=request.form['state_selection'],
                               state_period=request.form['state_period'],
                               state_ytd=request.form['state_ytd'],
                               net_pay=request.form['net_pay'],
                               comments=request.form['comments']
                               )
        session.add(new_statement)
        session.commit()
        return (redirect(url_for('full_page_template')))
    return render_template('templatethree.html')

@app.route('/yourstub/<int:check_id>/')
def viewCheck(check_id):
    """view for checkstub completed by user. Only creator has access"""
    # non logged in user is is denied permission
    if 'facebook_id' not in login_session or 'state' not in login_session:
        return abort(403)

    # user is logged in and either granted or denied permission
    user = session.query(User).filter_by(f_id=login_session['facebook_id']).one()
    try:
        # check if stub exists
        check = session.query(Check).filter_by(id=check_id).one()
    except:
        return abort(404)
    
    if user.id != check.creator:
        return abort(403)
    else:
        return render_template('checkstub_done.html',check=check)

@app.route('/myhome')
def my_home():
    """ membership home page with opitions to create stub from template or
        view created stubs
    """
    # logged in user with csrf token is directed home all others get 403 
    if 'facebook_id' in login_session and 'state' in login_session:
        user = session.query(User).filter_by(f_id=login_session['facebook_id']).one()
        stubs = session.query(Check).filter_by(creator=user.id)
        return render_template('myhome.html', stubs=stubs)
    else:
        abort(403)

@app.route('/thankyou/')
def thank_you():

    # once site is on aws get transaction id, checkout id and reference id
    # from the url and compare to originals for verification

    # transaction_id = request.args.get('')
    # checkout_id = request.args.get('')
    # reference_id = request.args.get('')

    return render_template('thankyou.html')

@app.route('/squarepayment/', methods=['GET','POST'])
def square():
    """ square payment form and post to process payment"""
    
    if request.method == "POST":

        # make the request to charge endpoint, completing transaction
        card_nonce = request.form['nonce']
        response = unirest.post('https://connect.squareup.com/v2/locations/' + location_id + '/transactions',
                                headers={'Accept': 'application/json',
                                         'Content-Type': 'application/json',
                                         'Authorization': 'Bearer ' + access_token,
                                         },
                                params = json.dumps({'card_nonce': card_nonce,
                                                     'amount_money': {'amount': 100,
                                                                      'currency': 'USD'
                                                                      },
                                                     'idempotency_key': str(uuid.uuid1())
                                                     })
                                )
        
        print response.body
        return 'response printed'
    return render_template('squaretrans.html')

# UTILITY FUNCTIONS FOR TESTING
@app.route('/users')
def print_users():
    users = session.query(User).all()
    for i in users:
        print i.name
        print i.f_id
    return 'users printed'

@app.route('/membershipstatus/')
def switch_membership_status():
    user = session.query(User).filter_by(f_id=login_session['facebook_id']).one()
    if user.is_member == False:
        user.is_member = True
        session.add(user)
        session.commit()
        print user.is_member
        return 'membership status switched'
    else:
        user.is_member = False
        session.add(user)
        session.commit()
        print user.is_member
        return 'membership status switched'
    
if __name__ == '__main__':
    app.debug = True
    app.run(host = '0.0.0.0', port = 5000)
