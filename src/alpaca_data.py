import os
import pandas as pd
import datetime as dt
import alpaca_trade_api as trade_api


class AlpacaData:
    def __init__(self, start_date, end_date):
        self.start_date = start_date
        self.end_date = end_date
        self.api = trade_api.REST(key_id=os.environ.get('API_KEY'),
                                  secret_key=os.environ.get('SECRET_KEY'),
                                  base_url='https://paper-api.alpaca.markets',
                                  api_version='v2'
                                  )

    def get_portfolio_history(self, comparison='SPY'):
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
        port_df['Portfolio'] = (port_df['Portfolio'] / port_df['Portfolio'].iloc[0]) - 1
        port_df[comparison] = (port_df[comparison] / port_df[comparison].iloc[0]) - 1

        return port_df


    def get_order_data(self):
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

        return orders

    def get_position_sizing(self):
        '''

        :return:
        '''
        resp = self.api.list_positions()

        df_list = []

        for position in resp:
            tdf = pd.DataFrame({'Symbol': position.symbol,
                                'Shares': position.qty,
                                'Avg Price': position.avg_entry_price,
                                'Current Price': position.current_price,
                                'Total Cost': position.cost_basis,
                                'Market Value': position.market_value
                                }, index=[0]
                               )
            df_list.append(tdf)

        return pd.concat(df_list)
