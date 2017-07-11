from flask import Flask, render_template, request, g
from datetime import datetime
from database import connect_db, get_db
app = Flask(__name__)

@app.teardown_appcontext #this is more specific to flask so i'll leave it here only.. rather thn moving to database.py file
def close_db(error):
	if hasattr(g,'sqlite.db'):
		g.sqlite_db.close()


@app.route('/', methods=['POST','GET']) #for home
def index():
	db=get_db()
	if request.method == 'POST':
		date = request.form['date'] #Assuming that daate is in YYYY-MM-DD format
		dt = datetime.strptime(date, '%Y-%m-%d')
		database_date = datetime.strftime(dt, '%Y%m%d')
		
		db.execute('insert into log_date (entry_date) values (?)', [database_date])
		db.commit()

	cur=db.execute('select log_date.entry_date, sum(food.protein) as protein, sum(food.carbohydrates) as carbohydrates, sum(food.fat) as fat, sum(food.calories) as calories from log_date\
		left join food_date on food_date.log_date_id=log_date.id\
		left join food on food.id=food_date.food_id \
		group by log_date.entry_date order by log_date.entry_date desc')
	results=cur.fetchall()

	date_results = []

	for i in results:
		single_date = {}

		single_date['entry_date'] = i['entry_date']
		single_date['protein'] = i['protein'] #as protien in query if as protein1 change this i['protein1']
		single_date['carbohydrates'] = i['carbohydrates']
		single_date['fat'] = i['fat']
		single_date['calories'] = i['calories']

		d=datetime.strptime(str(i['entry_date']), '%Y%m%d')
		single_date['pretty_date'] = datetime.strftime(d,'%B %d, %Y')

		date_results.append(single_date)

	return render_template('home.html', results=date_results)

@app.route('/view/<date>', methods=['POST', 'GET'])	#this date will be like 20170826 #for viewing day, various ways for particular date.. by adding parameter or by using query string value...
def view(date):
	db=get_db()

	cur = db.execute('select id, entry_date from log_date\
	where entry_date = ?', [date])
	date_result= cur.fetchone() #will haveid as well as the entry date as result['id'], result['entry_date']

	if request.method=='POST':
		db.execute('insert into food_date (food_id, log_date_id) values (?, ?)', [request.form['food-select'], date_result['id']])
		db.commit()

	d=datetime.strptime(str(date_result['entry_date']), '%Y%m%d')
	pretty_date = datetime.strftime(d,'%B %d, %Y')

	food_cur = db.execute('select id, name from food')
	food_results=food_cur.fetchall()

	log_cur=db.execute('select food.name, food.protein, food.carbohydrates, food.fat, food.calories from log_date\
		join food_date on food_date.log_date_id=log_date.id\
		join food on food.id=food_date.food_id where entry_date = ?', [date])
	log_results=log_cur.fetchall()

	#for totaling the values there can be various ways.. like quering database and get sum or by python calc... we will use python clac as it is generally faster as quering database is time consuming comparatively
	totals = {} #dictionary
	totals['protein'] = 0
	totals['carbohydrates'] = 0
	totals['fat'] = 0
	totals['calories'] = 0
	
	for food in log_results:
		totals['protein'] += food['protein'] #this means the result that we get though query is an array but the variable we take for loop make it individual dictionary..
		totals['carbohydrates'] += food['carbohydrates']
		totals['fat'] += food['fat']
		totals['calories'] += food['calories']

	return render_template('day.html', entry_date= date_result['entry_date'], pretty_date=pretty_date,\
		food_results=food_results, log_results=log_results, totals=totals)

@app.route('/food', methods=['GET', 'POST']) #for adding food
def food():
	db=get_db()
	if request.method == 'POST':
		name = request.form['food-name']
		protein = int(request.form['protein'])
		carbohydrates = int(request.form['carbohydrates']) 
		fat = int(request.form['fat']) #converted into int just to make sure they are int

		calories = protein * 4 + carbohydrates * 4 + fat * 9

		#db=get_db()
		db.execute('insert into food (name, protein, carbohydrates, fat, calories) values (?, ?, ?, ?, ?)', \
			[name, protein, carbohydrates, fat, calories])
		db.commit()

	cur=db.execute('select name, protein, carbohydrates, fat, calories from food')
	results=cur.fetchall()

	return render_template('add_food.html', results=results)

#database-  3tables..  1- dates 2-foods list 3- track when each food applies to each data
#this will be the mapping b/w food and dates.. 

if __name__ == '__main__':
	app.run(debug=True)