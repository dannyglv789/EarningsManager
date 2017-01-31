import random, string, httplib2
import unirest
import json
import uuid
from flask import Flask, render_template, url_for, request, session as login_session, make_response, abort, json, redirect
app = Flask(__name__)
from sqlalchemy import create_engine, update
from sqlalchemy.orm import sessionmaker
from checkstubdb import Check,User, Base
from locations_test import location_id

# engine and db connection
engine = create_engine('sqlite:///checkstub.db')
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
    login_session['provider'] = 'facebook'
#    login_session['username'] = data["name"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to properly logout, let's strip out the information before the equals sign in our token
    stored_token = token.split("=")[1]
    login_session['access_token'] = stored_token

    # see if user exists
    try:
        user = session.query(User).filter_by(name=data['email']).one()
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
    output += '<h1>Welcome, '
    output += login_session['email']

    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '

    # flash("Now logged in as %s" % login_session['username'])
    return output

@app.route('/')
@app.route('/checkstub/', methods=['GET','POST'])
def check_stub():
    """ view for creating and editing a stub"""
    if request.method == 'POST':
        if 'email' not in login_session:
            return redirect(url_for('test_login'))
        
        user = session.query(User).filter_by(name=login_session['email']).one()

        # if a user is not a member and has made thier first complimentary check
        # they are redirected to the sign up page
        if user.is_member == False and user.check_count >= 1:
            return 'sign up'
        else:
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
            return render_template('checkstub.html')
    return render_template('checkstub.html')

@app.route('/yourstub/<int:check_id>/')
def viewCheck(check_id):
    """view for checkstub completed by user. Only creator has access"""
    # non logged in user is redirected to login
    if 'facebook_id' not in login_session:
        return 'you must login'

    # user is logged in and either granted or denied permission
    user = session.query(User).filter_by(f_id=login_session['facebook_id']).one()

    try:
        # check if stub exists
        check = session.query(Check).filter_by(id=check_id).one()
    except:
        return '404 not found', 404
    
    if user.id != check.creator:
        return abort(403)
    else:
        return render_template('checkstub_done.html',check=check)

@app.route('/mystubs/')
def my_stubs():
    """ stubs are queried by user id. Only creator has access"""
    # non logged in user is redirected to login
    if 'facebook_id' not in login_session:
        return 'you must login'
    
    user = session.query(User).filter_by(f_id=login_session['facebook_id']).one()
    stubs = session.query(Check).filter_by(creator=user.id)
    return render_template('mychecks.html', stubs=stubs)

@app.route('/squarepayment/', methods=['GET','POST'])
def square():
    """ square payment page and post to process payment"""
    access_token = 'sandbox-sq0atb-AuykGFFuHYzEFDweaQpdyA'
    
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

@app.route('/users')
def print_users():
    users = session.query(User).all()
    for i in users:
        print i.name
        print i.f_id
    return 'users printed'

if __name__ == '__main__':
    app.debug = True
    app.run(host = '0.0.0.0', port = 5000)
