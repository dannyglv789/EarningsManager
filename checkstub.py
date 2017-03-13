from datetime import datetime, timedelta
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
from cred import secret_key, location_id, access_token

# engine and db connection
engine = create_engine('postgresql://daniel:Seven11ok@localhost/stub')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

app.secret_key = secret_key

# HELPER FUNCTIONS 
def check_login_and_csrf():
    """Check if user is logged in and csrf token is in session"""
    if 'facebook_id' in login_session and 'state' in login_session:
        return True 
    else:
        return False

# ---- LOGIN IN/OUT AND PROFILE PAGE FUNCTIONS ----
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

    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 200px; height: 200px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    return output

@app.route('/logout/')
def logout():
    if check_login_and_csrf() == True:
        login_session.pop("access_token")
        login_session.pop("facebook_id")
        login_session.pop("state")
        login_session.pop("email")
        return redirect(url_for("check_stub"))
    
@app.route('/fullpagepreview')
def full_page_preview():
    return render_template('fullpagepreview.html')

@app.route('/myhome/')
def my_home():
    """ membership home page with opitions to create stub from template or
        view created stubs
    """
    # logged in user with csrf token is directed home all others get 403 
    if 'facebook_id' in login_session and 'state' in login_session:
        user = session.query(User).filter_by(f_id=login_session['facebook_id']).one()
        stubs = session.query(Check).filter_by(creator=user.id)
        statements = session.query(Check_2).filter_by(creator=user.id)
        pic = login_session['picture']
        return render_template('myhome.html', stubs=stubs, statements=statements, pic=pic)
    else:
        abort(403)

# CREATE AND EDIT FUNCTIONS -- UI TEMPLATES
@app.route('/')
@app.route('/checkstub/', methods=['GET','POST'])
def check_stub():
    """ view for creating and editing a stub
        visitors are redirected to fb login
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
                                                'name': "365 day membership",
                                                'quantity': '1',
                                                'base_price_money':{
                                                    'amount': 699,
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
            # complimentary statement
            newCheck = Check(creator=user.id,
                             emp_name=request.form['emp_name'],
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
                             state_selection=request.form['state_selection'],
                             state_tax=request.form['state_tax'],
                             state_ytd=request.form['state_ytd'],
                             ytd_gross=request.form['ytd_gross'],
                             ytd_deductions=request.form['ytd_deductions'],
                             ytd_net=request.form['ytd_net'],
                             total=request.form['total'],
                             bottom_deductions=request.form['bottom_deductions'],
                             net_pay=request.form['net_pay']
                             )
            user.check_count +=1
            session.add(newCheck)
            session.add(user)
            session.commit()
            return redirect(url_for('my_home'))
    if 'facebook_id' in login_session and 'state' in login_session:
        pic = login_session['picture']
        print pic
        return render_template('loggedinfront.html',pic=pic)
    return render_template('checkstub.html',state=state)

@app.route('/templateone')
def main_template():
    """ Page for creating stubs with template one for
        members
    """
    # user is logged in and granted/denied permission based on
    # membership status. Visitors are denied access
    if check_login_and_csrf() == True:
        user = session.query(User).filter_by(name=login_session['email']).one()
        if user.is_member == True:
            return render_template('templateone.html')
        else:
            abort(403)
    else:
        abort(403)

@app.route('/templatethree', methods=['GET','POST'])
def full_page_template():
    """user create a template three statement"""
    if request.method == 'POST':
        if request.form['_csrf_token'] != login_session['state']:
            abort(403)
            
        user = session.query(User).filter_by(name=login_session['email']).one()
        new_statement = Check_2(creator=user.id,
                                company_name=request.form['company_name'],
                                company_address=request.form['company_address'],
                                company_city=request.form['company_city'],
                                pay_begin=request.form['pay_begin'],
                                pay_end=request.form['pay_end'],
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
                                ov_hours=request.form['ov_hours'],
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
                                comments=request.form['comments'])
        session.add(new_statement)
        session.commit()
        return redirect(url_for('my_home'))
    
    if check_login_and_csrf() == True:
        state = login_session['state']
        user = session.query(User).filter_by(name=login_session['email']).one()
        if user.is_member == True:
            return render_template('templatethree.html',state=state)
        else:
            return "Get full access now to access this template!"
    else:
        abort(403)
        
@app.route('/fullpage/edit/<int:check_id>', methods=['GET','POST'])
def full_page_edit(check_id):
    """ user edit for fullpage template """
    try:
        check = session.query(Check_2).filter_by(id=check_id).one()
    except:
        abort(404)
        
    if request.method=='POST':
        if request.form['_csrf_token'] != login_session['state']:
            abort(403)
            
        check.company_name=request.form['company_name'],
        check.company_address=request.form['company_address'],
        check.company_city=request.form['company_city'],
        check.pay_begin=request.form['pay_begin'],
        check.pay_end=request.form['pay_end'],
        check.pay_date=request.form['pay_date'],
        check.status=request.form['status'],
        check.exemptions=request.form['exemptions'],
        check.emp_name=request.form['emp_name'],
        check.emp_address=request.form['emp_address'],
        check.emp_city_state_zip=request.form['emp_city_state_zip'],
        check.reg_rate=request.form['reg_rate'],
        check.reg_hours=request.form['reg_hours'],
        check.reg_period=request.form['reg_period'],
        check.reg_ytd=request.form['reg_ytd'],
        check.ov_rate=request.form['ov_rate'],
        check.ov_period=request.form['ov_period'],
        check.ov_ytd=request.form['ov_ytd'],
        check.vac_rate=request.form['vac_rate'],
        check.vac_hours=request.form['vac_hours'],
        check.vac_period=request.form['vac_period'],
        check.vac_ytd=request.form['vac_ytd'],
        check.gross_period=request.form['gross_period'],
        check.gross_ytd=request.form['gross_ytd'],
        check.fed_period=request.form['fed_period'],
        check.fed_ytd=request.form['fed_ytd'],
        check.soc_period=request.form['soc_period'],
        check.soc_ytd=request.form['soc_ytd'],
        check.state_selection=request.form['state_selection'],
        check.state_period=request.form['state_period'],
        check.state_ytd=request.form['state_ytd'],
        check.net_pay=request.form['net_pay'],
        check.comments=request.form['comments']
        session.add(check)
        session.commit()
        return redirect(url_for('my_home'))
    
    # check for permission and csrf/login
    if check_login_and_csrf() == True:
        user = session.query(User).filter_by(name=login_session['email']).one()
        state = login_session['state']
        if user.id != check.creator:
            abort(403)
        else:
            return render_template('editthree.html', check=check, state=state)
    else:
        abort(403)

@app.route('/stub/edit/<int:check_id>', methods=['GET','POST'])
def edit_stub_statement(check_id):
    """ user edit for stub template """
    try:
        check = session.query(Check).filter_by(id=check_id).one()
    except:
        return abort(404)

    if request.method == "POST":
        if request.form['_csrf_token'] != login_session['state']:
            abort(403)
        check.emp_name=request.form['emp_name'],
        check.social=request.form['social'],
        check.rep_period=request.form['rep_period'],
        check.pay_date=request.form['pay_date'],
        check.emp_num=request.form['emp_num'],
        check.rate=request.form['rate'],
        check.hours=request.form['hours'],
        check.current_pay=request.form['current_pay'],
        check.fica_medi=request.form['fica_medi'],
        check.fica_social=request.form['fica_social'],
        check.fica_medi_ytd=request.form['fica_medi_ytd'],
        check.fica_social_ytd=request.form['fica_social_ytd'],
        check.fed_tax=request.form['fed_tax'],
        check.fed_ytd=request.form['fed_ytd'],
        check.state_selection=request.form['state_selection'],
        check.state_tax=request.form['state_tax'],
        check.state_ytd=request.form['state_ytd'],
        check.ytd_gross=request.form['ytd_gross'],
        check.ytd_deductions=request.form['ytd_deductions'],
        check.ytd_net=request.form['ytd_net'],
        check.total=request.form['total'],
        check.bottom_deductions=request.form['bottom_deductions'],
        check.net_pay=request.form['net_pay']
        session.add(check)
        session.commit()
        return redirect(url_for('my_home'))
    
    # check if user is logged in and creator of check
    # visitors are denied access
    if check_login_and_csrf() == True:
        user = session.query(User).filter_by(name=login_session['email']).one()
        state = login_session['state']
        if check.creator != user.id:
            return abort(403)
        else:
            return render_template('editstub.html', check=check, state=state)
    else:
        return abort(403)

@app.route('/delete/fullpage/<int:check_id>', methods=['GET','POST'])
def delete_full_page_statement(check_id):
    try:
        check = session.query(Check_2).filter_by(id=check_id).one()
    except:
        return abort(404)
    
    if request.method == "POST":
        if request.form['_csrf_token'] != login_session['state']:
            return abort(403)
        
        session.delete(check)
        session.commit()
        return redirect(url_for('my_home'))

    if check_login_and_csrf() == True:
        # Check that logged in user is check owner, if not 403
        # visitors also get a 403
        user = session.query(User).filter_by(name=login_session['email']).one()
        state = login_session['state']
        if user.id != check.creator:
            abort(403)
        else:
            flash('DELETE? No going back')
            return render_template('fullpagedelete.html',check=check, state=state)
    else:
        return abort(403)

@app.route('/delete/stub/<int:check_id>/', methods=['GET','POST'])
def delete_stub_statement(check_id):
    try:
        check = session.query(Check).filter_by(id=check_id).one()
        user = session.query(User).filter_by(name=login_session['email']).one()
    except:
        return abort(403)

    if request.method == "POST":
        if request.form['_csrf_token'] != login_session['state'] or user.id != check.creator:
            return abort(403)
        
        session.delete(check)
        session.commit()
        return redirect(url_for('my_home'))

    if check_login_and_csrf() == True:
        # Check that logged in user is check owner, if not 403
        # visitors also get a 403
        state = login_session['state']
        if user.id != check.creator:
            abort(403)
        else:
            flash('DELETE? No going back')
            return render_template('stubdelete.html',check=check, state=state)
    else:
        return abort(403)

# PRINT OUTS -- SAVED STATEMENTS FOR PRINTING
@app.route('/fullpage/print/<int:check_id>')
def full_page_print(check_id):
    """ full page print out """
   
    if check_login_and_csrf() == True:
        try:
            check = session.query(Check_2).filter_by(id=check_id).one()
        except:
            return abort(404)
        
        user = session.query(User).filter_by(name=login_session['email']).one()
        if user.id != check.creator:
            abort(403)
        else:
            flash("Please use Chrome and make sure background graphics is checked under print options")
            return render_template('fullpage.html', check=check)
    else:
        return abort(403)

@app.route('/stub/id=<int:check_id>/')
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
        flash("Please use Chrome and make sure background graphics is checked under print options")
        return render_template('checkstub_done.html',check=check)

@app.route('/thankyou/')
def thank_you():

    # once site is on aws get transaction id, checkout id and reference id
    # from this url and compare to originals for verification
    # after checkout square will appened the results to the url
    # once user completes checkout change is_member to true and add the date
    # signup_date

    # transaction_id = request.args.get('')
    # checkout_id = request.args.get('')
    # reference_id = request.args.get('')

    return render_template('thankyou.html')

# UTILITY FUNCTIONS FOR TESTING
@app.route('/checks')
def all_check_2():
    checks = session.query(Check_2).all()
    for i in checks:
        print i.id
    return 'checks printed'

@app.route('/users')
def print_users():
    users = session.query(User).all()
    for i in users:
        print i.name
        print i.f_id
    return 'users printed'

@app.route('/signupdate/')
def change_signup_date():
    user = session.query(User).filter_by(f_id=login_session['facebook_id']).one()
    user.signup_date = datetime.today()
    session.add(user)
    session.commit()
    print user.signup_date
    return "date printed"
    print user.signup_date
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
