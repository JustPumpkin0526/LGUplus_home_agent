import chardet
import configparser
# from shapely.geometry import Polygon, MultiPolygon
# from shapely.ops import unary_union
import matplotlib.pyplot as plt
# import geopandas as gpd

from _tools import *
from _tools.define import *

def load_config(config_path):
    config = configparser.ConfigParser()

    with open(config_path, 'r', encoding='utf-8') as configfile:
        config.read_file(configfile)
    
    config_dict = {}
    
    for section in config.sections():
        section_dict = {}
        for key, value in config.items(section):
            # 쉼표로 구분된 문자열을 리스트로 변환
            if ',' in value:
                section_dict[key] = [item.strip() for item in value.split(',')]
            else:
                section_dict[key] = value
        config_dict[section] = section_dict

    return config_dict

# 파일의 인코딩 형식을 반환
def detect_encoding(file_path):
    with open(file_path, 'rb') as f:
        raw_data = f.read()
    result = chardet.detect(raw_data)
    encoding = result['encoding']
    return encoding

# json_path로부터 json 파일을 읽어 반환
def load_json(json_path, encoding='utf-8'):
    with open(json_path, 'r', encoding=encoding) as json_file:
        data = json.load(json_file)

    return data

def save_json(json_path, json_data, encoding='utf-8', indent=4, ensure_ascii=False):
    with open(json_path, 'w', encoding=encoding) as json_file:
        json.dump(json_data, json_file, indent=indent, ensure_ascii=ensure_ascii)

def read_csv_file(file_path):
    encoding = detect_encoding(file_path)

    with open(file_path, 'r', newline='', encoding=encoding) as csvfile:
        csv_reader = csv.reader(csvfile)
        headers = next(csv_reader)  # 첫 번째 행을 헤더로 설정
        
        data_dict = []
        for row in csv_reader:
            row_dict = {}
            for idx, value in enumerate(row):
                # data_dict[headers[idx]].append(value)  # 각 헤더에 해당하는 값 리스트에 추가
                row_dict[headers[idx]] = value
            data_dict.append(row_dict)
                    
    return data_dict

def load_files_from_folder(folder_path):
    # 폴더 내 파일 이름들을 가져옵니다.
    return os.listdir(folder_path)

def load_txt(txt_path, encoding='utf-8'):
    lines = []
    with open(txt_path, 'r') as file:
        lines = file.readlines()
        # 줄 끝의 개행 문자를 제거하고 리스트에 저장
        lines = [line.strip() for line in lines]
    
    return lines

def save_txt(txt_path, txt_data, encoding='utf-8'):
    with open(txt_path, 'w', encoding=encoding) as file:
        for line in txt_data:
            file.write(line + "\n")

def load_bin(bin_path):
    with open(bin_path, 'rb') as file:
        datas = pickle.load(file)
    
    return datas

import struct
def load_w3(bin_path, dtype):
    w3 = []
    with open(bin_path, 'rb') as file:
        while True:
            data = file.read(4)
            if not data:
                break
            data = struct.unpack(dtype, data)
            w3.append(data)

    return w3

#폴더 내부 요소 전부 삭제
def delete_all_files(folderpath):
    if os.path.exists(folderpath):
        for file in os.scandir(folderpath):
            os.remove(file.path)
        return 'Remove All File'
    else:
        return 'Directory Not Found'

def get_subfolders(directory):
    # 디렉토리 내 항목 중 폴더만 필터링
    return [name for name in os.listdir(directory) if os.path.isdir(os.path.join(directory, name))]

def get_all_file_paths(root_folder, exts=None, recur=False):
    # exts가 None이거나 빈 리스트일 경우 모든 확장자 파일을 가져옴
    if exts is None:
        exts = []
    elif exts is str:
        exts = [exts]

    file_paths = []
    
    if recur == False:
        for filename in os.listdir(root_folder):
            file_path = os.path.join(root_folder, filename)
            if os.path.isfile(file_path):
                if not exts or any(filename.endswith(ext) for ext in exts):
                    file_paths.append(file_path)
    else:
        for dirpath, dirnames, filenames in os.walk(root_folder):
            for filename in filenames:
                if not exts or any(filename.endswith(ext) for ext in exts):
                    file_paths.append(os.path.join(dirpath, filename))
    
    return file_paths

def load_shp(file_path):
    # file_path = "C:/Users/User/Downloads/N3A_G0110000/N3A_G0110000.shp"
    gdf = gpd.read_file(file_path)
    if gdf.crs is not None:
        gdf = gdf.to_crs(epsg=4326)
    return gdf
    
# import rasterio
# from rasterio.transform import Affine
# from pyproj import Transformer

# def load_dem(dem_file):
#     """DEM 파일을 열고 필요한 데이터 로드"""
#     dem = rasterio.open(dem_file)
#     transformer = Transformer.from_crs("EPSG:4326", dem.crs)
#     dem_data = dem.read(1)  # DEM 데이터를 메모리에 로드
#     return dem, dem_data, transformer

def beopjeong_shp_parsing():
    aws_path = "./_result/api_datas/AWS 속한 특보구역 코드.json"
    aws_datas = fs.load_json(aws_path)

    file_path = "C:/Users/User/Downloads/N3A_G0110000/N3A_G0110000.shp" #dong
    # file_path = "C:/Users/User/Downloads/N3A_G0100000/N3A_G0100000.shp" #si
    gdf = fs.load_shp(file_path)

    print(gdf)
    exit()

    sigungu_datas = []
    aws_sigungu_pair_datas = []

    cnt = 0
    for index, row in gdf.iterrows():
        # if index > 100:
        #     break

        # print(f'{row["NAME"]} {row["BJCD"]} {row["SCLS"]} {row["DIVI"]}')
        # continue
            
        name = row['NAME']
        geometry = row['geometry']
        scls = row["SCLS"]

        if scls == "G0018113":
            cnt += 1
        
        # MultiPolygon인지 Polygon인지 확인 후 처리
        if isinstance(geometry, Polygon):
            polygons = [geometry]  # Polygon 객체를 리스트로 감싸기
        elif isinstance(geometry, MultiPolygon):
            polygons = geometry.geoms # MultiPolygon을 개별 Polygon으로 분해

        if len(polygons) > 1:
            print(name, len(polygons))
            polygons = MultiPolygon(polygons)
            polygons = unary_union(polygons.buffer(0.005))
            if isinstance(polygons, MultiPolygon):
                polygons = polygons.geoms
            else:
                polygons = [polygons]
        else:
            polygons = [polygons[0]]

        save_polygons = []
        for polygon in polygons:
            save_polygon = []
            for point in polygon.exterior.coords:
                save_polygon.append([point[0], point[1]])
            save_polygons.append(save_polygon)

        multi_polygon = MultiPolygon(polygons)
        
        sigungu_lon = float(multi_polygon.centroid.x)
        sigungu_lat = float(multi_polygon.centroid.y)
        
        sigungu_datas.append({"ufid":row["UFID"], "bjcd":row["BJCD"], "name":row["NAME"], "scls":row["SCLS"], "lon":sigungu_lon, "lat":sigungu_lat, "geom":save_polygons})
    
        si_lon = sigungu_lon
        si_lat = sigungu_lat

        min_aws = None
        min_dist = 9999999
        for aws in aws_datas:
            aws_lon = float(aws["LON"])
            aws_lat = float(aws["LAT"])
            dist = geo.haversine_distance(si_lat, si_lon, aws_lat, aws_lon)
            if dist < min_dist:
                min_dist = dist
                min_aws = aws

        aws_sigungu_pair_datas.append({"aws_stn":min_aws["STN_ID"], "bjcd":row["BJCD"], "scls":row["SCLS"]})

    print(cnt)

    # fs.save_json("./_result/sigungu_datas_new.json", sigungu_datas)
    
    # fs.save_json("./_result/AWS_법정동_pair_datas_new.json", aws_sigungu_pair_datas)