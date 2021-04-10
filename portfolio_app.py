import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

from src.alpaca_data import AlpacaData


class AppViz(AlpacaData):
    def __init__(self, start_date, end_date):
        super().__init__(start_date, end_date)
        self.start_date = start_date
        self.end_date = end_date

    def benchmark_performance(self, comp_ticker):
        comp_df = self.get_portfolio_history(comp_ticker)

        fig = go.Figure()

        fig.add_trace(go.Scatter(x=comp_df['Date'],
                                 y=comp_df['Portfolio'],
                                 mode='lines',
                                 line_shape='spline',
                                 line={'color': '#2069e0', 'width': 4},
                                 name='Portfolio Returns'
                                 )
                      )
        fig.add_trace(go.Scatter(x=comp_df['Date'],
                                 y=comp_df[comp_ticker],
                                 mode='lines',
                                 line_shape='spline',
                                 line={'color': '#bebebe', 'width': 4},
                                 name=f'{comp_ticker} Returns'
                                 )
                      )

        fig.update_layout(template='plotly_dark',
                          xaxis={'showgrid': False},
                          yaxis={'title': '% Retrun',
                                 'tickformat': '%',
                                 'showgrid': False}
                          )
        mr_row = comp_df.iloc[-1, :]

        diff = np.abs((mr_row['Portfolio'] - mr_row[comp_ticker]) * 100)
        summary_base = f'My portfolio is currently{diff: .1f} percentage pts '

        if mr_row['Portfolio'] > mr_row[comp_ticker]:
            summary_text = summary_base + f'better than {comp_ticker}'
        else:
            summary_text = summary_base + f'worse than {comp_ticker}'

        return fig, summary_text

    def summarize_portfolio(self):
        pass

    def show_orders(self):
        pass


if __name__ == '__main__':
    st.header('Portfolio Tracker')

    st.sidebar.header('Options')
    start_date = st.sidebar.date_input('Start Date',
                                       value=pd.to_datetime('2021-04-01'),
                                       min_value=pd.to_datetime('2021-04-01')
                                       )
    end_date = st.sidebar.date_input('End Date')
    comp_ticker = st.sidebar.text_input('Benchmark Ticker Symbol', value='SPY', max_chars=6)

    av = AppViz(start_date, end_date)
    fig, summ_text = av.benchmark_performance(comp_ticker=comp_ticker)
    st.plotly_chart(fig)
    st.text(summ_text)
