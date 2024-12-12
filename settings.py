from dataclasses import dataclass, asdict

# -*- coding: utf-8 -*-

# POPULATION_SIZE = 50  # 30 количество геномов ()
# MUTA_RATE = 15  # вероятность мутации (из-за random в методе GA.mutate())
# ROTATIONS = 4  # выбор вращения, 1: нет вращения
# # Единица MM (мм)
# SPACING = 6.3  # графический интервал между контурами
# RESULT_ROTATION_ANGLE = 90  # Повернуть весь получившийся результат на 90, 180, 270
# RESULT_OFFSET_X = 1380.00  # Если RESULT_ROTATION_ANGLE = 0, то эти значения не учитываются
# RESULT_OFFSET_Y = 0.0
#
# # разные размеры рабочей области
# BIN_HEIGHT = 1380
# BIN_WIDTH = 2580
# BIN_NORMAL = [[0, 0], [0, BIN_HEIGHT], [BIN_WIDTH, BIN_HEIGHT], [BIN_WIDTH, 0]]  # области
# BIN_CUT_BIG = [[0, 0], [0, 1570], [2500, 1570], [2500, 0]]  # Размер области для резки 1
# BIN_CUT_SMALL = [[0, 0], [0, 1200], [1500, 1200], [1500, 0]]  # Размер области для резки 2
#
#
#
# # Коэффициент масштабирования контуров для объекта SPLINE
# CONTOUR_SCALING = 10  # установите 1, если не надо масштабировать
# SPLIT_SPLINES = False  # когда в файле несколько объектов SPLINE (читать как один контур или несколько)
# SIMPLIFYING_POLYGONS = True  # упрощать полигоны до минимального количенства точек для увеличения быстродействия
#                              # В результате все равно будут исходные точки


@dataclass
class NestConfig:
    BIN_HEIGHT: int
    BIN_WIDTH: int
    BIN_NORMAL: list[list[int]]

    POPULATION_SIZE: int
    MUTA_RATE: int
    ROTATIONS: int
    GROUP_ROTATION: bool
    SPACING: float
    RESULT_ROTATION_ANGLE: int
    RESULT_OFFSET_X: float
    RESULT_OFFSET_Y: float

    CONTOUR_SCALING: float
    SPLIT_SPLINES: bool
    SIMPLIFYING_POLYGONS: bool
    SPLINE_FLATTENING_DISTANCE: int
    SPLINE_FLATTENING_SEGMENTS: int
    APPROX_EPSILON: float

    MAT_ACTIVE_HEIGHT: float
    MAT_LIFT_HEIGHT: float
    MAT_PRELIFT_HEIGHT: float
    USE_MARKER_SHAPES: bool
    MARKER_ACTIVE_HEIGHT: float
    MARKER_LIFT_HEIGHT: float
    MARKER_PRELIFT_HEIGHT: float

    def __init__(self, data: dict = None):
        self.POPULATION_SIZE = 25  # 30 количество геномов ()
        self.MUTA_RATE = 15  # вероятность мутации (из-за random в методе GA.mutate())
        self.ROTATIONS = 4  # выбор вращения, 1: нет вращения
        self.GROUP_ROTATION = False  # вращение происходит для всех объектов группы по outer_id

        # разные размеры рабочей области
        self.BIN_HEIGHT = 1380
        self.BIN_WIDTH = 2580

        # Единица MM (мм)
        self.SPACING = 6.3  # графический интервал между контурами
        self.RESULT_ROTATION_ANGLE = 90  # Повернуть весь получившийся результат на 90, 180, 270
        self.RESULT_OFFSET_X = float(self.BIN_HEIGHT)  # Если RESULT_ROTATION_ANGLE = 0, то эти значения не учитываются
        self.RESULT_OFFSET_Y = 0.0
        # self.RESULT_OFFSET_Y = float(self.BIN_WIDTH)

        # Коэффициент масштабирования контуров для объекта SPLINE
        self.CONTOUR_SCALING = 10  # 9.935 # установите 1, если не надо масштабировать
        self.SPLIT_SPLINES = False  # когда в файле несколько объектов SPLINE (читать как один контур или несколько)
        self.SIMPLIFYING_POLYGONS = True  # упрощать полигоны до минимального
        # количенства точек для увеличения быстродействия
        # В результате все равно будут исходные точки
        self.SPLINE_FLATTENING_DISTANCE = 1
        self.SPLINE_FLATTENING_SEGMENTS = 30
        self.APPROX_EPSILON = 0.02  # Коэффициент аппроксимации перед триангуляцией чтобы вписать лэйблы
                                    # которые рисуются маркером (после нестинга)

        # GCode
        self.MAT_ACTIVE_HEIGHT = -10.0  # активная высота, на которой происходит резка
        self.MAT_LIFT_HEIGHT = 20.0  # высота подъема для перемещения ножа
        self.MAT_PRELIFT_HEIGHT = 3.0  # высота предварительного подъема, чтобы достать нож из материала
        self.USE_MARKER_SHAPES = True
        self.MARKER_ACTIVE_HEIGHT = -0.5
        self.MARKER_LIFT_HEIGHT = 50.0
        self.MARKER_PRELIFT_HEIGHT = 3.0

        if data is not None:
            self.POPULATION_SIZE = data.get('POPULATION_SIZE', self.POPULATION_SIZE)
            self.MUTA_RATE = data.get('MUTA_RATE', self.MUTA_RATE)
            self.ROTATIONS = data.get('ROTATIONS', self.ROTATIONS)
            self.GROUP_ROTATION = data.get('GROUP_ROTATION', self.GROUP_ROTATION)
            self.SPACING = data.get('SPACING', self.SPACING)
            self.BIN_HEIGHT = data.get('BIN_HEIGHT', self.BIN_HEIGHT)
            self.BIN_WIDTH = data.get('BIN_WIDTH', self.BIN_WIDTH)
            self.RESULT_ROTATION_ANGLE = data.get('RESULT_ROTATION_ANGLE', self.RESULT_ROTATION_ANGLE)
            self.RESULT_OFFSET_X = float(self.BIN_HEIGHT)
            # self.RESULT_OFFSET_Y = float(self.BIN_WIDTH)
            self.CONTOUR_SCALING = data.get('CONTOUR_SCALING', self.CONTOUR_SCALING)
            self.SPLIT_SPLINES = data.get('SPLIT_SPLINES', self.SPLIT_SPLINES)
            self.SIMPLIFYING_POLYGONS = data.get('SIMPLIFYING_POLYGONS', self.SIMPLIFYING_POLYGONS)
            self.SPLINE_FLATTENING_DISTANCE = data.get('SPLINE_FLATTENING_DISTANCE', self.SPLINE_FLATTENING_DISTANCE)
            self.SPLINE_FLATTENING_SEGMENTS = data.get('SPLINE_FLATTENING_SEGMENTS', self.SPLINE_FLATTENING_SEGMENTS)
            self.APPROX_EPSILON = data.get('APPROX_EPSILON', self.APPROX_EPSILON)

            self.MAT_ACTIVE_HEIGHT = data.get('MAT_ACTIVE_HEIGHT', self.MAT_ACTIVE_HEIGHT)
            self.MAT_LIFT_HEIGHT = data.get('MAT_LIFT_HEIGHT', self.MAT_LIFT_HEIGHT)
            self.MAT_PRELIFT_HEIGHT = data.get('MAT_PRELIFT_HEIGHT', self.MAT_PRELIFT_HEIGHT)
            self.USE_MARKER_SHAPES = data.get('USE_MARKER_SHAPES', self.USE_MARKER_SHAPES)
            self.MARKER_ACTIVE_HEIGHT = data.get('MARKER_ACTIVE_HEIGHT', self.MARKER_ACTIVE_HEIGHT)
            self.MARKER_LIFT_HEIGHT = data.get('MARKER_LIFT_HEIGHT', self.MARKER_LIFT_HEIGHT)
            self.MARKER_PRELIFT_HEIGHT = data.get('MARKER_PRELIFT_HEIGHT', self.MARKER_PRELIFT_HEIGHT)


        self.BIN_NORMAL = [[0, 0],
                           [0, self.BIN_HEIGHT],
                           [self.BIN_WIDTH, self.BIN_HEIGHT],
                           [self.BIN_WIDTH, 0]]  # области
        self.BIN_CUT_BIG = [[0, 0],
                            [0, 1570],
                            [2500, 1570],
                            [2500, 0]]  # Размер области для резки 1
        self.BIN_CUT_SMALL = [[0, 0],
                              [0, 1200],
                              [1500, 1200],
                              [1500, 0]]  # Размер области для резки 2

    def asdict(self):
        return asdict(self)

    def __getitem__(self, key):
        return getattr(self, key)

    def set_param(self, key, value):
        param = self[key]
        if isinstance(param, bool):
            value = value.lower() == 'true'
        elif isinstance(param, float):
            value = float(value)
        elif isinstance(param, list):
            # Assuming the list contains lists of integers
            value = [[int(num) for num in sublist.split(',')] for sublist in value.split(';')]
        setattr(self, key, value)