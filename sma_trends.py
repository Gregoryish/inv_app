import pandas as pd
import numpy as np
# import yfinance as yf
import requests
import apimoex

import plotly.graph_objects as go
import datetime

import streamlit as st

dict_periods = {"1d": 1, "5d": 5, "1mo": 30, "3mo": 3 * 30, "6mo": 6 * 30, "1y": 365, "2y": 2 * 365, "5y": 5 * 365,
                    "10y": 10 * 365, "max": None}
# def get_data_ticker_yfinance(ticker_name, period='1y'):
#     ticker = yf.Ticker(ticker_name)

#     data = ticker.history(period=period, interval='1d')

#     return data


def get_data_ticker_moex(ticker_name, start=None, end=None):
    """
    
    """
    with requests.Session() as session:
        try:
            data = apimoex.get_board_history(session, ticker_name, start=start, end=end)
            df = pd.DataFrame(data)
            df.set_index('TRADEDATE', inplace=True)
        except:
            df = pd.DataFrame()
    return df


def get_data_ticker(ticker_name, period):
    """
    
    """

    if period != "max":
        days = dict_periods[period]
        end = datetime.datetime.today()+datetime.timedelta(days=1)
        start = end - datetime.timedelta(days=days)
        end_str = end.strftime("%Y-%m-%d")
        start_str = start.strftime("%Y-%m-%d")
    else:
        end_str = None
        start_str = None

    data = get_data_ticker_moex(ticker_name, start=start_str, end=end_str).rename(columns={'CLOSE': 'Close'})
    # if data.shape[0] == 0:
    #     data = get_data_ticker_yfinance(ticker_name, period=period)

    return data


def sma_calc(data, short=5, medium=30, long=90, ticker_name = None):
    """

    """

    dict_periods = {'SMA_short': short,
                    'SMA_medium': medium,
                    'SMA_long': long}

    cols = ['Close', 'SMA_short', 'SMA_medium', 'SMA_long']
    data['SMA_short'] = data['Close'].rolling(short, ).mean()
    data['SMA_medium'] = data['Close'].rolling(medium).mean()
    data['SMA_long'] = data['Close'].rolling(long).mean()
    data['Diff'] = data.SMA_medium - data.SMA_short
    data['Cross'] = np.select(
        [((data.Diff < 0) & (data.Diff.shift() > 0)), ((data.Diff > 0) & (data.Diff.shift() < 0))], ['Up', 'Down'],
        None)

    fig = go.Figure()
    for col in cols:
        if col in dict_periods:
            period = dict_periods[col]
            name = f"{col[:3]} - {period} d"
        else:
            name = col

        fig.add_trace(go.Scatter(x=data.index, y=data[col], name=name))

    if data[data['Cross'].notnull()]['Cross'].shape[0] >= 1:
        for cross_cat in data[data['Cross'].notnull()]['Cross'].unique():
            if cross_cat == 'Down':
                color = 'red'
            else:
                color = 'green'
            fig.add_trace(
                go.Scatter(x=data[data['Cross'] == cross_cat].index, y=data[data['Cross'] == cross_cat]['SMA_short'],
                           name=cross_cat, mode='markers',
                           opacity=0.5,
                           marker=dict(
                               color=color,
                               size=10,
                               line=dict(
                                   color=color,
                                   width=8
                               ))))

    fig.update_layout(title=f'<b>{ticker_name}</b>', width=700, height=500,

                      xaxis=dict(
                          rangeselector=dict(
                              buttons=list([
                                  dict(count=1,
                                       label="1m",
                                       step="month",
                                       stepmode="backward"),
                                  dict(count=6,
                                       label="6m",
                                       step="month",
                                       stepmode="backward"),
                                  dict(count=1,
                                       label="YTD",
                                       step="year",
                                       stepmode="todate"),
                                  dict(count=1,
                                       label="1y",
                                       step="year",
                                       stepmode="backward"),
                                  dict(step="all")
                              ])
                          ),
                          rangeslider=dict(
                              visible=True
                          ),
                          type="date"
                      )
                      )
    # fig.show()
    return data, fig


def user_input_features():
    ticker_name = st.sidebar.text_input("Ticker", "NEE")
    period = st.sidebar.selectbox('Period', ('6mo','3mo','1y', '2y', '5y', '10y', 'max',))
    short_term = st.sidebar.slider('Short term', 5,10,7)
    mid_term = st.sidebar.slider('Medium term', 20,40,30)
    long_term =st.sidebar.slider('Long term', 90,180,100)

    data = get_data_ticker(ticker_name, period)
    data, fig = sma_calc(data,  short=short_term, medium=mid_term, long=long_term, ticker_name=ticker_name)
    return data, fig


st.write("""# Hello!""")

st.subheader("""this is a tool based on the ***moving average method*** to analyse stock trends 
Data information from *Yahoo! Finance API* and *MOEX API* libraries""")
st.markdown("""Information about [moving average method](https://stocktrainer.ru/trendovyiy-indikator-prostoe-ckolzyashhee-crednee/)""")
st.markdown("""Created by [Grigory Ishimbaev](https://github.com/Gregoryish)""")
st.write('# Enter any Ticker on left sidebar')
st.sidebar.header("Set inputs")
data, fig = user_input_features()

st.write("""
Green markers ***Up - Signal to buy*** signal a further increase in the share price\n
Red markers ***Down - Signal to sell*** signal a further drop in the share price""")
st.write(fig)
changes = data[data['Cross'].notnull()]
st.write("Data Table")
st.write(changes)
