import pandas as pd
import plotly.graph_objs as go
from plotly.subplots import make_subplots

# -------------------------------------------------------------------
# LOAD DATA
# -------------------------------------------------------------------
df20 = pd.read_csv('index_series_20.csv', names=['date','index'], parse_dates=['date'], skiprows=1)
df50 = pd.read_csv('index_series_50.csv', names=['date','index'], parse_dates=['date'], skiprows=1)

w20 = pd.read_csv('weights_per_quater_20.csv')
w50 = pd.read_csv('weights_per_quater_50.csv')

quarters = [c for c in w20.columns if c != "Unnamed: 0"]

# -------------------------------------------------------------------
# TOTAL RETURN CALCULATION
# -------------------------------------------------------------------
tr20 = (df20['index'].iloc[-1] / df20['index'].iloc[0] - 1) * 100
tr50 = (df50['index'].iloc[-1] / df50['index'].iloc[0] - 1) * 100

total_return_table = pd.DataFrame({
    "Index": ["Index 20", "Index 50"],
    "Total Return": [f"{tr20:.2f}%", f"{tr50:.2f}%"]
})

# -------------------------------------------------------------------
# WEIGHTS TABLE CREATION FUNCTION
# -------------------------------------------------------------------
def build_weights(q):
    w20_q = w20[['Unnamed: 0', q]].rename(columns={'Unnamed: 0': 'Ticker', q: 'Weight 20'})
    w50_q = w50[['Unnamed: 0', q]].rename(columns={'Unnamed: 0': 'Ticker', q: 'Weight 50'})
    
    merged = pd.merge(w20_q, w50_q, on='Ticker', how='outer').sort_values('Ticker')

    # Replace NaN with 0 before percentage conversion
    merged[['Weight 20', 'Weight 50']] = merged[['Weight 20', 'Weight 50']].fillna(0)

    # Convert to %
    for col in ["Weight 20", "Weight 50"]:
        merged[col] = merged[col].astype(float) * 100
        merged[col] = merged[col].round(2).astype(str) + "%"

    # Replace 0% with blank
    merged.replace({"0.0%": "", "0%": ""}, inplace=True)

    # Convert to list-of-strings for Plotly
    for col in merged.columns:
        merged[col] = merged[col].astype(str).tolist()

    return merged

default_q = quarters[-1]
weights = build_weights(default_q)

# -------------------------------------------------------------------
# FIGURE SETUP (3 ROWS)
# -------------------------------------------------------------------
fig = make_subplots(
    rows=3, cols=1,
    shared_xaxes=False,
    row_heights=[0.60, 0.10, 0.30],
    vertical_spacing=0.10,
    specs=[
        [{"type": "scatter"}],
        [{"type": "table"}],
        [{"type": "table"}]
    ]
)

# -------------------------------------------------------------------
# ROW 1 — LINE CHART
# -------------------------------------------------------------------
fig.add_trace(go.Scatter(
    x=df20['date'], y=df20['index'], mode='lines', name='Index 20'),
    row=1, col=1
)

fig.add_trace(go.Scatter(
    x=df50['date'], y=df50['index'], mode='lines', name='Index 50'),
    row=1, col=1
)

# -------------------------------------------------------------------
# ROW 2 — TOTAL RETURN TABLE (TRACE INDEX 2)
# -------------------------------------------------------------------
fig.add_trace(
    go.Table(
        header=dict(values=list(total_return_table.columns), fill_color='lightgrey', align='left'),
        cells=dict(values=[total_return_table[col] for col in total_return_table.columns], align='left')
    ),
    row=2, col=1
)

# -------------------------------------------------------------------
# ROW 3 — WEIGHTS TABLE (TRACE INDEX 3)
# -------------------------------------------------------------------
fig.add_trace(
    go.Table(
        header=dict(values=list(weights.columns), fill_color='lightgrey', align='left'),
        cells=dict(values=[weights[col] for col in weights.columns], align='left'),
        columnwidth=[120, 60, 60]
    ),
    row=3, col=1
)

# Weight table trace index (0-based)
table_trace_index = 3

# -------------------------------------------------------------------
# DROPDOWN BUTTONS
# -------------------------------------------------------------------
dropdown_buttons = []

for q in quarters:
    new_weights = build_weights(q)
    header_vals = list(new_weights.columns)
    cell_vals = [new_weights[col] for col in new_weights.columns]

    dropdown_buttons.append(
        dict(
            label=q,
            method="restyle",
            args=[
                {
                    "header.values": [header_vals],
                    "cells.values": [cell_vals]
                },
                [table_trace_index]
            ]
        )
    )

fig.update_layout(
    height=1000,
    title="Index 20 vs Index 50 + Total Returns + Weights by Quarter",
    showlegend=True,
    updatemenus=[
        dict(
            buttons=dropdown_buttons,
            direction="down",
            x=1.05,
            y=0.72,
            xanchor="left",
            yanchor="middle"
        )
    ]
)

fig.show()
fig.write_html("index_comparison.html")
