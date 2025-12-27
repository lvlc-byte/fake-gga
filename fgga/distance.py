import math
import random

def get_new_coordinates(lon, lat, dx, dy):
    """
    根据给定的经纬度和移动距离（米），计算新的经纬度。
    
    参数:
    lon (float): 原始经度（度）
    lat (float): 原始纬度（度）
    dx (float): 东西方向移动距离（米），东为正(+)，西为负(-)
    dy (float): 南北方向移动距离（米），北为正(+)，南为负(-)
    
    返回:
    (float, float): 新的 (经度, 纬度)
    """
    
    # 地球半径，单位：米 (使用 WGS-84 椭球体赤道半径)
    earth_radius = 6378137.0
    
    # 1. 计算纬度的变化
    # 纬度每度的距离相对固定（约111公里），直接用弧长公式：L = R * θ
    # 变换为：θ (弧度) = dy / R
    d_lat_rad = dy / earth_radius
    new_lat = lat + math.degrees(d_lat_rad)
    
    # 2. 计算经度的变化
    # 经度每度的距离随纬度变化而变化（赤道最长，极点为0）
    # 经度圈半径 r = R * cos(纬度)
    # 变换为：θ (弧度) = dx / (R * cos(纬度))
    avg_lat_rad = math.radians(lat)
    d_lon_rad = dx / (earth_radius * math.cos(avg_lat_rad))
    new_lon = lon + math.degrees(d_lon_rad)
    
    return new_lon, new_lat


def get_random_displacement_components(distance):
    """
    输入直线绝对距离，输出随机的东西(dx)和南北(dy)位移。
    保证 sqrt(dx^2 + dy^2) == distance。
    
    参数:
    distance (float): 直线距离 (必须 >= 0)
    
    返回:
    (float, float): (dx, dy)，正负号随机
    """
    if distance < 0:
        raise ValueError("距离不能为负数")

    # 1. 生成一个 0 到 360 度 (0 到 2π 弧度) 之间的随机角度
    # 这个角度决定了方向，从而随机决定了 dx 和 dy 的正负号
    angle_rad = random.uniform(0, 2 * math.pi)
    
    # 2. 根据三角函数分解距离
    # cos 在 0-90°(第一象限)为正，90-180°(第二象限)为负...以此类推，自动处理正负
    dx = distance * math.cos(angle_rad)
    dy = distance * math.sin(angle_rad)
    
    return dx, dy

# --- 测试代码 ---
if __name__ == "__main__":
        # 示例：北京附近
    original_lon = 117.345
    original_lat = 38.123
    
    # 向东移动 1000 米，向北移动 500 米
    move_x = 1000  
    move_y = 500
    
    n_lon, n_lat = get_new_coordinates(original_lon, original_lat, move_x, move_y)
    
    print(f"原坐标: ({original_lon}, {original_lat})")
    print(f"移动后: ({n_lon:.6f}, {n_lat:.6f})")
    print(f"变化值: 经度 {n_lon - original_lon:.6f}, 纬度 {n_lat - original_lat:.6f}")
    dist = 100.0  # 假设移动 100 米
    
    print(f"设定直线距离: {dist}")
    
    # 模拟 5 次随机生成
    for i in range(5):
        dx, dy = get_random_displacement_components(dist)
        
        # 验证计算结果
        calculated_dist = math.sqrt(dx**2 + dy**2)
        direction_str = ""
        direction_str += "东" if dx > 0 else "西"
        direction_str += "北" if dy > 0 else "南"
        
        print(f"第 {i+1} 次: dx={dx:7.2f}, dy={dy:7.2f} | 校验距离: {calculated_dist:.2f} | 方向: {direction_str}")

        n_lon, n_lat = get_new_coordinates(original_lon, original_lat, dx, dy)
        print(f"移动后: ({n_lon:.6f}, {n_lat:.6f}); 变化值: 经度 {n_lon - original_lon:.6f}, 纬度 {n_lat - original_lat:.6f}")
    
    print("====")
    dx, dy = get_random_displacement_components(dist)
    n_lon = original_lon
    n_lat = original_lat
    for i in range(10):
        n_lon, n_lat = get_new_coordinates(n_lon, n_lat, dx, dy)
        print(f"移动后: ({n_lon:.6f}, {n_lat:.6f}); 变化值: 经度 {n_lon - original_lon:.6f}, 纬度 {n_lat - original_lat:.6f}")

