import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import pandas as pd
import numpy as np
import matplotlib.dates as mdates

def plot_pnl_waterfall_3d(pnl_curves_dict, title="3D PnL Waterfall Plot", 
                          z_spacing=1.0, alpha=0.7, figsize=(15, 10),
                          colors=None, line_colors=None, line_width=1.5,
                          y_label="Cumulative PnL", z_label="Strategy/Run", x_label="Time",
                          base_pnl_value=0.0):
    """
    绘制多条收益曲线的3D瀑布图。

    参数:
    pnl_curves_dict (dict): 字典，键为曲线名称 (str)，值为 Pandas Series (累计收益，索引为 datetime)。
    title (str): 图表标题。
    z_spacing (float): 各个曲线在Z轴上的视觉间距。
    alpha (float): 多边形的透明度。
    figsize (tuple): 图表大小。
    colors (list or None): 每个瀑布层面的填充颜色列表。如果为 None，则使用默认颜色循环。
    line_colors (list or None): 每条P&L曲线顶部的线条颜色列表。如果为 None，则使用默认颜色循环或与填充色相同。
    line_width (float): P&L曲线顶部线条的宽度。
    y_label (str): Y轴标签。
    z_label (str): Z轴标签。
    x_label (str): X轴标签。
    base_pnl_value (float): PnL瀑布图的基线值。
    """
    if not pnl_curves_dict:
        print("No PnL curves data provided.")
        return

    fig = plt.figure(figsize=figsize)
    ax = fig.add_subplot(111, projection='3d')

    num_curves = len(pnl_curves_dict)
    
    # 准备颜色
    if colors is None:
        prop_cycle = plt.rcParams['axes.prop_cycle']
        default_colors = prop_cycle.by_key()['color']
        colors = [default_colors[i % len(default_colors)] for i in range(num_curves)]
    elif len(colors) < num_curves:
        colors = colors + [plt.cm.viridis(i / num_curves) for i in range(len(colors), num_curves)] # 补充颜色

    if line_colors is None:
        line_colors = colors # 默认线条颜色与填充色一致
    elif len(line_colors) < num_curves:
        line_colors = line_colors + [plt.cm.cool(i / num_curves) for i in range(len(line_colors), num_curves)]


    all_min_pnl = []
    all_max_pnl = []
    all_min_time_num = []
    all_max_time_num = []

    polygons_list = []
    z_positions = np.arange(num_curves) * z_spacing
    
    curve_names = list(pnl_curves_dict.keys())

    for i, curve_name in enumerate(curve_names):
        pnl_series = pnl_curves_dict[curve_name]
        if not isinstance(pnl_series, pd.Series) or pnl_series.empty:
            print(f"Warning: PnL data for '{curve_name}' is invalid or empty. Skipping.")
            continue

        # 确保索引是 datetime 类型并转换为 matplotlib 可用的数值格式
        if not isinstance(pnl_series.index, pd.DatetimeIndex):
            try:
                pnl_series.index = pd.to_datetime(pnl_series.index)
            except Exception as e:
                print(f"Warning: Could not convert index of PnL curve '{curve_name}' to datetime: {e}. Skipping.")
                continue
        
        time_num = mdates.date2num(pnl_series.index.to_pydatetime()) # 转换为matplotlib的日期数值
        pnl_values = pnl_series.values

        if len(time_num) < 2: # 需要至少两个点来画线或多边形
            print(f"Warning: PnL curve '{curve_name}' has less than 2 data points. Skipping.")
            continue
            
        all_min_pnl.append(np.min(pnl_values))
        all_max_pnl.append(np.max(pnl_values))
        all_min_time_num.append(np.min(time_num))
        all_max_time_num.append(np.max(time_num))

        # 创建多边形的顶点 (逆时针)
        # (time, pnl)
        # Vertices: (t0, base), (t0, pnl0), (t1, pnl1), ..., (tn, pnln), (tn, base)
        verts = []
        # 底边前点
        verts.append((time_num[0], base_pnl_value)) 
        # PnL曲线上的点
        for t, pnl in zip(time_num, pnl_values):
            verts.append((t, pnl))
        # 底边后点
        verts.append((time_num[-1], base_pnl_value))
        
        # 将2D顶点转换为3D，并添加到列表
        # Poly3DCollection 需要的是一个 (N, 3) 的顶点数组列表，每个数组代表一个多边形
        polygon_verts_3d = np.array([(x, y, z_positions[i]) for x, y in verts])
        polygons_list.append(polygon_verts_3d)
        
        # 绘制PnL曲线顶部的线条
        ax.plot(time_num, pnl_values, zs=z_positions[i], zdir='y', color=line_colors[i % len(line_colors)], linewidth=line_width, label=f'{curve_name} PnL')


    if not polygons_list:
        print("No valid PnL curves to plot.")
        plt.close(fig) # 关闭空图
        return

    # 创建 Poly3DCollection
    # facecolors 和 edgecolors 可以是一个列表，对应 polygons_list 中的每个多边形
    poly_collection = Poly3DCollection(polygons_list, 
                                       facecolors=colors[:len(polygons_list)], 
                                       edgecolors=line_colors[:len(polygons_list)], # 可以用不同颜色或更深的填充色
                                       linewidths=0.5, # 多边形边缘线宽
                                       alpha=alpha)
    ax.add_collection3d(poly_collection)

    # 设置坐标轴范围
    ax.set_xlim(min(all_min_time_num), max(all_max_time_num))
    ax.set_ylim(min(all_min_pnl) - abs(min(all_min_pnl)*0.1) , max(all_max_pnl) * 1.1) # Y轴是PnL
    ax.set_zlim(-z_spacing, max(z_positions) + z_spacing) # Z轴是策略/曲线的区分

    # 设置坐标轴标签
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label) # PnL 轴
    ax.set_zlabel(z_label) # 策略/曲线区分轴
    
    # 格式化X轴 (时间)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    fig.autofmt_xdate() # 自动调整日期标签以防重叠

    # 设置Z轴刻度和标签 (显示曲线名称)
    # Z轴是曲线的区分，Y轴才是 PnL
    ax.set_yticks(z_positions) # 注意这里用 set_yticks 因为我们将 PnL 曲线沿 plot 的 Y 方向展开
    ax.set_yticklabels(curve_names) # 对应 Y 方向的刻度标签
    
    # 调整Y轴 (PnL值) 和 Z轴 (策略区分) 的方向和标签
    # Matplotlib的3D图中，'y'通常是深度，'z'是高度。
    # 我们想要时间是X, PnL是Y(高度), 策略区分是Z(深度)
    # 如果默认行为不符合预期，可能需要交换 set_ylim/set_zlim 和 set_ylabel/set_zlabel
    # 以及 ax.plot 中的 zdir 参数。
    # 当前 ax.plot(..., zs=z_pos, zdir='y', ...) 表示曲线在 X-Z 平面上，并沿 Y 轴（深度）方向堆叠。
    # 为了让 PnL 成为 "高度" (通常的 Y 轴概念)，而策略成为 "深度" (Z 轴)，我们调整一下：
    # PnL 绘制在 Y 轴，策略沿 Z 轴分布，时间沿 X 轴。
    # 因此 Poly3DCollection 的顶点应该是 (time, strategy_z, pnl_value)
    # 或者 (time, pnl_value) 配上一个 z_offset。
    # 上面的 polygon_verts_3d = np.array([(x, y, z_positions[i]) for x, y in verts]) 
    # 假设 x=time, y=pnl, z_position[i] 是策略的深度。
    # plot(time, pnl, zs=z_pos, zdir='z') 会在 x-y 平面画线，沿 z 轴堆叠。这是更常见的。
    
    # *** 重构顶点和plot以符合常见3D坐标习惯 (X=时间, Y=PnL, Z=策略) ***
    # (上面的注释有点混乱，我们重新整理一下坐标轴对应关系)
    # X轴: 时间 (time_num)
    # Y轴: PnL值 (pnl_values)
    # Z轴: 策略/曲线的偏移量 (z_positions)

    # Poly3DCollection 的顶点应该是 [(x1,y1), (x2,y2), ...] for each polygon
    # 然后 add_collection3d 时，它会被放置在 Z=z_positions[i] 的平面上。
    # 不，Poly3DCollection的verts参数需要已经是3D的了。
    # verts = list of (N,3) arrays.
    # 所以，每个polygon的顶点必须是 (x,y,z)。
    # 对于我们的第 i 个 PnL 曲线：
    # time_num (X), pnl_values (Y), z_value = z_positions[i] (Z)
    # 多边形顶点: (time_val, pnl_val, z_value)
    
    # 再次确认 Poly3DCollection 的用法和 `verts` 的结构:
    # `verts` is a list of (N, D) arrays, where D is 2 or 3.
    # If D is 2, then `zs` must be provided. (This is for `PathPatch3D`)
    # For `Poly3DCollection`, `verts` should be a list of lists of (x, y, z) tuples, or (N, 3) arrays.
    # 我的实现 `polygon_verts_3d = np.array([(x, y, z_positions[i]) for x, y in verts])` 是正确的。
    
    # 清理一下坐标轴设置
    ax.set_xlim(min(all_min_time_num), max(all_max_time_num))
    ax.set_ylim(min(all_min_pnl) - abs(min(all_min_pnl)*0.1) if all_min_pnl else -1 , 
                max(all_max_pnl) * 1.1 if all_max_pnl else 1) # PnL 轴
    ax.set_zlim(min(z_positions) - z_spacing/2, max(z_positions) + z_spacing/2) # 策略区分轴

    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label) 
    ax.set_zlabel(z_label) 
    
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    for tick in ax.get_xticklabels(): # 旋转X轴标签
        tick.set_rotation(30)
        tick.set_ha('right')

    # 设置Z轴刻度和标签 (显示曲线名称)
    ax.set_zticks(z_positions)
    ax.set_zticklabels(curve_names, rotation=-15, va='center', ha='left') # 调整标签旋转和对齐

    # 视角调整
    ax.view_init(elev=25, azim=-135) # 调整仰角和方位角

    if title:
        plt.title(title, fontsize=16)
    
    # 添加图例 (针对 ax.plot 绘制的线条)
    # 由于 Poly3DCollection 本身不直接支持图例标签的简单方式，
    # 我们依赖 ax.plot 的标签，或者手动创建图例代理。
    # 当前的 ax.plot 带有 label，但它们可能被Poly3DCollection遮挡或不显示。
    # 一个简单的解决方法是，在Z轴标签旁边展示策略名，或者不显示曲线上的线条。
    # 另一个方法是创建代理艺术家 (proxy artists)
    
    # 为了简化，并且因为曲线名称已在Z轴上，我们可能不需要重复的图例。
    # 如果需要图例，可以如下创建：
    # proxies = [plt.Rectangle((0, 0), 1, 1, fc=colors[i % len(colors)]) for i in range(num_curves)]
    # ax.legend(proxies, curve_names, title="Strategies", loc='upper left', bbox_to_anchor=(1.05, 1))


    plt.tight_layout() # 调整布局以适应标签
    return fig, ax

if __name__ == '__main__':
    # 示例用法:
    # 创建一些示例 PnL 数据 (Pandas Series)
    dates1 = pd.to_datetime(pd.date_range(start='2023-01-01', periods=100, freq='D'))
    pnl1 = pd.Series(np.random.randn(100).cumsum() * 100, index=dates1)
    
    dates2 = pd.to_datetime(pd.date_range(start='2023-01-15', periods=80, freq='D'))
    pnl2 = pd.Series((np.random.randn(80).cumsum() + 5) * 120, index=dates2)
    
    dates3 = pd.to_datetime(pd.date_range(start='2023-02-01', periods=120, freq='D'))
    pnl3 = pd.Series((np.random.randn(120).cumsum() - 3) * 80, index=dates3)

    pnl_data_dict = {
        "Strategy Alpha": pnl1,
        "Strategy Beta (Optimized)": pnl2,
        "Benchmark Gamma": pnl3,
        "Empty Strategy": pd.Series(dtype=float), # 测试空Series
        "Short Strategy": pnl1[:1] # 测试点数过少的Series
    }

    fig, ax = plot_pnl_waterfall_3d(pnl_data_dict, title="Sample 3D PnL Waterfall", z_spacing=10)
    
    if fig: # 确保 fig 不是 None (例如所有数据都无效时)
        # 保存图表（可选）
        # output_dir = "./charts" 
        # os.makedirs(output_dir, exist_ok=True)
        # fig.savefig(os.path.join(output_dir, "pnl_waterfall_3d.png"), dpi=300)
        # print(f"3D Waterfall plot saved to {os.path.join(output_dir, 'pnl_waterfall_3d.png')}")
        plt.show() 