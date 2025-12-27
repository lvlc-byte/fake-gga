import yaml
import sys
import os
import time

from fgga import GGA,get_random_displacement_components,get_new_coordinates

# 为了方便演示，这里直接将YAML内容作为字符串放入代码中
# 在实际应用中，你通常会使用 open('config.yaml', 'r') 来读取文件
yaml_data = """
- { name: Paris, longitude: 2.2945, latitude: 48.8584, height: 35.0 }
- { name: Toulouse, longitude: 1.4808, latitude: 43.5606, height: 146.0 }
- { name: StMichel, longitude: -1.5115, latitude: 48.6360, height: 52.0 }
- { name: Nice, longitude: 7.2148, latitude: 43.6598, height: 4.0 }
- { name: Marseille, longitude: 5.3560, latitude: 43.3390, height: 5.0 }
- { name: Berlin, longitude: 13.3777, latitude: 52.5163, height: 34.0 }
- { name: Darmstadt, longitude: 8.6225, latitude: 49.8708, height: 144.0 }
- { name: Munich, longitude: 11.7861, latitude: 48.3537, height: 453.0 }
- { name: Hamburg, longitude: 9.9400, latitude: 53.5430, height: 10.0 }
- { name: Zugspitze, longitude: 10.9850, latitude: 47.4210, height: 2962.0 }
"""

class LocationManager:
    def __init__(self, yaml_content):
        """初始化管理器，解析YAML并建立查找表"""
        try:
            # 加载 YAML 数据
            self.raw_list = yaml.safe_load(yaml_content)
            
            # 将列表转换为字典，key为 name，方便快速查找
            # 格式: {'Paris': {'name': 'Paris', 'longitude': ...}, ...}
            self.locations = {item['name']: item for item in self.raw_list}
            
        except yaml.YAMLError as exc:
            self.locations = {}

    def list_locations(self):
        """列出所有可用的地点名称"""
        return list(self.locations.keys())

    def get_location_info(self, name):
        """根据名称获取经纬度和高度"""
        if name in self.locations:
            data = self.locations[name]
            return {
                "lon": data['longitude'],
                "lat": data['latitude'],
                "h": data['height']
            }
        else:
            return None

# --- 主程序逻辑 ---

if __name__ == "__main__":
    # 1. 初始化管理器
    try:
        with open("locations.yml", "r", encoding="utf-8") as f:
            file_content = f.read()
            manager = LocationManager(file_content)
            # 后续逻辑同上...
    except FileNotFoundError:
        print("错误：找不到 locations.yaml 文件")

        # 2. 列出所有地点
        print("\n--- 可用地点列表 ---")
        all_names = manager.list_locations()
        print(", ".join(all_names))
        print("-" * 30)

            
    # 4. 模拟 GNSS 应用中的坐标提取
    location_data = manager.get_location_info("Paris")
    if not location_data:
        sys.exit(1)
        # 这里模拟传给 GNSS 算法的变量
    lat = location_data['lat']
    lon = location_data['lon']
    h = location_data['h']
    gnss_input = (lat, lon, h)
    #print(f"发送到接收机算法的元组: {gnss_input}")

    dx,dy = get_random_displacement_components(1)
    n_lon = lon
    n_lat = lat
    g = GGA()
    while True:
        n_lon, n_lat = get_new_coordinates(n_lon, n_lat, dx, dy)
        g.lat = n_lat
        g.lon = n_lon
        print(g)
        time.sleep(1)