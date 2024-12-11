import json
import pandas as pd
import warnings
from datetime import datetime
from nfp_assistant import NFPAssistant
from shapely.geometry import Polygon
from show import PltFunc
from util.packing_util import get_inner_fit_rectangle
from util.polygon_util import (
    check_bound,
    check_right,
    check_top,
    poly_to_arr,
    scale_polygon,
    slide_poly,
    slide_to_point,
)


def warning_to_exception(message, category, filename, lineno, file=None, line=None):
    if "没有可行向量" in str(message):
        raise category(message)


# 可用于捕获异常
warnings.showwarning = warning_to_exception


class BottomLeftFill(object):
    def __init__(self, width, height, original_polygons, nfp_assistant, **kw):
        self.choose_nfp = False
        self.width = width
        self.height = height
        self.length = self.height
        self.contain_length = self.height
        self.polygons = original_polygons
        self.nfp_assistant = nfp_assistant
        self.container = Polygon([[0,0], [self.width,0], 
                                [self.width,self.height], 
                                [0,self.height]])

        print("Total Num:", len(original_polygons))
        if not self.placeFirstPoly():
            raise ValueError("Первый полигон не помещается в контейнер")
            
        for i in range(1, len(self.polygons)):
            print(f"##### Place the {i + 1}th shape #####")
            if not self.placePoly(i):
                raise ValueError(f"Не удалось разместить полигон {i+1}")
        self.getLength()

    def check_placement(self, poly):
        """Проверка корректности размещения полигона"""
        poly_shape = Polygon(poly)
        
        # Проверка границ контейнера с допуском
        TOLERANCE = 1e-10
        bounds = poly_shape.bounds  # (minx, miny, maxx, maxy)
        
        if (bounds[0] < -TOLERANCE or 
            bounds[1] < -TOLERANCE or 
            bounds[2] > self.width + TOLERANCE or 
            bounds[3] > self.height + TOLERANCE):
            return False
            
        # Проверка пересечений с другими полигонами
        for other_poly in self.polygons:
            if other_poly != poly:  # Не проверяем с самим собой
                other_shape = Polygon(other_poly)
                if poly_shape.intersects(other_shape):
                    intersection = poly_shape.intersection(other_shape)
                    if intersection.area > 1e-10:  # Допуск на численные погрешности
                        return False
        return True

    def find_valid_position(self, poly, start_x=0, start_y=0):
        """Поиск валидной позиции для полигона"""
        left_index, bottom_index, right_index, top_index = check_bound(poly)
        poly_width = poly[right_index][0] - poly[left_index][0]
        poly_height = poly[top_index][1] - poly[bottom_index][1]
        
        # Пробуем различные позиции
        for y in range(int(start_y), int(self.height - poly_height) + 1):
            for x in range(int(start_x), int(self.width - poly_width) + 1):
                test_poly = poly.copy()
                slide_poly(test_poly, x - poly[left_index][0], y - poly[bottom_index][1])
                if self.check_placement(test_poly):
                    slide_poly(poly, x - poly[left_index][0], y - poly[bottom_index][1])
                    return True
        return False

    def placeFirstPoly(self):
        """Размещение первого полигона с поиском позиции"""
        return self.find_valid_position(self.polygons[0])

    def placePoly(self, index):
        """Размещение полигона с проверками"""
        adjoin = self.polygons[index]
        ifr = get_inner_fit_rectangle(self.polygons[index], self.length, self.width)
        differ_region = Polygon(ifr)

        # Собираем все NFP
        nfp_regions = []
        for main_index in range(0, index):
            main = self.polygons[main_index]
            try:
                nfp = self.nfp_assistant.getDirectNFP(main, adjoin)
                nfp_poly = Polygon(nfp)
                nfp_regions.append(nfp_poly)
                differ_region = differ_region.difference(nfp_poly)
            except Exception as e:
                print(f"NFP failure for polygons {main_index} and {index}: {str(e)}")
                return False

        if differ_region.is_empty:
            print(f"Нет места для размещения полигона {index+1}")
            return False

        # Получаем все возможные точки размещения
        differ_points = poly_to_arr(differ_region)
        
        # Сортируем точки по возрастанию x и y
        differ_points.sort(key=lambda p: (p[0], p[1]))
        
        # Пробуем разные точки размещения
        for point in differ_points:
            refer_pt_index = check_top(adjoin)
            test_poly = self.polygons[index].copy()
            slide_to_point(test_poly, adjoin[refer_pt_index], point)
            
            if self.check_placement(test_poly):
                slide_to_point(self.polygons[index], adjoin[refer_pt_index], point)
                return True
                
        return False

    def getBottomLeft(self, poly):
        # 获得左底部点，优先左侧，有多个左侧选择下方
        bl = []  # bottom left的全部点
        _min = 999999
        # 选择最左侧的点
        for i, pt in enumerate(poly):
            pt_object = {"index": i, "x": pt[0], "y": pt[1]}
            target = pt[0]
            if target < _min:
                _min = target
                bl = [pt_object]
            elif target == _min:
                bl.append(pt_object)
        if len(bl) == 1:
            return bl[0]["index"]
        else:
            target = "y"
            _min = bl[0][target]
            one_pt = bl[0]
            for pt_index in range(1, len(bl)):
                if bl[pt_index][target] < _min:
                    one_pt = bl[pt_index]
                    _min = one_pt["y"]
            return one_pt["index"]

    def showAll(self):
        # for i in range(0,2):
        for i in range(0, len(self.polygons)):
            PltFunc.addPolygon(self.polygons[i])
        length = max(self.width, self.contain_length)
        PltFunc.showPlt(
            width=max(length, self.width), height=max(length, self.width), minus=100
        )

    def showPolys(self, polys):
        for i in range(0, len(polys) - 1):
            PltFunc.addPolygon(polys[i])
        PltFunc.addPolygonColor(polys[len(polys) - 1])
        length = max(self.width, self.contain_length)
        PltFunc.showPlt(
            width=max(length, self.width), height=max(length, self.width), minus=200
        )

    def getLength(self):
        _max = 0
        for i in range(0, len(self.polygons)):
            extreme_index = check_right(self.polygons[i])
            extreme = self.polygons[i][extreme_index][0]
            if extreme > _max:
                _max = extreme
        self.contain_length = _max
        # PltFunc.addLine([[0,self.contain_length],[self.width,self.contain_length]],color="blue")
        return _max


if __name__ == "__main__":
    df = pd.read_csv("data/test_rotated_sorted.csv")
    # Get polygons repeated by their corresponding num value
    polygons = []
    for _, row in df.iterrows():
        num = int(row["num"])
        polygon = json.loads(row["polygon"])
        for _ in range(num):
            polygons.append(polygon)
    scaled_polygons = [scale_polygon(polygon, 1) for polygon in polygons]
    start_time = datetime.now()
    nfp_assistant = NFPAssistant(
        polys=scaled_polygons, store_nfp=True, get_all_nfp=True, load_history=True
    )
    bfl = BottomLeftFill(
        width=1200,
        height=1000,
        original_polygons=scaled_polygons,
        nfp_assistant=nfp_assistant,
    )
    end_time = datetime.now()
    print("total time: ", end_time - start_time)
    bfl.showAll()
