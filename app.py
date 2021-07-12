import imghdr
import os
import datetime
import smtplib
import socket
import sqlite3
from flask import Flask, render_template, session, request, redirect, flash, make_response
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename


app = Flask(__name__)

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
ALLOWED_EXTENSIONS = set(['.jpg', '.png', '.gif', '.jpeg', '.webp'])
app.config['UPLOAD_FOLDER'] = 'static/images/uploads/'
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


@app.route('/')
def index():
    connection = sqlite3.connect('ex.db')
    db = connection.cursor()

    a = session.get("username")
    today = datetime.date.today()
    d1 = today.strftime("%d %B %Y")
    yesterday = today - datetime.timedelta(days=1)
    tomorrow = today + datetime.timedelta(days=1)
    d2 = tomorrow.strftime("%d %B %Y")

    db.execute("DELETE FROM event_details WHERE s_date <= (?)", (yesterday,))
    connection.commit()

    db.execute("DELETE FROM ticket WHERE s_date <= (?) ", (yesterday,))
    connection.commit()

    eventnames = db.execute("SELECT event_name FROM event_details").fetchall()
    activeusers = db.execute(" SELECT participating_event FROM users WHERE user_role_id = 4").fetchall()
    noevent = []
    for item in activeusers:
        if item not in eventnames:
            noevent.append(item)
    for event in noevent:
        db.execute("DELETE FROM users WHERE participating_event = (?)", (event))
        connection.commit()

    db.execute("SELECT * FROM event_details WHERE event_type = 'public' OR event_type = 'business'")
    events = db.fetchall()
#changes
    try:
        main_event1 = db.execute("SELECT * FROM event_details WHERE  ticket = 'Book Ticket' AND s_date != (?) AND event_type != 'private'", (today,)).fetchall()[-1]

    except IndexError as error:
        main_event1 = ['EventOn', 'Demo of event', 'public', 'This is an example of event', '2050-10-10', '2050-10-10', '12:10', '01:00', 'xyz', 100, 'Book Ticket', 'yes', 'Admin', 6, '07.jpg']

        print('index error')

    event_name1 = main_event1[1]

    start_name1 = event_name1.split(' ', 1)[0]
    mid = event_name1.split(start_name1, 1)[1]
    mid_name1 = mid.rsplit(' ', 1)[0]
    last_name1 = event_name1.rsplit(' ', 1)[1]

    format_str = '%Y-%m-%d'
    main_event1_sdate = ((datetime.datetime.strptime(main_event1[4], format_str)).date()).strftime("%d %B %Y")
    main_event1_edate = ((datetime.datetime.strptime(main_event1[5], format_str)).date()).strftime("%d %B %Y")

    todays_event = db.execute("SELECT * FROM event_details WHERE s_date = (?)", (today,)).fetchall()
    tom_event = db.execute("SELECT * FROM event_details WHERE s_date = (?)", (tomorrow,)).fetchall()
    if a is not None:
        return render_template("index.html", today=d1, tomorrow=d2, events=events, todays_event=todays_event,
                               tom_event=tom_event, username=a, start_name1=start_name1, mid_name1=mid_name1, last_name1=last_name1, main_event1=main_event1,  main_event1_sdate=main_event1_sdate,  main_event1_edate=main_event1_edate)
    return render_template("index.html", today=d1, tomorrow=d2, events=events, todays_event=todays_event, tom_event=tom_event, start_name1=start_name1, mid_name1=mid_name1, last_name1=last_name1, main_event1=main_event1,   main_event1_sdate=main_event1_sdate,  main_event1_edate=main_event1_edate)


@app.route('/search', methods=["GET", "POST"])
def search():
    if request.method == "POST":
        connection = sqlite3.connect("ex.db")
        db = connection.cursor()
        today = datetime.date.today()
        d1 = today.strftime("%d %B %Y")
        tomorrow = today + datetime.timedelta(days=1)
        d2 = tomorrow.strftime("%d %B %Y")
        query = request.form.get("query")
#changes
        try:
            main_event1 = db.execute(
                "SELECT * FROM event_details WHERE  ticket = 'Book Ticket' AND s_date != (?) AND event_type != 'private'",
                (today,)).fetchall()[-1]

        except IndexError as error:
            main_event1 = ['Yashwant Naik', 'Demo of event1', 'public', 'This is an example of event', '2050-10-10',
                           '2050-10-10', '12:10', '01:00', 'xyz', 100, 'Book Ticket', 'yes', 'Admin', 6, '07.jpg']

            print('index error')

        event_name1 = main_event1[1]


        start_name1 = event_name1.split(' ', 1)[0]
        mid = event_name1.split(start_name1, 1)[1]
        mid_name1 = mid.rsplit(' ', 1)[0]
        last_name1 = event_name1.rsplit(' ', 1)[1]


        format_str = '%Y-%m-%d'
        main_event1_sdate = ((datetime.datetime.strptime(main_event1[4], format_str)).date()).strftime("%d %B %Y")
        main_event1_edate = ((datetime.datetime.strptime(main_event1[5], format_str)).date()).strftime("%d %B %Y")
        todays_event = db.execute("SELECT * FROM event_details WHERE s_date = (?)", (today,)).fetchall()
        tom_event = db.execute("SELECT * FROM event_details WHERE s_date = (?)", (tomorrow,)).fetchall()
        events = db.execute("SELECT * FROM event_details WHERE event_name LIKE '%{}%' COLLATE NOCASE AND event_type != 'private'".format(query))
        return render_template("index.html", events=events, today=d1, tomorrow=d2, todays_event=todays_event, tom_event=tom_event, start_name1=start_name1, mid_name1=mid_name1, last_name1=last_name1, main_event1=main_event1, main_event1_sdate=main_event1_sdate,  main_event1_edate=main_event1_edate)
    return redirect("/")


@app.route("/subscription/<event>", methods=["GET", "POST"])
def subscribe(event):
    connection = sqlite3.connect("ex.db")
    db = connection.cursor()
#changes
    try:
        url = request.base_url
        format_str = '%Y-%m-%d'
        event_detail = db.execute("SELECT * FROM event_details WHERE event_name = (?)", (event,)).fetchone()
        ticket_price = db.execute("SELECT * FROM ticket WHERE event_name = (?)", (event,)).fetchone()
        username = event_detail[0]
        event_name = event_detail[1]
        disc = event_detail[3]
        s_date = ((datetime.datetime.strptime(event_detail[4], format_str)).date()).strftime("%d %B %Y")
        e_date = ((datetime.datetime.strptime(event_detail[5], format_str)).date()).strftime("%d %B %Y")
        s_time = event_detail[6]
        e_time = event_detail[7]
        venue = event_detail[8]
        image = event_detail[14]
        user = db.execute("SELECT * FROM users WHERE user_name = (?)", (username,)).fetchone()
        email = user[3]
        mobile = user[4]
        org_name = username
        org_email = email
        org_mobile = mobile
        organizor = db.execute("SELECT org_name FROM event_details WHERE event_name = ?", (event_name,)).fetchone()
        if organizor is not None:
            org_details = db.execute("SELECT * FROM users WHERE user_name = ?", (organizor[0],)).fetchone()
            if org_details is not None:
                org_name = organizor[0]
                org_email = org_details[3]
                org_mobile = org_details[4]
        if request.method == "POST":
            try:
                connection = sqlite3.connect("ex.db")
                db = connection.cursor()
                user_role_id = 4
                name = request.form.get("name")
                p_email = request.form.get("email")
                mobile = request.form.get("mobile")
                db.execute("INSERT INTO users (user_role_id, name, participant_email, mbl_no, participating_event) VALUES (?, ?, ?, ?, ?)", (user_role_id, name, p_email, mobile, event_name,))
                connection.commit()
                connection.close()
                Mail = """ Hey {}\nYou have been successfully subscribed to {} event \nSchedule: From {} to {}, at {}-{}\nMore information will be provided by the organiser \nTHANK YOU\n(Note: Enquiry payment procedure when organiser came to contact)""".format(name, event_name, s_date, e_date, s_time, e_time)
                OMail = """ Hey {}\nParticipant {}  is subscribed to "{}" event\nPlease provide more information to your client\nClient mail: {}\nClient phone: {} """.format(username, name, event_name, p_email, mobile)
                server = smtplib.SMTP("smtp.gmail.com", 587)
                server.starttls()
                server.login("eventon43@gmail.com", "DeadPool305@")
                server.sendmail("eventon43@gmail.com", p_email, Mail)
                server.quit()
                server = smtplib.SMTP("smtp.gmail.com", 587)
                server.starttls()
                server.login("eventon43@gmail.com", "DeadPool305@")
                server.sendmail("eventon43@gmail.com", org_email, OMail)
                server.quit()
        #changes
                flash('Successfully registered.')
                return redirect(url)
            except socket.gaierror as e:
                flash('Booking Failed: Check your internet connection..')
                print('socket error: ', e.args[0])
        return render_template("index_events.html", username=username, event_name=event_name, disc=disc, s_date=s_date, e_date=e_date, s_time=s_time, e_time=e_time, venue=venue, email=email, mobile=mobile, ticket_price=ticket_price, org_name=org_name, org_mobile=org_mobile, org_email=org_email, image=image)
    except TypeError as error:
        print('image here')
        return redirect("/not_found")


@app.route("/not_found")
def nf():
    return render_template("notfound.html")


@app.route("/login", methods=["GET", "POST"])
def log():
    if request.method == "POST":
        connection = sqlite3.connect('ex.db', timeout=10)

        db = connection.cursor()
        password = request.form.get("password")
        username = request.form.get("username")

        if not username or not password:
            flash('Please enter username and password')
            return redirect("/login")
        user = db.execute("SELECT * FROM users WHERE user_name = (?)", (username,)).fetchone()
        user_role = db.execute("SELECT user_role_id FROM users WHERE user_name=(?)", (username,)).fetchone()[0]
        connection.commit()

        if user is not None and check_password_hash(user[7], password):
            session["user_id"] = user[0]
            session["username"] = user[2]
            session["email"] = user[3]
            connection.commit()
            connection.close()
            if user_role == 2:
                return redirect("/profile")
            elif user_role == 3:
                return redirect("/org_profile")
            flash('Invalid username or password')
            return redirect("/login")
        flash('Invalid username or password')
        return redirect("/login")
    else:
        return render_template("login.html")


@app.route("/reg2", methods=["GET", "POST"])
def reg():
    if request.method == "POST":
        # connects the db to the signup function
        connection = sqlite3.connect('ex.db', timeout=50)
        db = connection.cursor()
        user_role_id = 2
        username = request.form.get("username")
        email = request.form.get("email")
        mobile = request.form.get("mobile")
        city = request.form.get("city")
        pin = request.form.get("pin")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        connection.commit()
        userCheck = db.execute("SELECT * FROM users WHERE user_name = :username",
                               {"username": request.form.get("username")}).fetchone()

        mailCheck = db.execute("SELECT * FROM users WHERE user_name = :email",
                               {"email": request.form.get("email")}).fetchone()

        if not confirmation or not password or not pin or not city or not mobile or not email or not username:
            flash("Error: Empty")
            return redirect("/reg3")
        if password != confirmation:
            flash('Error: Passwords are not matching')
            return redirect("/reg2")
        if userCheck or mailCheck is not None:
            flash("Failed: Username or Email is already exist")
            return redirect("/reg2")
        hashed = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)
        db.execute("INSERT INTO users (user_role_id, user_name, email, mbl_no, city, pin, password) VALUES (?, ?, ?, ?, ?, ?, ?)", (user_role_id, username, email, mobile, city, pin, hashed,))
        user = db.execute("SELECT * FROM users WHERE user_name = (?)", (username,)).fetchone()
        session["user_id"] = user[0]
        session["username"] = user[2]
        session["email"] = user[3]
        connection.commit()
        connection.close()
        return redirect("/profile")
    else:
        return render_template("RegHost.html")


@app.route("/reg3", methods=["GET", "POST"])
def regor():
    if request.method == "POST":
        connection = sqlite3.connect('ex.db', timeout=50)
        db = connection.cursor()
        user_role_id = 3
        username = request.form.get("username")
        email = request.form.get("email")
        mobile = request.form.get("mobile")
        city = request.form.get("city")
        pin = request.form.get("pin")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        pri_venue = request.form.get("private_name")
        business_venue = request.form.get("business_name")
        pub_venue = request.form.get("public_name")
        connection.commit()
        userCheck = db.execute("SELECT * FROM users WHERE user_name = :username",
                               {"username": request.form.get("username")}).fetchone()
        mailCheck = db.execute("SELECT * FROM users WHERE user_name = :email",
                               {"email": request.form.get("email")}).fetchone()
        if not pub_venue or not business_venue or not pri_venue or not confirmation or not password or not pin or not city or not mobile or not email or not username:
            flash("Error: Empty")
            return redirect("/reg3")
        if password != confirmation:
            flash('Error: Passwords are not matching')
            return redirect("/reg3")

        if userCheck or mailCheck is not None:
            flash("Failed: Username or email is already exist")
            return redirect("/reg3")
        hashed = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)
        db.execute("INSERT INTO users (user_role_id, user_name, email, mbl_no, city, pin, password, private_venue, public_venue, busi_venue) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (user_role_id, username, email, mobile, city, pin, hashed, pri_venue, pub_venue, business_venue,))
        user = db.execute("SELECT * FROM users WHERE user_name = (?)", (username,)).fetchone()
        session["user_id"] = user[0]
        session["username"] = user[2]
        connection.commit()
        session["email"] = user[3]
        connection.close()
        return redirect("/org_profile")
    else:
        return render_template("RegOrg.html")


@app.route("/profile")
def prof():
    connection = sqlite3.connect('ex.db')
    db = connection.cursor()
    a = session.get("user_id")
    if a is not None:
        user_role = db.execute("SELECT user_role_id FROM users WHERE user_id=(?)", (session["user_id"],)).fetchone()[0]
        if user_role == 2:
            events = db.execute("SELECT * FROM event_details WHERE user_name=(?)", (session["username"],)).fetchall()
            # org_events = db.execute("SELECT * FROM event_details WHERE org_name=(?)", (session["username"],)).fetchall()
            username = db.execute("SELECT user_name FROM users WHERE user_id=(?)", (session["user_id"],)).fetchone()[0]
            email = db.execute("SELECT email FROM users WHERE user_id=(?)", (session["user_id"],)).fetchone()[0]
            mbl_no = db.execute("SELECT mbl_no FROM users WHERE user_id=(?)", (session["user_id"],)).fetchone()[0]
            bio = db.execute("SELECT bio FROM users WHERE user_id=(?)", (session["user_id"],)).fetchone()[0]
            # user_role = db.execute("SELECT user_role_id FROM users WHERE user_id=(?)", (session["user_id"],)).fetchone()[0]
            connection.commit()
            connection.close()
            return render_template("profile.html", username=username, email=email, mbl_no=mbl_no, bio=bio,events=events)
        return redirect("/org_profile")
    else:
        return redirect("/login")


@app.route("/org_profile")
def org_prof():
    connection = sqlite3.connect('ex.db')
    db=connection.cursor()
    a = session.get("user_id")
    if a is not None:
        org_events = db.execute("SELECT * FROM event_details WHERE org_name=(?)", (session["username"],)).fetchall()
        username = db.execute("SELECT user_name FROM users WHERE user_id=(?)", (session["user_id"],)).fetchone()[0]
        email = db.execute("SELECT email FROM users WHERE user_id=(?)", (session["user_id"],)).fetchone()[0]
        mbl_no = db.execute("SELECT mbl_no FROM users WHERE user_id=(?)", (session["user_id"],)).fetchone()[0]
        bio = db.execute("SELECT bio FROM users WHERE user_id=(?)", (session["user_id"],)).fetchone()[0]
        connection.commit()
        connection.close()
        return render_template("org_profile.html", username=username, email=email, mbl_no=mbl_no, bio=bio, org_events=org_events)


@app.route("/logout", methods=["GET", "POST"])
def logout():
    session.clear()
    return redirect("/")


@app.route("/reset/<user_n>", methods=["GET", "POST"])
def reset(user_n):
    a = session.get("user_id")
    if a is not None:
        if request.method == "POST":
            connection = sqlite3.connect('ex.db')
            db = connection.cursor()
            password = request.form.get("password")
            reset_pass = request.form.get("re_password")
            confirmation = request.form.get("confirmation")
            url = request.base_url
            # a = session.get("user_id")
            if reset_pass != confirmation:
                flash('Failed: Passwords are not matching')
                return redirect(url)
            # elif a is not None:
            username = db.execute("SELECT user_name FROM users WHERE user_id=(?)", (session["user_id"],)).fetchone()[0]
            user = db.execute("SELECT * FROM users WHERE user_name = (?)", (username,)).fetchone()
            user_role = db.execute("SELECT user_role_id FROM users WHERE user_name=(?)", (username,)).fetchone()[0]
            connection.commit()
            if user is not None and check_password_hash(user[7], password):
                re_hashed = generate_password_hash(reset_pass, method='pbkdf2:sha256', salt_length=16)
                print("password updated")
                db.execute("Update users set password = ? where user_name = ?", (re_hashed, user[2]))
                connection.commit()
                connection.close()
                if user_role == 2:
                    return redirect("/profile")
                elif user_role == 3:
                    return redirect("/org_profile")
                return redirect(url)
            flash('Error: Incorrect password')
            return redirect(url)
        else:
            return render_template("reset.html", username=user_n)
    else:
        return redirect("/login")


@app.route("/edit", methods=["GET", "POST"])
def edit():
    if request.method == "POST":
        connection = sqlite3.connect('ex.db', timeout=100)
        db = connection.cursor()
        session_user = session.get("username")
        session_mail = session.get("email")
        username = request.form.get("username1")
        bio = request.form.get("bio1")
        email = request.form.get("email1")
        mbl_no = request.form.get("mbl_no1")
        user_role = db.execute("SELECT user_role_id FROM users WHERE user_id=(?)", (session["user_id"],)).fetchone()[0]
        edit_username = db.execute("SELECT user_name FROM users WHERE user_id=(?)", (session["user_id"],)).fetchone()[0]
        edit_usermail = db.execute("SELECT email FROM users WHERE user_id=(?)", (session["user_id"],)).fetchone()[0]
        user = db.execute("SELECT * FROM users WHERE user_name = (?)", (edit_username,)).fetchone()
        check_user = db.execute("SELECT * FROM users WHERE user_name = :username", {"username": request.form.get("username1")}).fetchone()
        check_mail = db.execute("SELECT * FROM users WHERE email = :email", {"email": request.form.get("email1")}).fetchone()

        if not username or not email or not mbl_no:
            flash("Failed: Updating empty data ")
            return redirect("/profile")
        if session_user is not None:
            db.execute("UPDATE users SET  bio = ?, mbl_no = ? where user_name = ?", (bio, mbl_no, user[2]))
            connection.commit()
            if check_user or check_mail is not None:
                if user[2] != session_user or user[3] != session_mail:
                    flash("Failed: Username or Email is already exist")
                    return redirect("/profile")
                try:
                    db.execute("UPDATE users SET user_name = ?, bio = ?, email = ?, mbl_no = ? where user_name = ?",
                           (username, bio, email, mbl_no, user[2]))
                    session["username"] = username
                    session["email"] = email
                    connection.commit()
                    db.execute("UPDATE event_details SET user_name = ? where user_name = ?", (username, user[2]))
                    connection.commit()
                    connection.close()
                    if user_role == 2:
                        return redirect("/profile")
                    return redirect('/org_profile')
                except sqlite3.IntegrityError as e:
                    flash("Failed: Username or Email is already exist")
                    print('sqlite error: ', e.args[0])
            return redirect("/profile")
        return redirect("/login")
    else:
        return redirect("/profile")


@app.route("/profile/add_event/<usr>", methods=["GET", "POST"])
def ad_event(usr):
    session_id = session.get("user_id")
    connection = sqlite3.connect("ex.db")
    db = connection.cursor()
    if session_id is not None:
        user_role = db.execute("SELECT user_role_id FROM users WHERE user_id=(?)", (session["user_id"],)).fetchone()[0]
        if request.method == "POST":
            connection = sqlite3.connect("ex.db")
            db = connection.cursor()
            event_name = request.form.get("eventname")
            event_type = request.form.get("event_type")
            disc = request.form.get("discription")
            s_date = request.form.get("s-date")
            e_date = request.form.get("e-date")
            s_time = request.form.get("s_time")
            e_time = request.form.get("e_time")
            venue = request.form.get("venue")
            people = request.form.get("people")
            organize = request.form.get("orga")
            ticket = request.form.get("ticket")
            ticket_price = request.form.get("ticketprice")
            uploaded_file = request.files.get("image")
            if uploaded_file is not None:
                filename = secure_filename(uploaded_file.filename)
                if filename != '':
                    file_ext = os.path.splitext(filename)[1]
                    if file_ext == '.jpeg' or '.jpg' or '.png':
                        file_ext = '.jpg'
                        if file_ext not in ALLOWED_EXTENSIONS or \
                                file_ext != validate_image(uploaded_file.stream):
                            flash('Invalid format of image')
                            return redirect("/profile/add_event/{}".format(usr))
                        uploaded_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            username = db.execute("SELECT user_name FROM users WHERE user_id=(?)", (session["user_id"],)).fetchone()[0]

            db.execute("INSERT INTO event_details (user_name, event_name, event_type, disc, s_date, e_date, s_time,e_time ,venue, no_of_ppl, organize, ticket, image) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (username, event_name, event_type, disc, s_date, e_date, s_time, e_time, venue, people, organize, ticket, filename,))
            connection.commit()
            db.execute("INSERT INTO ticket (event_name, ticket_price, no_of_ticket, s_date) VALUES (?, ?, ?, ?)", (event_name, ticket_price, people, s_date,))
            connection.commit()
            connection.close()
            return redirect("/profile")
        elif user_role == 2:
            return render_template("eventform.html", username=usr)
        flash("Suggestion: login as a Host")
        return redirect("/login")
    return redirect("/")

@app.route("/profile/add_event/")
def ad_error():
    flash("Suggestion: login as a Host")
    return redirect("/login")


@app.route("/profile/participant/<ename>")
def part(ename):
    session_id = session.get("user_id")
    connection = sqlite3.connect("ex.db")
    db = connection.cursor()
    if session_id is not None:
        p_user = db.execute("SELECT * FROM users WHERE participating_event=(?)", (ename,)).fetchall()
        return render_template("parcipant.html", users=p_user)
    return redirect("/login")


@app.route("/contact_us", methods=["POST", "GET"])
def contact():
    url = request.base_url
    email = request.form.get("email")
    subject = request.form.get("subject")
    message = request.form.get("message")
    Mail = """{} \nmessage:{} \nfrom:{}""".format(subject, message, email)

    if not email or not subject or not message:
        return redirect(url)
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login("eventon43@gmail.com", "DeadPool305@")
        server.sendmail(email, "eventon43@gmail.com", Mail)
        server.quit()
        return redirect("/")
    except socket.gaierror as e:
        print("connection failed")
        flash('Try again: Check your internet connection..')
        print('socket error: ', e.args[0])

    return redirect("/")


@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        name = request.form.get("name")
        password = request.form.get("password")
        if name == 'Yashwant' and password == '12345':
            session["name"] = 'Yashwant'
            return redirect("/admin/dashboard")
        return redirect("/admin")
    else:
        return render_template("admin_signin.html")


@app.route("/admin/update/<event_name>", methods=["GET", "POST"])
def update(event_name):
    admin_u = session.get("name")
    if admin_u is not None:
        connection = sqlite3.connect("ex.db")
        db = connection.cursor()
        events = db.execute(
            "SELECT * FROM event_details WHERE event_name = ?", (event_name,)).fetchone()
        ticket_price = db.execute("SELECT * FROM ticket WHERE event_name = (?)", (event_name,)).fetchone()
        organized = db.execute("SELECT org_name FROM event_details WHERE event_name = (?)", (event_name,)).fetchone()
        event = request.form.get("event")
        disc = request.form.get("disc")
        s_date = request.form.get("s_date")
        e_date = request.form.get("e_date")
        s_time = request.form.get("s_time")
        e_time = request.form.get("e_time")
        venue = request.form.get("venue")
        if request.method == "POST":
            connection = sqlite3.connect("ex.db")
            db = connection.cursor()

            ticket_price = request.form.get("ticket_price")
            organizor = request.form.get("organizor")
            db.execute(
                "UPDATE event_details SET event_name = ?, disc= ?, s_date = ?, e_date = ?, s_time = ?, e_time = ?, venue = ?",
                (event, disc, s_date, e_date, s_time, e_time, venue,))
            connection.commit()
            db.execute("UPDATE ticket SET ticket_price = ? where event_name = ?", (ticket_price, event_name,))
            connection.commit()
            # if eventCheck is None:
            db.execute("UPDATE event_details SET org_name = ? where event_name = ?", (organizor, event_name,))
            connection.commit()
            connection.close()
                # return redirect("/admin/dashboard")
            return redirect("/admin/dashboard")
        return render_template("update_event.html", events=events, ticket_price=ticket_price, organized=organized)
    return redirect("/admin")


@app.route("/admin/dashboard")
def dash():
    admin_u = session.get("name")
    if admin_u is not None:
        connection = sqlite3.connect("ex.db")
        db = connection.cursor()
        events = db.execute(
            "SELECT * FROM event_details WHERE ticket = 'Book Ticket'  ORDER BY track DESC")
        return render_template("admin.html", events=events)
    return redirect("/admin")


@app.route("/admin/basic_table")
def table():
    admin_u = session.get("name")
    if admin_u is not None:
        connection = sqlite3.connect("ex.db")
        db = connection.cursor()
        users = db.execute("SELECT * FROM users WHERE user_role_id = '2' OR user_role_id = '3'").fetchall()
        tickets = db.execute("SELECT * FROM ticket").fetchall()
        events = db.execute("SELECT * FROM event_details").fetchall()
        return render_template("basic-table.html", users=users, tickets=tickets, events=events)
    return redirect("/admin")


@app.route("/admin/basic_element", methods=["GET", "POST"])
def element():
    admin_u = session.get("name")
    if admin_u is not None:
        if request.method == "POST":
            connection = sqlite3.connect("ex.db")
            db = connection.cursor()
            event_name = request.form.get("eventname")
            event_type = request.form.get("event_type")
            disc = request.form.get("discription")
            s_date = request.form.get("s-date")
            e_date = request.form.get("e-date")
            s_time = request.form.get("s_time")
            e_time = request.form.get("e_time")
            venue = request.form.get("venue")
            people = request.form.get("people")
            organize = request.form.get("orga")
            ticket = request.form.get("ticket")
            ticket_price = 0
            username = 'Yashwant'
            uploaded_file = request.files.get("image")
            if uploaded_file:
                filename = secure_filename(uploaded_file.filename)
                if filename != '':
                    file_ext = os.path.splitext(filename)[1]
                    if file_ext == '.jpeg' or '.jpg' or '.png':
                        file_ext = '.jpg'
                        if file_ext not in ALLOWED_EXTENSIONS or \
                                file_ext != validate_image(uploaded_file.stream):
                            return redirect("/admin/basic_element")
                        uploaded_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            db.execute(
                "INSERT INTO event_details (user_name, event_name, event_type, disc, s_date, e_date, s_time,e_time ,venue, no_of_ppl, organize, ticket, image) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (username, event_name, event_type, disc, s_date, e_date, s_time, e_time, venue, people, organize,
                 ticket, filename,))
            connection.commit()
            db.execute("INSERT INTO ticket (event_name, ticket_price, no_of_ticket) VALUES (?, ?, ?)",
                       (event_name, ticket_price, people,))
            connection.commit()
            connection.close()
            return redirect("/admin/dashboard")
        return render_template("basic_elements.html")
    return redirect("/admin")


@app.route("/admin/documentation")
def doc():
    return render_template("documentation.html")


@app.route("/admin/userlogin")
def userlog():
    admin_u = session.get("name")
    if admin_u is not None:
        return redirect("/login")
    return redirect("/admin")


@app.route("/admin/register")
def register():
    return render_template("register.html")


@app.route("/video", methods=["GET","POST"])
def video():
    youtube_link = request.form.get("youtube")


@app.route("/admin/close/<ename>", methods=["GET", "POST"])
def adclose(ename):
    admin_u = session.get("name")
    connection = sqlite3.connect("ex.db")
    db = connection.cursor()
    if admin_u is not None:
        db.execute("DELETE FROM event_details WHERE event_name=(?)", (ename,))
        connection.commit()
        return redirect("/admin/dashboard")
    return redirect("/admin")


@app.route("/close/confirm/<ename>", methods=["GET", "POST"])
def closconf(ename):
    session_id = session.get("user_id")
    connection = sqlite3.connect("ex.db")
    db = connection.cursor()
    if session_id is not None:
        db.execute("DELETE FROM event_details WHERE event_name=(?)", (ename,))
        connection.commit()
        return redirect("/profile")
    return redirect("/login")


def validate_image(stream):
    header = stream.read(512)
    stream.seek(0)
    format = imghdr.what(None, header)
    if not format:
        return None
    return '.' + (format if format != 'jpeg' else 'jpg')


if __name__ == '__main__':
    app.run(debug=True)
