import re
import logging
import datetime


logger = logging.getLogger("NMEA_Check")

class GGA:
    def __init__(self, talker="GP", utc_time=None, lat=None, lon=None, quality=0, num_sats=0):
        """
        初始化 GGA 语句对象
        
        参数:
        talker (str): Talker ID, 默认为 "GP" (GPS). 也可以是 "GN" (多模GNSS) 等.
        utc_time (datetime.time or str): UTC 时间.
        lat (float): 纬度 (十进制, 如 39.908). 正数为北纬, 负数为南纬.
        lon (float): 经度 (十进制, 如 116.397). 正数为东经, 负数为西经.
        quality (int): 定位质量 (0=无效, 1=单点定位, 2=差分定位, 4=RTK固定解...).
        num_sats (int): 卫星数量.
        hdop (float): 水平精度因子.
        alt (float): 海拔高度 (米).
        """
        self.talker = talker
        self.utc_time = utc_time
        self.lat = lat
        self.lon = lon
        self.quality = quality
        self.num_sats = num_sats
        # 其他字段暂时设空
        self.hdop = ""
        self.alt = ""
        self.geo_sep = ""    # 大地水准面分离度
        self.age_diff = ""   # 差分数据龄期
        self.ref_id = ""     # 差分基站ID

    def _decimal_to_nmea_lat(self, lat):
        """内部函数：将十进制纬度转换为 NMEA 格式 (DDMM.MMMM)"""
        if lat is None: return "", ""
        
        direction = 'N' if lat >= 0 else 'S'
        abs_lat = abs(lat)
        degrees = int(abs_lat)
        minutes = (abs_lat - degrees) * 60
        # 格式化: 2位度数 + 2位整数分 + 小数分
        nmea_val = f"{degrees:02d}{minutes:09.6f}" # 09.6f 保证分钟显示足够的精度
        return nmea_val, direction

    def _decimal_to_nmea_lon(self, lon):
        """内部函数：将十进制经度转换为 NMEA 格式 (DDDMM.MMMM)"""
        if lon is None: return "", ""
        
        direction = 'E' if lon >= 0 else 'W'
        abs_lon = abs(lon)
        degrees = int(abs_lon)
        minutes = (abs_lon - degrees) * 60
        # 格式化: 3位度数 + 2位整数分 + 小数分
        nmea_val = f"{degrees:03d}{minutes:09.6f}"
        return nmea_val, direction

    def _format_time(self):
        """格式化时间为 hhmmss.ss"""
        if self.utc_time is None:
            return  datetime.datetime.now().time().strftime("%H%M%S.%f")[:9] # 保留两位毫秒
        if isinstance(self.utc_time, (datetime.time, datetime.datetime)):
            return self.utc_time.strftime("%H%M%S.%f")[:9] # 保留两位毫秒
        return str(self.utc_time)

    def __str__(self):
        """生成最终的 NMEA 字符串"""
        
        # 1. 准备各个字段的数据
        time_str = self._format_time()
        lat_str, ns = self._decimal_to_nmea_lat(self.lat)
        lon_str, ew = self._decimal_to_nmea_lon(self.lon)
        
        # 2. 拼接数据体 (注意: 即使数据为空, 逗号也不能少)
        # 格式: ID,Time,Lat,NS,Lon,EW,Quality,NumSV,HDOP,Alt,M,Sep,M,Age,RefID
        # 头部 "$" 不参与校验和计算
        payload = f"{self.talker}GGA,{time_str},{lat_str},{ns},{lon_str},{ew}," \
                  f"{self.quality},{self.num_sats:02d},{self.hdop},{self.alt},M," \
                  f"{self.geo_sep},M,{self.age_diff},{self.ref_id}"
        
        # 3. 计算校验和
        cs = calculate_nmea_checksum(payload)
        
        # 4. 返回完整语句
        return f"${payload}*{cs}"

def calculate_nmea_checksum(sentence):
    """
    Calculates the 2-digit hexadecimal checksum for an NMEA string.
    """
    if sentence.startswith('$'):
        sentence = sentence[1:]
    if '*' in sentence:
        sentence = sentence.split('*')[0]

    checksum = 0
    for char in sentence:
        checksum ^= ord(char)

    return hex(checksum)[2:].upper().zfill(2)

def validate_gga_message(sentence):
    """
    Validates a GGA message.
    Logs specific failure reasons to the logger.
    Returns: bool
    """
    
    sentence = sentence.strip()

    # --- LEVEL 1: Basic Integrity ---
    if not sentence.startswith('$'):
        logger.warning(f"Format Error: Message must start with '$'. Input: {sentence[:10]}...")
        return False
        
    if '*' not in sentence:
        logger.warning("Format Error: Message missing checksum delimiter '*'.")
        return False

    try:
        raw_content, provided_checksum = sentence.split('*')
    except ValueError:
        logger.warning("Format Error: Message contains multiple asterisks or is malformed.")
        return False

    # Verify Checksum
    calculated = calculate_nmea_checksum(raw_content)
    if calculated != provided_checksum.upper():
        logger.warning(f"Checksum Mismatch: Calculated '{calculated}', Provided '{provided_checksum}'.")
        return False

    # --- LEVEL 2: Structure (Field Counts) ---
    content_body = raw_content[1:] # Remove '$'
    fields = content_body.split(',')

    # GGA must have exactly 15 fields
    if len(fields) != 15:
        logger.warning(f"Structure Error: Expected 15 fields, found {len(fields)}.")
        return False

    # --- LEVEL 3: Content Format (Regex) ---
    
    # Field 0: Talker ID
    if not fields[0].endswith('GGA'):
        logger.warning(f"Type Error: Sentence ID '{fields[0]}' is not GGA.")
        return False

    # Field 1: Time (HHMMSS.ss)
    if fields[1] and not re.match(r'^\d{6}(\.\d+)?$', fields[1]):
        logger.warning(f"Data Error: Invalid UTC Time format '{fields[1]}'.")
        return False

    # Field 2: Latitude (DDMM.MMMM)
    if fields[2] and not re.match(r'^\d{4}\.\d+$', fields[2]):
        logger.warning(f"Data Error: Invalid Latitude format '{fields[2]}'. Expected DDMM.MMMM.")
        return False

    # Field 3: N/S
    if fields[3] and fields[3] not in ('N', 'S'):
        logger.warning(f"Data Error: Invalid Latitude Direction '{fields[3]}'.")
        return False

    # Field 4: Longitude (DDDMM.MMMM)
    if fields[4] and not re.match(r'^\d{5}\.\d+$', fields[4]):
        logger.warning(f"Data Error: Invalid Longitude format '{fields[4]}'. Expected DDDMM.MMMM.")
        return False

    # Field 5: E/W
    if fields[5] and fields[5] not in ('E', 'W'):
        logger.warning(f"Data Error: Invalid Longitude Direction '{fields[5]}'.")
        return False

    # Field 6: Fix Quality (0-8)
    if not re.match(r'^[0-8]$', fields[6]):
        logger.warning(f"Data Error: Invalid Fix Quality '{fields[6]}'.")
        return False

    # Field 7: Satellites
    if fields[7] and not fields[7].isdigit():
        logger.warning(f"Data Error: Invalid Satellite count '{fields[7]}'.")
        return False

    # Field 8: HDOP
    if fields[8] and not re.match(r'^\d+(\.\d+)?$', fields[8]):
        logger.warning(f"Data Error: Invalid HDOP '{fields[8]}'.")
        return False

    # Field 9 & 10: Altitude + Unit
    if fields[9] and not re.match(r'^-?\d+(\.\d+)?$', fields[9]):
        logger.warning(f"Data Error: Invalid Altitude '{fields[9]}'.")
        return False
    if fields[9] and fields[10] != 'M':
        logger.warning(f"Data Error: Invalid Altitude Unit '{fields[10]}'. Expected 'M'.")
        return False

    # Field 11 & 12: Geoid + Unit
    if fields[11] and not re.match(r'^-?\d+(\.\d+)?$', fields[11]):
        logger.warning(f"Data Error: Invalid Geoid Separation '{fields[11]}'.")
        return False
    if fields[11] and fields[12] != 'M':
        logger.warning(f"Data Error: Invalid Geoid Unit '{fields[12]}'. Expected 'M'.")
        return False

    # Field 13: Age of DGPS
    if fields[13] and not re.match(r'^\d+(\.\d+)?$', fields[13]):
        logger.warning(f"Data Error: Invalid DGPS Age '{fields[13]}'.")
        return False

    # Field 14: Station ID
    if fields[14] and not fields[14].isdigit():
        logger.warning(f"Data Error: Invalid DGPS Station ID '{fields[14]}'.")
        return False

    # Success
    return True


# --- 测试示例 ---
if __name__ == "__main__":


    # Configure logging to show messages in the console
    logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')

    print("--- Test 1: Valid Message ---")
    valid_msg = "$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47"
    print(f"Result: {validate_gga_message(valid_msg)}\n")

    print("--- Test 2: Invalid Checksum ---")
    bad_chk = "$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*99"
    print(f"Result: {validate_gga_message(bad_chk)}\n")

    print("--- Test 3: Bad Latitude Format (Typo) ---")
    # Latitude here is 48.038 (decimal degrees style) instead of 4807.038 (NMEA style)
    bad_lat = "$GPGGA,123519,48.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*40"
    print(f"Result: {validate_gga_message(bad_lat)}\n")

    print("--- Test 4: Missing Fields ---")
    # Removed Geoid data completely
    bad_struct = "$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,,*1F"
    print(f"Result: {validate_gga_message(bad_struct)}\n")

    # 场景1: 创建一个空的 GGA (类似你的初始示例)
    empty_gga = GGA()
    print(f"空GGA: {empty_gga}") 
    # 输出类似于: $GPGGA,,,,,,0,00,0.0,0.0,M,,M,,*66
    print(f"Result: {validate_gga_message(str(empty_gga))}\n")

    # 场景2: 填入真实数据 (北京坐标)
    # 假设这是通过刚才的函数算出来的新坐标
    current_time = datetime.datetime.now().time()
    bj_lat = 39.908
    bj_lon = 116.397
    
    gga_msg = GGA(
        talker="GP", 
        utc_time=current_time, 
        lat=bj_lat, 
        lon=bj_lon, 
        quality=1,      # 1=GPS Fix
        num_sats=8,     # 8颗卫星
    )
    
    print(f"完整GGA: {gga_msg}")
    print(f"Result: {validate_gga_message(str(gga_msg))}\n")
    
    # 场景3: 动态更新位置
    gga_msg.lat = -33.8688 # 悉尼 (南纬)
    gga_msg.lon = 151.2093 # 悉尼 (东经)
    gga_msg.utc_time = "120000.00" # 手动设置时间字符串
    
    print(f"更新后: {gga_msg}")
    print(f"Result: {validate_gga_message(str(gga_msg))}\n")