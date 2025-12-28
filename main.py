import yaml
import sys
import os
import time
import argparse  # 引入参数解析库

from fgga import GGA,get_random_displacement_components,get_new_coordinates
import threading



def stdin_reader_thread():
    """后台线程：负责从标准输入读取二进制数据"""
    try:
        # 获取二进制读取器
        reader = sys.stdin.buffer
        while True:
            # 读取数据块（例如最大 1024 字节）
            # 注意：read 会阻塞直到有数据
            data = reader.read(1024)
            
            if not data:
                # 如果读取不到数据，说明管道已关闭
                break
            # process data??

    except Exception as e:
        print(f"\n[Thread Error] {e}", file=sys.stderr)

class LocationManager:
    def __init__(self, yaml_content):
        try:
            # 加载 YAML 数据
            self.raw_list = yaml.safe_load(yaml_content)
            if self.raw_list is None:
                self.raw_list = []

            self.locations = {}
            for item in self.raw_list:
                if 'name' in item:
                    key = str(item['name']).lower()
                    self.locations[key] = item
            
        except yaml.YAMLError as exc:
            print(f"YAML 解析错误: {exc}")
            self.locations = {}
        except Exception as e:
            print(f"加载错误: {e}")
            self.locations = {}

    def list_locations(self):
        """列出所有可用的地点名称 (返回原始大小写名称)"""
        return [data['name'] for data in self.locations.values()]

    def get_location_info(self, name):
        """根据名称获取经纬度和高度 (忽略大小写)"""
        if name is None:
            return None
            
        key = str(name).lower()
        
        if key in self.locations:
            data = self.locations[key]
            return {
                "lon": data['longitude'],
                "lat": data['latitude'],
                "h": data.get('height',1.0)
            }
        else:
            return None

# --- 主程序逻辑 ---

if __name__ == "__main__":
    # 定义命令行参数
    parser = argparse.ArgumentParser(description="GNSS GGA 模拟生成器")
    
    # 位置参数：location name (设为可选，因为 -l 模式下不需要)
    parser.add_argument("location_name", nargs="?", help="目标地点名称 (如 Paris)")
    
    # 可选参数
    parser.add_argument("-l", "--list", action="store_true", help="列出所有可用的 location name 并退出")
    parser.add_argument("-c", "--config", default="locations.yml", help="Location 配置文件路径 (默认: locations.yml)")
    parser.add_argument("-t", "--interval", type=float, default=1.0, help="输出/Sleep 间隔时间，单位秒 (默认: 1.0)")
    parser.add_argument("-s", "--speed", type=float, default=1.0, help="移动速度，单位 m/s (默认: 1.0)")

    args = parser.parse_args()
    # 1. 初始化管理器
    try:
        with open("locations.yml", "r", encoding="utf-8") as f:
            file_content = f.read()
            manager = LocationManager(file_content)
    except FileNotFoundError:
        print("错误：找不到 locations.yaml 文件")
        sys.exit(1)

    
    if args.list:
        locations = manager.list_locations()
        print("可用的地点:")
        for loc in locations:
            print(f" - {loc}")
        sys.exit(0)

    # 3. 校验位置参数 (如果不是 -l 模式，则必须提供 location_name)
    if not args.location_name:
        parser.error("必须指定 location name，或者使用 -l 查看可用列表。")

    # 4. 获取坐标信息
    location_data = manager.get_location_info(args.location_name)
    if not location_data:
        print(f"错误：地点 '{args.location_name}' 在配置文件中不存在。")
        sys.exit(1)

    lat = location_data['lat']
    lon = location_data['lon']
    h = location_data['h']
    
    # print(f"初始坐标: Lat={lat}, Lon={lon}, Height={h}")

    # 计算每一步的位移距离
    # 距离 (m) = 速度 (m/s) * 时间间隔 (s)
    step_distance = args.speed * args.interval
    
    # 获取位移分量 (根据原来的逻辑，这里生成一次方向后保持匀速直线运动)
    # 如果希望随机漫步，应将此行放入 while 循环内
    dx, dy = get_random_displacement_components(step_distance)
    
    n_lon = lon
    n_lat = lat
    g = GGA()

    reader_t = threading.Thread(target=stdin_reader_thread, daemon=True)
    reader_t.start()
    try:
        while True:
            # 更新坐标
            n_lon, n_lat = get_new_coordinates(n_lon, n_lat, dx, dy)
            
            g.lat = n_lat
            g.lon = n_lon
            # 注意：如果 GGA 类支持高度设置，建议也加上 g.h = h
            
            # 输出到 stdout 并flush
            sys.stdout.write(str(g))
            sys.stdout.write("\r\n")
            sys.stdout.flush()
            
            # 休眠指定间隔
            time.sleep(args.interval)
            
    except KeyboardInterrupt:
        sys.exit(0)