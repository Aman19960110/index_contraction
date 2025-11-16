import pandas as pd
import plotly.express as px

df20 = pd.read_csv('index_series_20.csv',names=['date','index'],parse_dates=['date'],skiprows=1)
df20.head()
df50 = pd.read_csv('index_series_50.csv',names=['date','index'],parse_dates=['date'],skiprows=1)
df50.head()

df_weight_20 = pd.read_csv('weights_per_quater_20.csv')
df_weight_20.head()
df_weight_50 = pd.read_csv('weights_per_quater_50.csv')
df_weight_50.head()

fig = px.line()
fig.add_scatter(x=df20['date'], y=df20['index'], mode='lines', name='Index 20')
fig.add_scatter(x=df50['date'], y=df50['index'], mode='lines', name='Index 50')

fig.update_layout(title="Index 20 vs Index 50")
fig.show()

import pandas as pd
import plotly.graph_objs as go
from plotly.subplots import make_subplots

# Load data
df20 = pd.read_csv('index_series_20.csv', names=['date','index'], parse_dates=['date'], skiprows=1)
df50 = pd.read_csv('index_series_50.csv', names=['date','index'], parse_dates=['date'], skiprows=1)

w20 = pd.read_csv('weights_per_quater_20.csv')
w50 = pd.read_csv('weights_per_quater_50.csv')

# ---- Choose quarter ----
quarter = "2024-03-31"
# ------------------------

# Build weight table
w20_q = w20[['Unnamed: 0', quarter]].rename(columns={'Unnamed: 0': 'Ticker', quarter: 'Weight 20'})
w50_q = w50[['Unnamed: 0', quarter]].rename(columns={'Unnamed: 0': 'Ticker', quarter: 'Weight 50'})
weights = pd.merge(w20_q, w50_q, on='Ticker', how='outer')

# ---- PLOTLY FIGURE WITH TABLE ----
fig = make_subplots(
    rows=2, cols=1,
    shared_xaxes=False,
    row_heights=[0.70, 0.30],
    vertical_spacing=0.12,
    specs=[[{"type": "scatter"}],
           [{"type": "table"}]]
)

# Line chart
fig.add_trace(go.Scatter(
    x=df20['date'], y=df20['index'],
    mode='lines', name='Index 20'
), row=1, col=1)

fig.add_trace(go.Scatter(
    x=df50['date'], y=df50['index'],
    mode='lines', name='Index 50'
), row=1, col=1)

# Table below chart
fig.add_trace(
    go.Table(
        header=dict(
            values=list(weights.columns),
            fill_color='lightgrey',
            align='left',
            font=dict(size=12)
        ),
        cells=dict(
            values=[weights[col] for col in weights.columns],
            align='left',
            font=dict(size=11)
        )
    ),
    row=2, col=1
)

fig.update_layout(
    height=900,
    title=f"Index 20 vs Index 50 + Weights for Quarter {quarter}",
    showlegend=True
)

fig.show()
