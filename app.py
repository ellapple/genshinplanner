from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
import requests
from bs4 import BeautifulSoup
from werkzeug.security import check_password_hash, generate_password_hash
import calendar as calmod
from datetime import date, datetime, timedelta

app = Flask(__name__)

app.config['SESSION_PERMANENT'] = False
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

db = SQL('sqlite:///app.db')

calmod.setfirstweekday(6)

current_version = db.execute('SELECT version FROM versions WHERE date(phase_1) <= date("now") ORDER BY julianday("now") - julianday(phase_1) LIMIT 1')[0]['version']

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    try:
        if db.execute('SELECT last_login FROM users WHERE id = ?', session['user_id'])[0]['last_login'] != str(date.today()):
            db.execute('UPDATE users SET last_login = ?, bugs = 5 WHERE id = ?', date.today(), session['user_id'])
    except KeyError:
        pass
    except IndexError:
        pass
    return response
@app.route('/')
def index():
    today = datetime.today()
    month = today.strftime("%B")
    year = today.year
    day = today.day
    try:
        user = db.execute('SELECT * FROM users WHERE id = ?', session['user_id'])[0]
    except KeyError:
        pass
    events = db.execute('SELECT * FROM events WHERE ? BETWEEN start AND end', today)
    for event in events:
        tmp = BeautifulSoup(requests.get(event['link']).text, 'html.parser').find('h1', id='firstHeading').text
        if event['type'] == 'wish':
            tmp = tmp[:-14]
        event['name'] = tmp.strip()
        diff = datetime.strptime(event['end'], "%Y-%m-%d") - today
        event['days_left'] = diff.days
        event['hours_left'] = diff.seconds // 3600
    try:
        unfinished = db.execute('SELECT COUNT(*) FROM todo WHERE user_id = ? AND completed = 1', session['user_id'])[0]['COUNT(*)']
    except KeyError:
        pass
    try:
        return render_template('/index.html', active='home', month=month, year=year, day=day, user=user, events=events, unfinished=unfinished)
    except UnboundLocalError:
        return render_template('/index.html', active='home', month=month, year=year, day=day, events=events)

# CALENDAR - CALENDAR - CALENDAR - CALENDAR - CALENDAR - CALENDAR - CALENDAR - CALENDAR - CALENDAR #
@app.route('/calendar')
def calendar():
    # Getting Calendar
    today = date.today()
    year = today.year
    if today.month + 3 > 12:
        year += 1
        month = (today.month + 3) - 12
    else:
        month = today.month + 3

    cal = []
    months_applicable = []
    for i in range(7):
        m = month - i
        y = year
        if m < 1:
            m += 12
            y -= 1
        cal.append(calmod.monthcalendar(y, m))
        months_applicable.append(calmod.month_name[m])
        if i == 6:
            months_applicable.insert(8, calmod.month_name[(m - 1) if (m - 1) >= 1 else 12])
        if i == 0:
            months_applicable.insert(0, calmod.month_name[(month + 1) if (month + 1) <= 12 else 1])

    months_applicable.reverse()
    cal.reverse()
    # Delete past events
    month2 = today.month - 3
    year2 = today.year

    if month2 <= 0:
        month2 += 12
        year2 -= 1

    db.execute('DELETE FROM events WHERE end < ?', datetime(year2, month2, 1))
    # Getting events
    durations = []
    names = []
    links = []
    # FOR LATER, if this stops working at any point its probably because today.month-3 very much does not change year
    events = db.execute('SELECT link, type, start, end FROM events WHERE end BETWEEN ? AND ? OR start BETWEEN ? AND ?', date(year, today.month-3, 1), date(year, month, 1), date(year, today.month-3, 1), date(year, month, 1))
    for event in events:
        durations.append(db.execute("SELECT julianday(?) - julianday(?) AS diff", event['end'], event['start'])[0]['diff'] + 1)
        name = BeautifulSoup(requests.get(event['link']).text, 'html.parser').find('h1', id='firstHeading').text
        if event['type'] == 'wish':
            name = name[:-14]
        names.append(name.strip())
        links.append(event['link'])
    starts = [event["start"] for event in events]
    return render_template('calendar.html', active='calendar', cal=cal, month_names=months_applicable, enames=names, etimes=durations, estarts=starts, month2=month2, elinks=links)

@app.route('/todo', methods=['GET', 'POST'])
def todo():
    try:
        items = db.execute('SELECT * FROM todo WHERE user_id = ?', session['user_id'])
        today = date.today()
        for item in items:
            if item['repeat'] and item['repeat'] != 0 and db.execute('SELECT last_checked FROM todo WHERE id = ?', item['id'])[0]['last_checked'] != date.today():
                if (today - (datetime.strptime(item['created'], '%Y-%m-%d')).date()).days % item['repeat'] == 0:
                    if item['completed'] == 0:
                        db.execute('UPDATE todo SET completed = FALSE WHERE id = ?', item['id'])
        items = db.execute('SELECT * FROM todo WHERE user_id = ?', session['user_id'])
        if request.method == 'POST':
            addName = request.form.get('name')
            addDesc = request.form.get('desc')
            addInterval = request.form.get('interval')
            if not addName and not addDesc:
                delete_id = request.form.get('delete_id')
                if not delete_id:
                    item_id = request.form.get('id')
                    repeat = request.form.get('edit-repeat')
                    desc = request.form.get('edit-desc')
                    if not item_id or not repeat or not desc:
                        print(item_id)
                        print(repeat)
                        print(desc)
                        return render_template('/todo.html', message='One or more edit fields are blank', active='todo', items=items)
                    try:
                        item_id = int(item_id)
                        repeat = int(repeat)
                    except ValueError:
                        return render_template('/todo.html', message='Repeat field must be a non-negative integer', active='todo', items=items)
                    if db.execute('SELECT COUNT(*) FROM todo WHERE id = ?', item_id)[0]['COUNT(*)'] != 1:
                        return render_template('/todo.html', message='Something went wrong', active='todo', items=items)
                    if repeat < 0:
                        return render_template('/todo.html', message='Repeat field must be a non-negative integer', active='todo', items=items)

                    if repeat == 0:
                        repeat = None
                    db.execute('UPDATE todo SET desc = ?, repeat = ? WHERE user_id = ? AND id = ?', desc, repeat, session['user_id'], item_id)
                    items = db.execute('SELECT * FROM todo WHERE user_id = ?', session['user_id'])
                    return render_template('/todo.html', active='todo', items=items, today=today)
                try:
                    delete_id = int(delete_id)
                except ValueError:
                    return render_template('/todo.html', active='todo', items=items, message='Something went wrong', today=today)
                if delete_id < 0:
                    return render_template('/todo.html', active='todo', items=items, message='Something went wrong', today=today)
                if db.execute('SELECT COUNT(*) FROM todo WHERE user_id = ? AND id = ?', session['user_id'], delete_id)[0]['COUNT(*)'] != 1:
                    return render_template('/todo.html', active='todo', message='Something went wrong', items=items, today=today)
                # technically the user_id thing has no use but just to be safe y'know
                db.execute('DELETE FROM todo WHERE id = ? AND user_id = ?', delete_id, session['user_id'])
                items = db.execute('SELECT * FROM todo WHERE user_id = ?', session['user_id'])
                return render_template('/todo.html', active='todo', items=items, today=today)
            try:
                addInterval = int(addInterval)
            except ValueError:
                addInterval = None
            if addInterval < 0:
                return render_template('/todo.html', active='todo', items=items, today=today, message='Interval field must be a non-negative integer')
            db.execute("INSERT INTO todo(user_id, name, desc, repeat) VALUES (?, ?, ?, ?)", session['user_id'], addName, addDesc, addInterval)
            items = db.execute("SELECT * FROM todo WHERE user_id = ?", session['user_id'])
            return render_template('/todo.html', active='todo', items=items, today=today)
    except KeyError:
        today = date.today()
        return render_template('/todo.html', active='todo', today=today, login='no')
    else:
        try:
            return render_template('/todo.html', active='todo', items=items, today=today)
        except UnboundLocalError:
            return render_template('/todo.html', active='todo', today=today, login='no')

@app.route('/api/todo/<int:id>', methods=['DELETE', 'GET'])
def delete_items(id):
    if request.method == 'DELETE':
        try:
            db.execute("DELETE FROM todo WHERE id=?", id)
            return '', 200
        except:
            return {'error': 'ID could not be found'}, 404
    else:
        try:
            if db.execute('SELECT completed FROM todo WHERE id = ?', id)[0]['completed'] == False:
                db.execute('UPDATE todo SET completed = TRUE, last_checked = ? WHERE id = ?', date.today(), id)
                return '', 200
            else:
                db.execute('UPDATE todo SET completed = FALSE, last_checked = "1970-01-01" WHERE id = ?', id)
                return '', 200
        except:
            return {'error': 'ID could not be found'}, 404

@app.route('/calculations', methods=['GET', 'POST'])
def calculations():
    amounts = db.execute('SELECT "Mondstadt + Dragonspine", "Liyue + Chenyu Vale","Inazuma" FROM sources')
    regions = list(amounts[0].keys())
    if request.method == 'POST':
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        if not start_date or not end_date:
            return render_template('/calculations.html', active='calculations', regions=regions, message='Must select start and end date')
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return render_template('/calculations.html', active='calculations', regions=regions, message='Date is in an invalid format')
        if start_date < date.today() or end_date <= start_date:
            return render_template('/calculations.html', active='calculations', regions=regions, message='Invalid date(s)')

        daydiff = (end_date - start_date).days
        months = (end_date.year * 12 + end_date.month) - (start_date.year * 12 + start_date.month)

        total = {}
        # STATIC STATIC STATIC
        total['static sources'] = 60 * daydiff + 60 * months + 40 * (db.execute('SELECT COUNT(*) FROM versions WHERE phase_1 BETWEEN ? AND ?', start_date, end_date)[0]['COUNT(*)']) + 40 * (db.execute('SELECT COUNT(*) FROM versions WHERE phase_2 BETWEEN ? AND ?', start_date, end_date)[0]['COUNT(*)'])
        # EXPLORATION EXPLORATION EXPLORATION
        regionprimos = []
        statueprimos = []
        for region in regions:
            try:
                percentage = float(request.form.get(f'{region.lower()}%')) / 100
            except ValueError:
                return render_template('/calculations.html', regions=regions, message='Exploration % must be a non-negative integer!', active='calculations')
            if percentage < 0 or percentage > 1:
                return render_template('/calculations.html', regions=regions, message='Exploration % must be a non-negative integer between 0 and 100!', active='calculations')
            if not request.form.get(f'btnestimate{region.lower()}'):
                return render_template('/calculations.html', regions=regions, message='Must select an estimation mode!', active='calculations')
            mode = request.form.get(f'btnestimate{region.lower()}')
            regionprimos.append(db.execute(f'SELECT SUM(ROUND("{mode}" * "{region}" * {1 - percentage}, 2)) AS primos FROM sources INNER JOIN primoestimation ON primoestimation.source = sources.source')[0]['primos'])
            if region == 'Mondstadt + Dragonspine' or region == 'Liyue + Chenyu Vale':
                statueprimos.append(10 * ((1 - percentage) * 10))
            elif region == 'Natlan':
                statueprimos.append(100 * ((1 - percentage) * 10))
            else:
                statueprimos.append(60 * ((1 - percentage) * 10))
        # This doesn't account for frostbearing tree because if it did I would have to check if exploration = 100%
        total['exploration'] = sum(regionprimos) + sum(statueprimos)

        # PAID
        welkin = request.form.get('welkinCheck')
        bp = request.form.get('bpCheck')
        if welkin:
            welkinamount = int(daydiff / 30)
            if daydiff % 30 != 0:
                welkinamount += 1
            welkinprimos = welkinamount * 300 + daydiff * 90
        else:
            welkinprimos = 0
        if bp:
            bpamount = int(daydiff / 42)
            bpprimos = bpamount * 1320 + ((daydiff / 42 - bpamount) * 1320)
        else:
            bpprimos = 0
        total['paid'] = welkinprimos + bpprimos

        # ENDGAME CONTENT ENDGAME CONTENT ENDGAME CONTENT
        abyss = request.form.get('spiralabyssfloor')
        theater = request.form.get('theateract')
        onslaught = request.form.get('onslaught')
        if not abyss or not theater or not onslaught:
            return render_template('/calculations.html', regions=regions, message='One or more endgame fields are empty', active='calculations')
        try:
            abyss = int(abyss)
            theater = int(theater)
            onslaught = int(onslaught)
        except ValueError:
            return render_template('/calculations.html', regions=regions, message='One or more endgame fields are invalid', active='calculations')
        if abyss < 0 or theater < 0 or onslaught < 0:
            return render_template('/calculations.html', regions=regions, message='One or more endgame fields are below 0', active='calculations')
        if abyss > 12 or theater > 10 or onslaught > 3:
            return render_template('/calculations.html', regions=regions, message='One or more endgame fields are above the maximum achievable', active='calculations')
        acts = [60, 60, 100, 60, 60, 100, 60, 120, 60, 120]
        abyssprimos = 0
        # I may have slightly overcomplicated this lol
        if abyss > 8:
            if start_date.day >= 16:
                if start_date.month == 12:
                    next_month = 1
                    year2 = start_date.year + 1
                else:
                    next_month = start_date.month + 1
                    year2 = start_date.year
                daydiff2 = daydiff - (date(year2, next_month, 16) - start_date).days
            else:
                daydiff2 = daydiff
            abyssprimos += round(daydiff2 / 30 + 1) * ((abyss - 8) * 200)
        theaterprimos = round((daydiff - 30) / 30 + 1) * sum(acts[:theater])
        onslaughtprimos = (db.execute('SELECT COUNT(*) FROM versions WHERE phase_1 BETWEEN ? AND ?', start_date, end_date)[0]['COUNT(*)']) * (onslaught * 150)
        total['endgame content'] = abyssprimos + theaterprimos + onslaughtprimos

        # PAIMON'S BARGAINS
        starglitter = request.form.get('starglitter')
        stardust = request.form.get('stardust')
        if not starglitter or not stardust:
            return render_template('/calculations.html', regions=regions, message="One or more Paimon's Bargains fields are empty", active='calculations')
        try:
            starglitter = int(starglitter)
            stardust = int(stardust)
        except ValueError:
            return render_template('/calculations.html', regions=regions, message="Paimon's Bargains inputs must be non-negative integers", active='calculations')
        if starglitter < 0 or stardust < 0:
            return render_template('/calculations.html', regions=regions, message="Paimon's Bargains inputs must be non-negative integers", active='calculations')
        starglitterprimos = int(starglitter / 5) * 160
        stardustprimos = 0
        for _ in range(months):
            fates = min(5, stardust // 75)
            if fates == 0:
                break
            stardust -= fates * 75
            stardustprimos += fates * 160
        total["Paimon's bargains"] = starglitterprimos + stardustprimos

        realtotal = sum(total.values())
        return render_template('/calculated.html', total=total, active='calculations', realtotal=realtotal)
    else:
        return render_template('/calculations.html', active='calculations', regions=regions)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            return render_template('/login.html', message='Username or password field was blank', active='login')

        rows = db.execute('SELECT * FROM users WHERE username = ?', username)
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):
            return render_template('/login.html', message='Username and/or password are incorrect', active='login')

        session["user_id"] = rows[0]["id"]

        return redirect("/")
    else:
        try:
            if session['user_id']:
                return redirect('/')
        except KeyError:
            return render_template('/login.html', active='login')

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    return redirect('/')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirmation = request.form.get('confirmation')
        if not username or not password or not confirmation:
            return render_template('/register.html', message='One or more fields are blank', active='login')

        rows = db.execute('SELECT * FROM users WHERE username = ?', username)
        if len(rows) != 0:
            return render_template('/register.html', message='Username is taken', active='login')
        if password != confirmation:
            return render_template('/register.html', message='Passwords do not match', active='login')

        db.execute('INSERT INTO users(username, hash) VALUES (?,?)', username, generate_password_hash(password))

        return redirect("/login")
    else:
        return render_template('/register.html', active='login')

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        try:
            new_username = request.form.get('username')
            if not new_username:
                new_password = request.form.get('password')
                confirmation = request.form.get('confirmation')
                if not new_password or not confirmation:
                    deletemes = request.form.get('delete_acc')
                    if not deletemes:
                        bug_report = request.form.get('bug_report')
                        if not bug_report:
                            try:
                                if session['user_id']:
                                    return render_template('/settings.html', active='settings', message='One or more fields are blank')
                            except KeyError:
                                return render_template('/settings.html', active='settings', message='One or more fields are blank', login='no')
                        try:
                            if int(db.execute('SELECT bugs FROM users WHERE id = ?', session['user_id'])[0]['bugs']) == 0:
                                return render_template('/settings.html', active='settings', message='You have submitted too many bugs. Please wait to submit more.')
                            db.execute('INSERT INTO bugs(user_id, desc) VALUES (?, ?)', session['user_id'], bug_report)
                            db.execute('UPDATE users SET bugs = bugs - 1 WHERE id = ?', session['user_id'])
                            return render_template('/settings.html', active='settings')
                        except KeyError:
                            if int(db.execute("SELECT COUNT(*) FROM bugs WHERE user_id = 0 AND DATE(time_submitted) = DATE('now', 'localtime')")[0]['COUNT(*)']) >= 25:
                                return render_template('/settings.html', active='settings', message='There are too many bug reports being submitted at the moment. Please wait to submit more.', login='no')
                            print(int(db.execute("SELECT COUNT(*) FROM bugs WHERE user_id = 0 AND DATE(time_submitted) = DATE('now', 'localtime')")[0]['COUNT(*)']))
                            db.execute("INSERT INTO bugs(user_id, desc) VALUES (0, ?)", bug_report)
                            return render_template('/settings.html', active='settings', login='no')
                    if session['user_id']:
                        if deletemes != 'DELETE':
                            return render_template('/settings.html', active='settings', message="Input did not match 'DELETE'")
                    db.execute('DELETE FROM todo WHERE user_id = ?', session['user_id'])
                    db.execute('DELETE FROM users WHERE id = ?', session['user_id'])
                    return redirect('/logout')
                if check_password_hash(db.execute('SELECT hash FROM users WHERE id = ?', session['user_id'])[0]['hash'], new_password):
                    return render_template('/settings.html', active='settings', message='Old password and new password match')
                if new_password != confirmation:
                    return render_template('/settings.html', active='settings', message='Password and confirmation do not match')
                db.execute('UPDATE users SET hash = ? WHERE id = ?', generate_password_hash(new_password), session['user_id'])
                return redirect('/')
            if db.execute('SELECT username FROM users WHERE id = ?', session['user_id'])[0]['username'] == new_username:
                return render_template('/settings.html', active='settings', message='Old username and new username match')
            if db.execute('SELECT username FROM users').count(new_username) != 0:
                return render_template('/settings.html', active='settings', message='Username is taken')
            db.execute('UPDATE users SET username = ? WHERE id = ?', new_username, session['user_id'])
            return redirect('/')
        except KeyError:
            return render_template('/settings.html', active='settings', login='no')
    else:
        try:
            if session['user_id']:
                return render_template('/settings.html', active='settings')
        except KeyError:
            return render_template('/settings.html', active='settings', login='no')
