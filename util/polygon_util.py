import numpy as np

from constant.calculation_constants import BIAS
from shapely.geometry import LineString, mapping, Polygon


def almost_contain(line, point):
    """Улучшенная проверка вхождения точки в линию"""
    pt1 = [line[0][0], line[0][1]]
    pt2 = [line[1][0], line[1][1]]
    point = [point[0], point[1]]

    # Оптимизированная проверка для горизонтальных/вертикальных линий
    dx = abs(pt1[0] - pt2[0])
    dy = abs(pt1[1] - pt2[1])
    
    if dx < BIAS:  # Вертикальная линия
        if abs(point[0] - pt1[0]) > BIAS:
            return False
        return (point[1] - pt1[1]) * (point[1] - pt2[1]) <= 0
        
    if dy < BIAS:  # Горизонтальная линия 
        if abs(point[1] - pt1[1]) > BIAS:
            return False
        return (point[0] - pt1[0]) * (point[0] - pt2[0]) <= 0

    # Для наклонных линий используем улучшенный алгоритм
    if (abs(pt1[0] - point[0]) < BIAS or 
        abs(pt2[0] - point[0]) < BIAS or
        abs(pt1[0] - pt2[0]) < BIAS):
        return False

    arc1 = np.arctan2(line[0][1] - line[1][1], line[0][0] - line[1][0])
    arc2 = np.arctan2(point[1] - line[1][1], point[0] - line[1][0])
    
    if abs(arc1 - arc2) < BIAS:
        return ((point[1] - pt1[1]) * (pt2[1] - point[1]) > 0 and 
                (point[0] - pt1[0]) * (pt2[0] - point[0]) > 0)
    return False


def almost_equal(point1, point2):
    if abs(point1[0] - point2[0]) < BIAS and abs(point1[1] - point2[1]) < BIAS:
        return True
    else:
        return False


def check_bound(poly):
    return (
        check_left(poly),
        check_bottom(poly),
        check_right(poly),
        check_top(poly),
    )


def check_left(poly):
    polyP = Polygon(poly)
    min_x = polyP.bounds[0]
    for index, point in enumerate(poly):
        if point[0] == min_x:
            return index


def check_bottom(poly):
    polyP = Polygon(poly)
    min_y = polyP.bounds[1]
    for index, point in enumerate(poly):
        if point[1] == min_y:
            return index


def check_right(poly):
    polyP = Polygon(poly)
    max_x = polyP.bounds[2]
    for index, point in enumerate(poly):
        if point[0] == max_x:
            return index


def check_top(poly):
    polyP = Polygon(poly)
    max_y = polyP.bounds[3]
    for index, point in enumerate(poly):
        if point[1] == max_y:
            return index


def compute_inter_area(orginal_inter):
    """
    计算相交区域的面积
    """
    inter = mapping(orginal_inter)
    # 一个多边形
    if inter["type"] == "Polygon":
        if len(inter["coordinates"]) > 0:
            poly = inter["coordinates"][0]
            return Polygon(poly).area
        else:
            return 0
    if inter["type"] == "MultiPolygon":
        area = 0
        for _arr in inter["coordinates"]:
            poly = _arr[0]
            area = area + Polygon(poly).area
        return area

    if inter["type"] == "GeometryCollection":
        area = 0
        for _arr in inter["geometries"]:
            if _arr["type"] == "Polygon":
                poly = _arr["coordinates"][0]
                area = area + Polygon(poly).area
        return area
    return 0


def copy_poly(poly):
    new_poly = []
    for pt in poly:
        new_poly.append([pt[0], pt[1]])
    return new_poly


def cross_product(vec1, vec2):
    res = vec1[0] * vec2[1] - vec1[1] * vec2[0]
    # 最简单的计算
    if abs(res) < BIAS:
        return 0
    # 部分情况叉积很大但是仍然基本平行
    if abs(vec1[0]) > BIAS and abs(vec2[0]) > BIAS:
        if abs(vec1[1] / vec1[0] - vec2[1] / vec2[0]) < BIAS:
            return 0
    return res


def get_point(point):
    mapping_result = mapping(point)
    return [mapping_result["coordinates"][0], mapping_result["coordinates"][1]]


# 获得某个多边形的边
def get_poly_edges(poly):
    edges = []
    for index, point in enumerate(poly):
        if index < len(poly) - 1:
            edges.append([poly[index], poly[index + 1]])
        else:
            edges.append([poly[index], poly[0]])
    return edges


def get_slide(poly, x, y):
    """
    获得平移后的情况
    """
    new_vertex = []
    for point in poly:
        new_point = [point[0] + x, point[1] + y]
        new_vertex.append(new_point)
    return new_vertex


# 用于touching计算交点 可以与另一个交点计算函数合并
def intersection(line1, line2):
    # 如果可以直接计算出交点
    Line1 = LineString(line1)
    Line2 = LineString(line2)
    inter = Line1.intersection(Line2)
    if inter.is_empty == False:
        mapping_inter = mapping(inter)
        if mapping_inter["type"] == "LineString":
            inter_coor = mapping_inter["coordinates"][0]
        else:
            inter_coor = mapping_inter["coordinates"]
        return inter_coor
    # 对照所有顶点是否相同
    res = []
    for pt1 in line1:
        for pt2 in line2:
            if almost_equal(pt1, pt2) == True:
                # print("pt1,pt2:",pt1,pt2)
                res = pt1
    if res != []:
        return res

    # 计算是否存在almostContain
    for pt in line1:
        if almost_contain(line2, pt) == True:
            return pt
    for pt in line2:
        if almost_contain(line1, pt) == True:
            return pt
    return []


# 可能需要用近似计算进行封装！
def judge_position(edge1, edge2):
    x1 = edge1[1][0] - edge1[0][0]
    y1 = edge1[1][1] - edge1[0][1]
    x2 = edge2[1][0] - edge2[0][0]
    y2 = edge2[1][1] - edge2[0][1]
    res = x1 * y2 - x2 * y1
    right = False
    left = False
    parallel = False
    # print("res:",res)
    if res == 0:
        parallel = True
    elif res > 0:
        left = True
    else:
        right = True
    return right, left, parallel


def line_to_vec(edge):
    return [edge[1][0] - edge[0][0], edge[1][1] - edge[0][1]]


# 主要用于判断是否有直线重合 过于复杂需要重构
def new_line_inter(line1, line2):
    """Улучшенная проверка пересечения линий"""
    vec1 = line_to_vec(line1)
    vec2 = line_to_vec(line2)
    vec12_product = cross_product(vec1, vec2)
    Line1 = LineString(line1)
    Line2 = LineString(line2)
    
    # Быстрая проверка на параллельность
    if abs(vec12_product) < BIAS:
        return _check_parallel_lines(line1, line2, vec1, vec2, Line1, Line2)
        
    # Проверка пересечения непараллельных линий
    inter = Line1.intersection(Line2)
    if not inter.is_empty:
        return {"length": inter.length, "geom_type": inter.geom_type}
    return {"length": 0, "geom_type": None}

def _check_parallel_lines(line1, line2, vec1, vec2, Line1, Line2):
    """Проверка пересечения параллельных линий"""
    new_line1 = copy_poly(line1)
    new_line2 = copy_poly(line2)
    
    # Проверяем направление векторов
    if vec1[0] * vec2[0] < 0 or vec1[1] * vec2[1] < 0:
        new_line2 = reverse_line(new_line2)
        
    # Проверяем совпадение концов
    for p1 in new_line1:
        for p2 in new_line2:
            if almost_equal(p1, p2):
                return {"length": 0, "geom_type": "Point"}
                
    # Проверяем наложение
    if (_line_contains_point(new_line1, new_line2[0]) or
        _line_contains_point(new_line1, new_line2[1]) or
        _line_contains_point(new_line2, new_line1[0]) or
        _line_contains_point(new_line2, new_line1[1])):
        return {"length": min(Line1.length, Line2.length),
                "geom_type": "LineString"}
                
    return {"length": 0, "geom_type": None}

def _line_contains_point(line, point):
    """Проверка, содержится ли точка в линии"""
    # Проверяем, лежит ли точка на отрезке
    if almost_contain(line, point):
        return True
        
    # Дополнительная проверка для граничных случаев
    if almost_equal(line[0], point) or almost_equal(line[1], point):
        return True
        
    return False

def poly_to_arr(inter):
    res = mapping(inter)
    _arr = []
    if res["type"] == "MultiPolygon":
        for poly in res["coordinates"]:
            for point in poly[0]:
                _arr.append([point[0], point[1]])
    elif res["type"] == "GeometryCollection":
        for item in res["geometries"]:
            if item["type"] == "Polygon":
                for point in item["coordinates"][0]:
                    _arr.append([point[0], point[1]])
    else:
        if res["coordinates"][0][0] == res["coordinates"][0][-1]:
            for point in res["coordinates"][0][0:-1]:
                _arr.append([point[0], point[1]])
        else:
            for point in res["coordinates"][0]:
                _arr.append([point[0], point[1]])
    return _arr


def reverse_line(line):
    pt0 = line[0]
    pt1 = line[1]
    return [[pt1[0], pt1[1]], [pt0[0], pt0[1]]]


def scale_polygon(polygon, scale_factor):
    return [[vertex[0] * scale_factor, vertex[1] * scale_factor] for vertex in polygon]


def slide_poly(poly, x, y):
    for point in poly:
        point[0] = point[0] + x
        point[1] = point[1] + y


def slide_to_point(poly, pt1, pt2):
    slide_poly(poly, pt2[0] - pt1[0], pt2[1] - pt1[1])


def rotate_polygon(polygon, angle):
    """Поворот полигона на заданный угол"""
    # Находим центр полигона
    poly = Polygon(polygon)
    centroid = poly.centroid
    
    # Переносим в начало координат
    translated = [[p[0] - centroid.x, p[1] - centroid.y] for p in polygon]
    
    # Поворачиваем
    angle_rad = np.radians(angle)
    cos_a = np.cos(angle_rad)
    sin_a = np.sin(angle_rad)
    
    rotated = []
    for p in translated:
        x = p[0] * cos_a - p[1] * sin_a
        y = p[0] * sin_a + p[1] * cos_a
        rotated.append([x + centroid.x, y + centroid.y])
        
    return rotated
