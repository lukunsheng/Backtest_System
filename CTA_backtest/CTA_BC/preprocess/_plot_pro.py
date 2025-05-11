import pandas as pd
import numpy as np
import os
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio
from plotly.offline import iplot
import warnings

# 新的qlib风格配置
qlib_template_config = {
    'paper_bgcolor': '#171B26',  # 深蓝灰背景
    'plot_bgcolor': '#171B26',
    'font_color': '#EAEAEA',    # 基础字体颜色
    'font_family': 'Arial',
    'font_size_base': 12,
    'title_font_size': 22,      # 主标题
    'title_font_color': '#FFFFFF',
    'colorway': ['#4E8EFB', '#50DDC2', '#FFC55C', '#FF7F7F', '#C48BFF', '#78D9EC'], # 新色板
    'legend_font_size': 11,
    'legend_bgcolor': 'rgba(23, 27, 38, 0.75)',
    'legend_bordercolor': 'rgba(60, 65, 80, 0.6)',
    'grid_color': 'rgba(70, 75, 90, 0.4)',
    'zeroline_color': 'rgba(100, 105, 120, 0.6)',
    'axis_tick_font_size': 10,
    'axis_tick_font_color': '#B8C2CC', # 浅蓝灰色刻度
    'axis_title_font_size': 13,
    'axis_title_font_color': '#D0D8E0',
    'subplot_title_font_size': 14, # 子图标题大小
}

# 应用qlib风格
def apply_qlib_style(fig):
    """应用qlib风格到plotly图形"""
    cfg = qlib_template_config
    fig.update_layout(
        paper_bgcolor=cfg['paper_bgcolor'],
        plot_bgcolor=cfg['plot_bgcolor'],
        font=dict(color=cfg['font_color'], family=cfg['font_family'], size=cfg['font_size_base']),
        title_font=dict(size=cfg['title_font_size'], color=cfg['title_font_color'], family=cfg['font_family']),
        colorway=cfg['colorway'],
        legend=dict(
            font=dict(size=cfg['legend_font_size'], color=cfg['font_color']),
            bgcolor=cfg['legend_bgcolor'],
            bordercolor=cfg['legend_bordercolor'],
            borderwidth=1
        ),
    )
    fig.update_xaxes(
        gridcolor=cfg['grid_color'],
        zerolinecolor=cfg['zeroline_color'],
        tickfont=dict(size=cfg['axis_tick_font_size'], color=cfg['axis_tick_font_color']),
        title_font=dict(size=cfg['axis_title_font_size'], color=cfg['axis_title_font_color'])
    )
    fig.update_yaxes(
        gridcolor=cfg['grid_color'],
        zerolinecolor=cfg['zeroline_color'],
        tickfont=dict(size=cfg['axis_tick_font_size'], color=cfg['axis_tick_font_color']),
        title_font=dict(size=cfg['axis_title_font_size'], color=cfg['axis_title_font_color'])
    )
    return fig

def save_figure_with_template(fig, filename, title):
    """使用自定义HTML模板保存图表"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(script_dir, "template.html")
    
    if not os.path.exists(template_path):
        # Create a minimal template if it doesn't exist, or handle error
        # For now, let's assume template.html exists and is correctly formatted
        print(f"Warning: HTML template file not found at {template_path}")
        # Fallback to simple HTML export if template is missing
        pio.write_html(fig, filename, auto_open=False)
        print(f"保存交互式图表到 (fallback): {filename}")
        return

    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()
    
    plot_json = fig.to_json()
    js_code = f"""
    var plotTitle = "{title}";
    var plotlyDiv = document.getElementById('plotly-chart');
    var plotData = {plot_json};
    Plotly.newPlot('plotly-chart', plotData.data, plotData.layout, {{
        responsive: true,
        displayModeBar: true,
        displaylogo: false,
        modeBarButtonsToAdd: ['hoverClosestGl2d', 'toggleSpikelines'],
        modeBarButtonsToRemove: ['toImage'],
    }});
    """
    html_content = template.replace('// PLOT_DATA将在生成HTML时被替换为实际的图表数据', js_code)
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"保存交互式图表到: {filename}")

# --- Helper Function 1: Price Chart with Signals (Single Product) ---
def _create_price_signal_plot_single(df_price_product, df_signal_product):
    fig = go.Figure()
    price_data = df_price_product.copy()
    signal_data = df_signal_product.copy()
    common_index = price_data.index.intersection(signal_data.index)
    price_data = price_data.loc[common_index]
    signal_data = signal_data.loc[common_index]
    fig.add_trace(go.Scatter(x=price_data.index, y=price_data, name="价格", line=dict(width=1.8)))
    buy_regions, sell_regions = [], []
    current_state, start_idx = 0, None
    for idx, val in signal_data.items():
        if pd.isna(val): continue
        if val == 1 and current_state != 1: start_idx, current_state = idx, 1
        elif val == -1 and current_state != -1: start_idx, current_state = idx, -1
        elif val == 0 and current_state != 0:
            if current_state == 1 and start_idx: buy_regions.append((start_idx, idx))
            elif current_state == -1 and start_idx: sell_regions.append((start_idx, idx))
            current_state, start_idx = 0, None
    if current_state != 0 and start_idx and len(price_data) > 0:
        end_idx = price_data.index[-1]
        if current_state == 1: buy_regions.append((start_idx, end_idx))
        elif current_state == -1: sell_regions.append((start_idx, end_idx))
    for r_start, r_end in buy_regions: fig.add_vrect(x0=r_start, x1=r_end, fillcolor="green", opacity=0.15, layer="below", line_width=0)
    for r_start, r_end in sell_regions: fig.add_vrect(x0=r_start, x1=r_end, fillcolor="red", opacity=0.15, layer="below", line_width=0)
    buy_points = signal_data[signal_data == 1].index
    sell_points = signal_data[signal_data == -1].index
    if not buy_points.empty: fig.add_trace(go.Scatter(x=buy_points, y=price_data.loc[buy_points], mode='markers', marker=dict(symbol='triangle-up', size=8, color='lime'), name="买入点"))
    if not sell_points.empty: fig.add_trace(go.Scatter(x=sell_points, y=price_data.loc[sell_points], mode='markers', marker=dict(symbol='triangle-down', size=8, color='magenta'), name="卖出点"))
    return fig

# --- Helper Function 2 (New): Turnover Chart --- 
def _create_turnover_plot_single(df_turnover_product_series):
    fig = go.Figure()
    if df_turnover_product_series is not None and not df_turnover_product_series.empty:
        turnover_data = pd.to_numeric(df_turnover_product_series, errors='coerce')
        fig.add_trace(go.Scatter(x=turnover_data.index, y=turnover_data, name="换手率/成交量", 
                                  line=dict(width=1.2, color=qlib_template_config['colorway'][4]), marker=dict(size=3)))
                                  # Using 5th color from colorway for distinction
    # If no data, fig remains empty, and an annotation will be added in the main function
    return fig

# --- Helper Function 3 (Original 2): Raw Signal Chart (Single Product) ---
def _create_raw_signal_plot_single(df_signal_product_series):
    fig = go.Figure()
    signal_data = pd.to_numeric(df_signal_product_series, errors='coerce')
    fig.add_trace(go.Scatter(x=signal_data.index, y=signal_data, name="策略信号值",
                              line=dict(width=1.5, shape='hv'), marker=dict(size=3)))
    return fig # Y-axis range will be set in combined plot

# --- Helper Function 4 (Original 3): Cumulative PnL Chart (Single Product) ---
def _create_cumulative_pnl_plot_single(df_cumulative_pnl_product, metrics_product):
    fig = go.Figure()
    for pnl_type in df_cumulative_pnl_product.columns:
        if 'pnl' in pnl_type.lower() or 'return' in pnl_type.lower(): 
            display_name = pnl_type.replace("_pnl", " PnL").replace("all", "总").replace("long", "多头").replace("short", "空头")
            if "return" in pnl_type.lower(): 
                 display_name = pnl_type.replace("return_", "").replace("all", "总").replace("long", "多头").replace("short", "空头") + " 回报"
            fig.add_trace(go.Scatter(x=df_cumulative_pnl_product.index, y=df_cumulative_pnl_product[pnl_type], name=display_name))

    textstr_lines = []
    if metrics_product:
        textstr_lines.append(f'总利润: {metrics_product.get("all_profit", 0):.2f}')
        textstr_lines.append(f'多头利润: {metrics_product.get("long_profit", 0):.2f}')
        textstr_lines.append(f'空头利润: {metrics_product.get("short_profit", 0):.2f}')
        textstr_lines.append(f'交易次数: {metrics_product.get("count_all", 0)} (多: {metrics_product.get("count_long",0)} 空: {metrics_product.get("count_short",0)})')
        textstr_lines.append(f'胜率: {metrics_product.get("all_win_rate", 0):.2%} (多: {metrics_product.get("long_win_rate",0):.2%} 空: {metrics_product.get("short_win_rate",0):.2%})')
        textstr_lines.append(f'盈亏比: {metrics_product.get("all_ProfitLoss_ratio", 0):.3f}')
    return fig, textstr_lines 

# --- Helper Function 5 (Original 4): Drawdown Chart (Single Product) ---
def _create_drawdown_plot_single(df_cumulative_pnl_product):
    fig = go.Figure()
    pnl_col_name = 'all_pnl' 
    if pnl_col_name not in df_cumulative_pnl_product.columns:
        pnl_cols = [col for col in df_cumulative_pnl_product.columns if 'pnl' in col.lower() or 'return' in col.lower()] 
        if not pnl_cols: return fig 
        all_pnl_cols = [col for col in pnl_cols if 'all' in col.lower()]
        if all_pnl_cols:
            pnl_col_name = all_pnl_cols[0]
        else:
            pnl_col_name = pnl_cols[0] 
        warnings.warn(f"计算回撤时首选'all_pnl'列未找到，使用 '{pnl_col_name}' 代替。")

    cumulative_pnl = df_cumulative_pnl_product[pnl_col_name]
    peak = cumulative_pnl.cummax()
    drawdown = peak - cumulative_pnl 
    
    fig.add_trace(go.Scatter(x=drawdown.index, y=-drawdown, name="回撤", # Drawdown as negative values
                              fill='tozeroy', line=dict(color=qlib_template_config['colorway'][3]), opacity=0.7))
    return fig

# --- Main Public Function for this Module ---
def generate_report_for_product(
    product_name, 
    df_price_product_series, 
    df_signal_product_series, 
    df_raw_signal_product_series, 
    df_turnover_product_series, # New: for turnover data
    df_cumulative_pnl_for_this_product, 
    metrics_for_this_product, 
    strategy_name_overall, 
    output_dir_for_product_charts=None, 
    initial_window_days=365
):
    content_fig1_price = _create_price_signal_plot_single(df_price_product_series, df_signal_product_series)
    content_fig2_turnover = _create_turnover_plot_single(df_turnover_product_series) # New turnover plot
    content_fig3_raw_signal = _create_raw_signal_plot_single(df_raw_signal_product_series) 
    content_fig4_pnl, pnl_metrics_text = _create_cumulative_pnl_plot_single(df_cumulative_pnl_for_this_product, metrics_for_this_product)
    content_fig5_drawdown = _create_drawdown_plot_single(df_cumulative_pnl_for_this_product)

    combined_fig = make_subplots(
        rows=5, cols=1, shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.30, 0.12, 0.10, 0.28, 0.20], # Adjusted for 5 rows
        subplot_titles=[
            f"{product_name} - 价格与交易点", 
            f"{product_name} - 换手率/成交量", # New
            f"{product_name} - 策略信号", 
            f"{product_name} - 累计收益", 
            f"{product_name} - 回撤情况"
        ]
    )
    combined_fig = apply_qlib_style(combined_fig)

    # Row 1: Price and Trade Signals
    for trace in content_fig1_price.data: combined_fig.add_trace(trace, row=1, col=1)
    for shape in content_fig1_price.layout.shapes: combined_fig.add_shape(shape, row=1, col=1)
    
    # Row 2: Turnover
    if content_fig2_turnover.data:
        for trace in content_fig2_turnover.data: combined_fig.add_trace(trace, row=2, col=1)
    else:
        combined_fig.add_annotation(text="无换手率数据", xref="x2 domain", yref="y2 domain", x=0.5, y=0.5, showarrow=False, row=2, col=1)

    # Row 3: Raw Strategy Signal
    for trace in content_fig3_raw_signal.data: combined_fig.add_trace(trace, row=3, col=1)
    
    # Row 4: Cumulative PnL and Metrics
    for trace in content_fig4_pnl.data: combined_fig.add_trace(trace, row=4, col=1)
    if pnl_metrics_text:
        combined_fig.add_annotation(xref='paper', yref='y4 domain', x=0.02, y=0.96, text="<br>".join(pnl_metrics_text),
                           showarrow=False, align="left", bgcolor="rgba(35, 39, 51, 0.88)",
                           bordercolor="rgba(100, 105, 120, 0.7)", borderwidth=1, borderpad=8,
                           font=dict(color="#E0E0E0", size=10, family=qlib_template_config.get('font_family', 'Arial')))

    # Row 5: Drawdown
    if content_fig5_drawdown.data:
        for trace in content_fig5_drawdown.data: combined_fig.add_trace(trace, row=5, col=1)
    else: # Should not happen if PnL data exists, but as a fallback
         combined_fig.add_annotation(text="无PNL数据无法计算回撤", xref="x5 domain", yref="y5 domain", x=0.5, y=0.5, showarrow=False, row=5, col=1)

    # X-axis configurations
    combined_fig.update_xaxes(showticklabels=False, row=1, col=1) 
    combined_fig.update_xaxes(showticklabels=False, row=2, col=1) 
    combined_fig.update_xaxes(showticklabels=False, row=3, col=1) 
    combined_fig.update_xaxes(showticklabels=False, row=4, col=1) 
    combined_fig.update_xaxes(
        showticklabels=True, 
        title_text="时间", 
        rangeslider=dict(visible=True, thickness=0.035, bgcolor="#1A1E28"), 
        row=5, col=1 # Rangeslider on the bottom chart (Drawdown)
    )
    
    if not df_price_product_series.empty:
        x_max_date = df_price_product_series.index.max()
        x_min_date = df_price_product_series.index.min()
        x_start_display = x_max_date - pd.Timedelta(days=initial_window_days)
        if x_start_display < x_min_date: x_start_display = x_min_date
        date_range = [x_start_display, x_max_date]
        for i in range(1, 6): # Apply to all 5 x-axes
            combined_fig.update_xaxes(range=date_range, row=i, col=1)
    elif not df_raw_signal_product_series.empty : 
         combined_fig.update_xaxes(rangeslider=dict(visible=True, thickness=0.035, bgcolor="#1A1E28"), row=5, col=1)

    # Y-axis titles and ranges
    combined_fig.update_yaxes(title_text="价格", fixedrange=False, row=1, col=1)
    combined_fig.update_yaxes(title_text="换手率/成交量", fixedrange=False, row=2, col=1)
    combined_fig.update_yaxes(title_text="信号值", range=[-1.5, 1.5], fixedrange=False, row=3, col=1) 
    combined_fig.update_yaxes(title_text="累计 PnL", fixedrange=False, row=4, col=1)
    combined_fig.update_yaxes(title_text="回撤", autorange="reversed", fixedrange=False, row=5, col=1) # Reversed for negative drawdown

    for ann_title in combined_fig.layout.annotations:
        if ann_title.text.startswith(product_name): 
            ann_title.font.size = qlib_template_config['subplot_title_font_size']
            ann_title.font.color = qlib_template_config['axis_title_font_color']

    combined_fig.update_layout(
        title_text=f"{strategy_name_overall} - {product_name} 综合报告",
        height=1500, width=1400, # Increased height for 5 plots
        hovermode='x unified', showlegend=True,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5, traceorder='normal'),
        margin=dict(t=100, b=60, l=75, r=50), dragmode='pan'
    )

    if output_dir_for_product_charts:
        os.makedirs(output_dir_for_product_charts, exist_ok=True)
        combined_html_path = os.path.join(output_dir_for_product_charts, f"{product_name}_combined_report.html")
        save_figure_with_template(combined_fig, combined_html_path, f"{strategy_name_overall} - {product_name} 综合报告")
    else:
        print(f"Displaying combined report for {product_name}...")
        iplot(combined_fig)
        
    return combined_fig