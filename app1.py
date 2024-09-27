# Sanjna Sunil, sanjnasu@usc.edu
# ITP 216, Fall 2023
# Section: 1
# Final Project
# Description: This final project is about visualizing financial data from Nasdaq for the past ten years (2013-2023). It has to main routes frm the home page
# one of which is showing historical data of low and high stocks over the yeras. Predictions that are past the year 2023 will show average stock values along with the average
# predictions of them (the low and high) based on a dynamic request of the input years. That is the aggregation, where it finds the average between Low and HIgh,
# Then provides a prediction model of thsoe as well based on user input. On the home page, there is also an option for the prediction page of nasdaq.
# The prediction will show trade ranges between low and high, and the predictions show the expected and predicted trade ranges based off of the user input. There is also
# a meaningful aggreaion finding the trade ranges and returs from low and high. I used a common db_create_dataframe from both because they are only sing dates, low, and high
# from their the respective endpoints. There is also a create_figure, one for the home page and hisotircal oen and one for the predction data. these both create two different
# figures for the endpoints. The historical data uses data points and lines, whereas the predictive data uses barcharts.


import datetime
import io
import os
import sqlite3 as sl

import pandas as pd
from flask import Flask, redirect, render_template, request, session, url_for, send_file, send_from_directory
from matplotlib import pyplot as plt
import matplotlib.dates as mdates
from matplotlib.figure import Figure
from sklearn.linear_model import LinearRegression
import numpy as np



app = Flask(__name__, static_url_path='/static')
db = "ndaq_data.db"
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0



#setting the home get endpoint. it will redirect to the template of home1
@app.route('/')
def home():
    return render_template('home1.html')


#setting route for endpoints for the nasdaq data,this is for the historical data. will show the the historical data from 2013-2023 of all the high and low data.
@app.route('/see_nasdaq_data', methods=['GET', 'POST'])
def see_nasdaq_data():
    title = "Historical Data"
    img = io.BytesIO()
    img_filename = None

    if request.method == 'POST':
        target_date_str = request.form.get('year') #taking in teh target year from thehtml input

        if target_date_str is not None:
            try:
                target_date = datetime.datetime.strptime(target_date_str, '%m/%d/%y')  # chaning the format just in case
                img_filename = target_date.strftime('%Y-%m-%d') + "_high_low.png"  # UPDATE THE FILE NAME!! This actually wasn't workign before until i did this
                stock_data = db_create_dataframe(target_date) #new data frame based off of the target date and getting all the needed data points

                if stock_data.empty: #EDGE CASE!! in the case the stock data is empty, default template
                    return render_template('data.html', title=title, error_message=f"No data available for {target_date}", display_form=True, form_action="/see_nasdaq_data",  form_fields=[{"id": "year", "label": "Target Date"}], content_type='image/png')

                # creating and seeting up the figure
                fig = create_figure(stock_data, target_date)

                if fig is None: #edge case for teh figure
                    return render_template('data.html', title=title, error_message=f"No data available for {target_date}", display_form=True, form_action="/see_nasdaq_data", form_fields=[{"id": "year", "label": "Target Date"}], content_type='image/png')

                img = io.BytesIO() #converting to the bytesIO type
                fig.savefig(img, format='png') #turn it inot a PNG!!
                img.seek(0)

                # Regular display graph for the user based if passes all the cases above
                return render_template('data.html', title=title, img_data=img.getvalue(), display_form=True, form_action="/see_nasdaq_data", form_fields=[{"id": "year", "label": "Target Date"}], img_filename=img_filename, content_type='image/png')

            except ValueError: #in case of error, need to use for edge case
                return render_template('data.html', title=title, img_data=img.getvalue(), display_form=True, form_action="/see_nasdaq_data", form_fields=[{"id": "year", "label": "Target Date"}], img_filename=img_filename, content_type='image/png', error_message="Invalid date format. Please enter a valid date.")

    # default in case they all fail
    return render_template('data.html', title=title, display_form=True,
                           form_action="/see_nasdaq_data",
                           form_fields=[{"id": "year", "label": "Target Date"}],
                           content_type='image/png')


#providing the endpoint image. sending the image to the html as well adding it to the folder (static->image)
@app.route("/image_endpoint/<target_year>")
def image_endpoint(target_year):
    target_year = os.path.basename(target_year)
    image_folder = "static/images"
    return send_from_directory(image_folder, f"{target_year}.png", as_attachment=True)


#figure request. will create the figure with  the create figure function, save it, and set the image path withteh arugmetn url
@app.route("/your_route/<data_request>/<locale>")
def fig(data_request, locale):
    # creating the figure using create_figure
    fig = create_figure(data_request, locale)

    # saving it with teh bytesIO
    img = io.BytesIO()
    fig.savefig(img, format='png')
    img.seek(0)

    # using url as image render for hte template
    img_path = f"{data_request}.png"
    return render_template("data.html", img_path=url_for("image_endpoint", target_year=img_path))



#create temaplate is a function that will create the temapltes based off of the data ad the target date. this function is custom to the histoircal data. will create dot/line data
def create_figure(data, target_date):
    if data is None or data.empty: #ifthe data is empty or n/a
        print(f"No data available for {target_date}")
        return None

    # have to convert the date to the datetime to be processed based off of the y/m/d (how it is in teh db)
    data['Date'] = pd.to_datetime(data['Date'], format='%Y-%m-%d')
    fig, ax = plt.subplots() #setting figure and the ax to the subplots

    if target_date <= data["Date"].max(): #if the values are BELOW 2023, it will plot the regular low and high values
        # plottig the high values and have a line connection between them all. USe O for the dots
        ax.plot(data["Date"], data["High"], label='High', marker='o', linestyle='-', linewidth=2)
        # same thig for the low values,
        ax.plot(data["Date"], data["Low"], label='Low', marker='o', linestyle='-', linewidth=2)


    else: #if the values are beyond 2023, that is when we use the predictions here. I don't wnat to use predcitions when they alrady ahve values with hihg and low
        # using sciKit and ML to get the prediciotn
        data['Days'] = (data['Date'] - data['Date'].min()).dt.days #fnding the days
        y = (data['High'] + data['Low']) / 2 # finding the average of high and low
        model = LinearRegression()
        model.fit(data['Days'].values.reshape(-1, 1), y) #setting hte model to fit those values

        # making the new dates for hte predicionts
        future_dates = pd.date_range(start=data['Date'].min(), end=target_date, freq='D')
        future_days = (future_dates - data['Date'].min()).days.values.reshape(-1, 1)
        future_values = model.predict(future_days)
        ax.plot(data["Date"], y, label='Historical Average', marker='o', linestyle='-', linewidth=2)

        # finaly, plot hte final preicated value
        ax.plot(future_dates, future_values, label='Predicted Average', marker='o', linestyle='--', linewidth=2)

    ax.legend() #get the legend! (no, not john legend)
    ax.set(xlabel="Date", ylabel="Low and High Average") #x and y labels to the proper

    # setting the x axis
    ax.set_xlim(data["Date"].min(), target_date)
    fig.subplots_adjust(bottom=0.15)

    img_filename = f"{target_date.strftime('%Y-%m-%d')}_high_low.png"
    img_path = os.path.join("static/images", img_filename)
    fig.savefig(img_path, format='png')
    plt.close(fig)

    # print(f"Debug Image Path: {img_path}") #i used this for debugging, not needed, just prints out the file path for the images

    return fig #retunign the fig image


#this is reading in the db and making the dataframe based off hte user input date
def db_create_dataframe(target_date): #taking in teh target_date as an input to check for validity, then  providing a dataframe
    conn = sl.connect(db) #setting connection to the db
    curs = conn.cursor()
    df = pd.DataFrame() #dataframe initiailizatn from pandas
    table = "stock_data" #getting the data from the stock data

    start_date = '2010-01-02' #ok this is a bit tricky. the first data peice is 1/2/13. Any target date can't pre-pass that or it ends up in an error.
    #ALSO start date will the begining of which the target date will get all the data from start date to the end date
    end_date = target_date.strftime('%Y-%m-%d') #chanign the date format, the db has that format so it must adjust
    stmt = f"SELECT date, high, low FROM {table} WHERE date BETWEEN ? AND ?" #querrying the db to get the proper data
    data = curs.execute(stmt, (start_date, end_date))
    items = curs.fetchall() #fetching ALL the data, it should start fromt eh start-date all the way to the end data pon

    if items:
        df = pd.DataFrame(items, columns=["Date", "High", "Low"]) #df with tehse data
        df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d').dt.strftime('%Y-%m-%d')

    conn.close() #close the connection and return the final dataframe
    return df



#this route is for hte nasdaq preiction. it is going to predict all dates for the stock/trange ranges. it will return the template with teh figure and proper data as wlel
@app.route('/nasdaq_prediction', methods=['GET', 'POST'])
def nasdaq_prediction():
    title = "Nasdaq Prediction" #setting the title
    img = io.BytesIO()
    img_filename = None

    if request.method == 'POST':
        target_date_str = request.form.get('year')

        if target_date_str is not None: #if the target date isn't empty and teh user actually cares
            try:
                target_date = datetime.datetime.strptime(target_date_str, '%m/%d/%y')  # making sure it's teh correct date format
                img_filename = target_date.strftime('%Y-%m-%d') + "_nasdaq_prediction.png"  # ALWAYS UPDATE THE FILE NAME!!

                nasdaq_data = db_create_dataframe(target_date) #creating a df baesd off of that data

                if nasdaq_data.empty: #if the df is empty, render the template iwth that
                    return render_template('data.html', title=title, error_message=f"No data available for {target_date}", display_form=True, form_action="/nasdaq_prediction", form_fields=[{"id": "year", "label": "Target Date"}], content_type='image/png')

                fig_nasdaq = create_nasdaq_prediction(nasdaq_data, target_date) #making figure

                if fig_nasdaq is None:
                    return render_template('data.html', title=title, error_message=f"No data available for {target_date}", display_form=True, form_action="/nasdaq_prediction", form_fields=[{"id": "year", "label": "Target Date"}], content_type='image/png')

                # saving img to bytesiO
                img = io.BytesIO()
                fig_nasdaq.savefig(img, format='png')
                img.seek(0)

                # after all, render template
                return render_template('data.html', title=title, img_data=img.getvalue(), display_form=True, form_action="/nasdaq_prediction", form_fields=[{"id": "year", "label": "Target Date"}], img_filename=img_filename,content_type='image/png')

            except ValueError: #in case of error
                return render_template('data.html', title=title, img_data=img.getvalue(), display_form=True, form_action="/nasdaq_prediction", form_fields=[{"id": "year", "label": "Target Date"}], img_filename=img_filename, content_type='image/png', error_message="Invalid date format. Please enter a valid date.")

    # using a default return statement in case none of the conditions are met
    return render_template('data.html', title=title, display_form=True, form_action="/nasdaq_prediction", form_fields=[{"id": "year", "label": "Target Date"}], content_type='image/png')



#this is the nasdaq preiction (kind of like the earlier create_figure) but for the preidciton one speficially.
#i am using this one specifalcly because the nasdaq prediction data is calctig trade ranges rahte rhtan just hihg and low prediciotns.
def create_nasdaq_prediction(data, target_date):
    if data is None or data.empty:
        print(f"No data available for {target_date}")
        return None

    data['Date'] = pd.to_datetime(data['Date'], format='%Y-%m-%d') #getting the date and setting up teh format
    fig, ax = plt.subplots() #setting matplot lib plots and axis+ fig

    if target_date >= data["Date"].min(): #making sure the target date is after hte minimum (1/2/13)
        title = "Predictive Data of Trade Ranges of High and Low" #setting title

        data['Days'] = (data['Date'] - data['Date'].min()).dt.days
        model = LinearRegression() #using the ML sciKit linearregressino model
        model.fit(data['Days'].values.reshape(-1, 1), data["High"] - data["Low"]) #settng it to fit with the data of high ad low

        future_dates = pd.date_range(start=data['Date'].min(), end=target_date, freq='D') #findin the figur edates with the ranges
        future_days = (future_dates - data['Date'].min()).days.values.reshape(-1, 1) #findng the future dates with the reshare s well. taking future dates - min date and reshae


        future_trading_ranges = model.predict(future_days) #gettng ranges
        ax.bar(data["Date"], data["High"] - data["Low"], label='Historical Trading Range', color='blue', alpha=0.7) #then set the label to hiostircal
        ax.bar(future_dates, future_trading_ranges, label='Predicted Trading Range', color='orange', alpha=0.7)#for the predicted dates

    ax.legend() #set up the legend
    ax.set(xlabel="Date", ylabel="Trading Range", title=title) #seting x and y labels
    ax.set_xlim(data["Date"].min(), target_date if title == "Existing Data" else future_dates[-1]) #x axis ticks and limits so it extendds the whole way
    fig.subplots_adjust(bottom=0.15) #adjusting hte size

    img_filename = f"{target_date.strftime('%Y-%m-%d')}_nasdaq_prediction.png"  # updated filename
    img_path = os.path.join("static/images", img_filename) #getting it to the path
    fig.savefig(img_path, format='png')
    plt.close(fig) #close the plot

    # print(f"Debug Image Path: {img_path}")  I USED THIS FOR DEBUGGING NOT NEEDED!!

    return fig #return the plot





if __name__ == '__main__':
    app.run(debug=True)