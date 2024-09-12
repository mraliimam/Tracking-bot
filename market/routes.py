from flask import render_template, request, flash, redirect, url_for, send_file
import os
from market import app
from market.models import *
from market.forms import *
from flask_login import logout_user, current_user, login_required
from flask_login import login_user
from functools import wraps
from market.static.scrapper import *
import json

def auth(form):
    user = User.query.filter_by(username=form.username.data).first()
    if user and user.check_password_correction(attempted_password=form.password.data):
        login_user(user)
        return 'Pass'
    else:
        return 'Fail'


def roles_required(*roles):
    def wrapper(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if current_user.role not in roles:
                flash("You are not authorized to access this page.", category="danger")
                return redirect(url_for("home_page"))
            return f(*args, **kwargs)
        return wrapped
    return wrapper


@app.route('/signup', methods=['GET'])
def signup_page():
    if request.method == 'GET':
        if User.query.filter_by(username='admin').first():
            return 'User already Exists.'
        else:
            user = User(username='admin', password='admin123@', role='admin')
            db.session.add(user)
            db.session.commit()
            return 'Pass'

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    form = LoginForm()

    if request.method == 'GET':
        return render_template('login.html', form=form)

    if request.method == 'POST':
        if auth(form) == 'Pass':
            return redirect(request.args.get('next') or url_for('home_page'))
        else:
            flash('Wrong Username or Password', category='danger')
            return redirect(url_for('login_page'))


@app.route('/logout')
@login_required
def logout_page():
    logout_user()
    flash('User is logout Successfuly!!', category='info')
    return redirect(url_for('login_page'))


@app.route('/download-db', methods=['GET'])
@login_required
def download_db():
    db_path = os.path.join(app.root_path, 'scrapper.db')
    if os.path.exists(db_path):
        return send_file(db_path, as_attachment=True)
    else:
        flash('Database file not found.', category='danger')
        return redirect(url_for('home_page'))


@app.route('/', methods=['GET', 'POST'])
@app.route('/home', methods=['GET', 'POST'])
@login_required
def home_page():
    from datetime import datetime
    import pytz
    new_york_date = datetime.now(pytz.timezone('America/New_York')).date()
    import datetime

    if request.method == 'GET':
        print(new_york_date)
        items = ScrapeData.query.all()
        url_of_businesses = set(result.url for result in items)
        dates = sorted(set(result.date for result in items))
        review_count_dict = {business: [''] * len(dates) for business in url_of_businesses}

        for item in items:
            urls = item.url
            date_index = dates.index(item.date)
            review_count_dict[urls][date_index] = item.reviews_count

        cols = ScrapeData.__table__.columns.keys()
        businesses_reviews_dates = {
            (ScrapeData.query.filter_by(url=url).first().business_name, ScrapeData.query.filter_by(url=url).first().url, ScrapeData.query.filter_by(url=url).first().nick_name, ScrapeData.query.filter_by(url=url).first().category): zip(review_count_dict[url], dates) for url in url_of_businesses
        }

        return render_template('home.html', items=items, dates=dates, cols=cols, reviewList=review_count_dict, businesses_reviews_dates=businesses_reviews_dates)
    if request.method == 'POST':
        category = request.form['category']
        print(category)
        action_type = request.form['actionType']
        changes = json.loads(request.form['changes']) if action_type in ('editDates', 'editReviews', 'editNickName') else None

        if action_type == 'getBusiness':
            url = request.form['business']

            if ScrapeData.query.filter_by(url=url).first():
                business_name, reviews_count = scrapperFunction(url)
                data_exist = ScrapeData.query.filter_by(date=new_york_date, url=url).first()
                if data_exist:
                    data_exist.reviews_count = reviews_count
                    db.session.add(data_exist)
                    db.session.commit()
                else:
                    data = ScrapeData(url=url, business_name=business_name, reviews_count=reviews_count, category = category)
                    db.session.add(data)
                    try:
                        db.session.commit()
                    except Exception as e:
                        db.session.rollback()
                        flash(f'Exception occurs: {e}!!', category='danger')
            else:
                flash(f'URL NO FOUND!!', category='danger')
            return redirect(url_for('home_page'))
        elif action_type == 'delBusiness':
            url = request.form['business']
            bs = ScrapeData.query.filter_by(url=url).all()
            for b in bs:
                db.session.delete(b)
            try:
                db.session.commit()
                flash(f'Business Deleted Successfully!', category='success')
            except Exception as e:
                db.session.rollback()
                flash(f'Error Occurred while deleting Business', category='success')
            return redirect(url_for('home_page'))
        elif action_type == 'delDate':
            date = request.form['date']
            bs = ScrapeData.query.filter_by(date=date).all()
            for bus in bs:
                db.session.delete(bus)
            try:
                db.session.commit()
                flash(f'Date Deleted Successfully!', category='success')
            except Exception as e:
                db.session.rollback()
                flash(f'Error Occurred while deleting Business', category='success')
            return redirect(url_for('home_page'))
        elif action_type == 'editDates':
            for original_date, new_date in changes.items():
                if original_date != new_date:
                    items = ScrapeData.query.filter_by(date=original_date).all()
                    for item in items:
                        date_format = new_date.split('-')
                        item.date = datetime.date(int(date_format[2]), int(date_format[0]), int(date_format[1]))
                        db.session.add(item)
            db.session.commit()
            return redirect(url_for('home_page'))
        elif action_type == 'editReviews':
            for url, dates_reviews in changes.items():
                for date_item, review in dates_reviews.items():
                    data_exist = ScrapeData.query.filter_by(date=date_item, url=url).first()
                    if data_exist:
                        data_exist.reviews_count = review
                        db.session.add(data_exist)
                    elif review != '':
                        scrape_data = ScrapeData.query.filter_by(url=url).first()
                        if scrape_data:
                            date_format = date_item.split('-')
                            new_scrape = ScrapeData(url=scrape_data.url, business_name=scrape_data.business_name, date=datetime.date(int(date_format[0]), int(date_format[1]), int(date_format[2])), reviews_count=review, category = category)
                            db.session.add(new_scrape)
            db.session.commit()
            return redirect(url_for('home_page'))
        elif action_type == 'editNickName':
            for url, nick_name in changes.items():
                for data in ScrapeData.query.filter_by(url=url):
                    data.nick_name = nick_name if nick_name else ''
                    db.session.add(data)
            db.session.commit()
            return redirect(url_for('home_page'))
        else:
            flash('Invalid action type', category='danger')
            return redirect(url_for('home_page'))


@app.route('/data')
@login_required
def data_page():
    business_name = request.args.get('name')
    items = ScrapeData.query.filter_by(business_name=business_name)
    return render_template('data.html', items=items, business_name=business_name)


@app.route('/form', methods=['GET', 'POST'])
@login_required
def form_page():
    from datetime import datetime
    import pytz
    new_york_date = datetime.now(pytz.timezone('America/New_York')).date()
    print(new_york_date)

    form = BusinessForm()

    if request.method == 'GET':
        return render_template('form.html', form=form)

    if request.method == 'POST':
        form.BusinessName.data, form.ReviewsCount.data = scrapperFunction(form.url.data)

        if None in (form.BusinessName.data, form.ReviewsCount.data):
            if form.BusinessName.data:
                form.ReviewsCount.data = 0
            else:
                flash('Data cannot be scrapped!', category='danger')
                return redirect(url_for('form_page'))

        data_exist = ScrapeData.query.filter_by(date=new_york_date, url=form.url.data).first()
        if data_exist:
            data_exist.reviews_count = form.ReviewsCount.data
            db.session.add(data_exist)
            db.session.commit()
            return redirect(url_for('form_page'))
        else:
            # data = ScrapeData(**form_to_dict(form))
            data = ScrapeData(
                business_name = form.BusinessName.data,
                url = form.url.data,
                reviews_count = form.ReviewsCount.data,
                category = form.category.data
            )
            db.session.add(data)
            try:
                db.session.commit()
                flash('Data is added Successfully!!', category='success')
                return redirect(url_for('home_page'))
            except Exception as e:
                db.session.rollback()
                flash(f'Exception occurs: {e}!!', category='danger')
                return redirect(url_for('form_page'))


@app.route('/getAllReviews')
def get_reviews():
    from datetime import datetime
    import pytz
    new_york_date = datetime.now(pytz.timezone('America/New_York')).date()

    items = ScrapeData.query.all()
    url_of_businesses = set(result.url for result in items)

    for url in url_of_businesses:
        business_name, reviews_count = scrapperFunction(url)
        if None in (business_name, reviews_count):
            if business_name:
                reviews_count = 0
            else:
                continue
        data_exist = ScrapeData.query.filter_by(date=new_york_date, url=url).first()
        if data_exist:
            data_exist.reviews_count = reviews_count
            db.session.add(data_exist)
            db.session.commit()
            return redirect(url_for('form_page'))
        else:
            data = ScrapeData(business_name=business_name, url=url, reviews_count=reviews_count, date=new_york_date)
            db.session.add(data)
    try:
        db.session.commit()
        flash('Data is added Successfully!!', category='success')
        return redirect(url_for('home_page'))
    except Exception as e:
        db.session.rollback()
        flash(f'Exception occurs: {e}!!', category='danger')
        return redirect(url_for('home_page'))