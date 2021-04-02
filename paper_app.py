import os
import pandas as pd
import streamlit as st
import datetime as dt
import plotly.graph_objects as go
import alpaca_trade_api as trade_api


class PortfolioApp:
    def __init__(self, start_date, end_date):
        self.start_date = start_date
        self.end_date = end_date
        self.api = trade_api.REST(key_id=os.environ.get('API_KEY'),
                                  secret_key=os.environ.get('SECRET_KEY'),
                                  base_url='https://paper-api.alpaca.markets',
                                  api_version='v2'
                                  )

    def plot_portfolio_performance(self, comparison='SPY'):
        day_diff = (pd.to_datetime(self.end_date) - pd.to_datetime(self.start_date)).days

        port_resp = self.api.get_portfolio_history(date_start=self.start_date,
                                                   date_end=self.end_date,
                                                   timeframe='1D'
                                                   )
        comp_resp = self.api.get_barset(comparison, 'day', limit=day_diff)

        port = pd.DataFrame({'Portfolio': port_resp.equity,
                             'Date': [dt.datetime.fromtimestamp(x) for x in port_resp.timestamp]})
        comp = pd.DataFrame({comparison: [i.c for i in comp_resp[comparison]],
                             'Date': [i.t for i in comp_resp[comparison]]})
        port['Date'] = pd.to_datetime(port['Date']).dt.strftime('%Y-%m-%d')
        comp['Date'] = pd.to_datetime(comp['Date']).dt.strftime('%Y-%m-%d')

        port_df = pd.merge(port, comp, on='Date')

        # index performance (apples-to-apples) + make dt a date
        port_df['Portfolio'] = port_df['Portfolio'] / port_df['Portfolio'].iloc[0]
        port_df[comparison] = port_df[comparison] / port_df[comparison].iloc[0]

        fig = go.Figure()

        fig.add_trace(go.Scatter(x=port_df['Date'],
                                 y=port_df['Portfolio'] - 1,
                                 mode='lines',
                                 line={'color': 'rgba(180, 10, 20, .8)'},
                                 line_shape='spline',
                                 name='Portfolio Returns'
                                 )
                      )
        fig.add_trace(go.Scatter(x=port_df['Date'],
                                 y=port_df[comparison] - 1,
                                 mode='lines',
                                 line={'color': 'rgba(20, 10, 180, .8)', 'dash': 'dot'},
                                 line_shape='spline',
                                 name=f'{comparison} Returns'
                                 )
                      )
        fig.update_layout(xaxis={'showgrid': False},
                          yaxis={'title': 'Percent Return',
                                 'tickformat': '.1%',
                                 'showgrid': False,
                                 'zeroline': False
                                 }
                          )

        return fig


    def plot_orders(self):
        resp = self.api.list_orders(status='closed',
                                    limit=100,
                                    nested=True
                                    )
        df_list = []

        for order in resp:
            df_list.append(pd.DataFrame({'Symbol': order.symbol,
                                         'Buy/Sell': order.side,
                                         'Shares': int(order.filled_qty),
                                         'Price': float(order.filled_avg_price),
                                         'Total': round(float(order.filled_avg_price) * int(order.filled_qty), 0),
                                         'Equity Type': order.asset_class,
                                         'Date': pd.to_datetime(order.filled_at).strftime('%Y-%m-%d')
                                         },
                                        index=[0]))

        orders = pd.concat(df_list)

        fig = go.Figure()

        for ticker in orders['Symbol'].unique():
            tdf = orders.loc[orders['Symbol'] == ticker].groupby(['Date']).sum()[['Shares', 'Total']].reset_index()
            tdf['Avg Price'] = tdf['Total'] / tdf['Shares']

            fig.add_trace(go.Bar(x=tdf['Date'],
                                 y=tdf['Total'],
                                 text=tdf['Shares'],
                                 name=ticker
                                 )
                          )
        fig.update_layout(yaxis={'title': 'Total Purchased',
                                 'tickformat': '$,.0f',
                                 'showgrid': False
                                 }
                          )

        return fig


if __name__ == '__main__':
    yesterday = (dt.datetime.now() - dt.timedelta(days=1)).strftime('%Y-%m-%d')

    start_date = st.sidebar.date_input('Start Date',)# min_value=pd.to_datetime('2020-04-01'))
    end_date = st.sidebar.date_input('End Date',)# min_value=pd.to_datetime('2020-04-02'))
    comp_ticker = st.sidebar.text_input('Pick Comparison Ticker', value='SPY', max_chars=6)

    pa = PortfolioApp(start_date=start_date, end_date=end_date)
    st.plotly_chart(pa.plot_portfolio_performance(comparison=comp_ticker))
    st.plotly_chart(pa.plot_orders())
