# coding=utf8
from settings import NestConfig
import ezdxf
import math


class DXFShapeFinder:
    def __init__(self, file_name: str, config: NestConfig):
        self.file_name = file_name
        self.dxf = None
        self.all_shapes = []
        self.new_polygon = {}
        self.spline_polygon = []
        self.first_spline = True
        self.config = config
        self.dxf_shape_utl = DXFShapeUtils(config=self.config)

    def input_polygon(self):
        datas = self.find_shape_from_dxf()

        shapes = []
        for i in range(0, len(datas)):
            shapes.append(datas[i])

        return shapes

    def find_shape_from_dxf(self):
        self.dxf = ezdxf.readfile(self.file_name)
        self.all_shapes = []
        self.new_polygon = {}
        self.spline_polygon = []
        self.first_spline = True

        # asd = [(e.dxftype(), e.dxf.hasattr("layer"), e) for e in self.dxf.entitydb.values() if e.dxftype() == 'SPLINE']
        for e in self.dxf.entities:
            # e in self.dxf.groups['TEST_TEST']
            if e.dxf.layer != 'main':
                continue

            if e.dxftype() == 'LINE':
                end_key = '{}x{}'.format(e.dxf.end[0], e.dxf.end[1])
                start_key = '{}x{}'.format(e.dxf.start[0], e.dxf.start[1])

                if end_key in self.new_polygon:
                    for points in self.new_polygon[end_key]:
                        points[0], points[1] = self.scaling_coordinates(points[0], points[1])
                    self.all_shapes.append(self.new_polygon[end_key])
                    self.new_polygon.pop(end_key)
                    continue

                if start_key in self.new_polygon:
                    self.all_shapes.append(self.new_polygon[start_key])
                    self.new_polygon.pop(start_key)
                    continue

                has_find = False
                for key, points in self.new_polygon.items():
                    if points[-1][0] == e.dxf.start[0] and points[-1][1] == e.dxf.start[1]:
                        self.new_polygon[key].append([e.dxf.end[0], e.dxf.end[1]])
                        has_find = True
                        break
                    if points[-1][0] == e.dxf.end[0] and points[-1][1] == e.dxf.end[1]:
                        self.new_polygon[key].append([e.dxf.start[0], e.dxf.start[1]])
                        has_find = True
                        break

                if not has_find:
                    self.new_polygon['{}x{}'.format(e.dxf.start[0], e.dxf.start[1])] = [
                        [e.dxf.start[0], e.dxf.start[1]], [e.dxf.end[0], e.dxf.end[1]]]

            elif e.dxftype() == 'SPLINE':
                if self.config.SPLIT_SPLINES:
                    self.spline_polygon = []
                first_spline_points = True
                bspline = e.construction_tool()
                xy_pts = [p.xy for p in bspline.flattening(distance=self.config.SPLINE_FLATTENING_DISTANCE,
                                                           segments=self.config.SPLINE_FLATTENING_SEGMENTS)]
                for x, y, _ in xy_pts:
                    if not self.config.SPLIT_SPLINES:
                        self.dxf_shape_utl.add_spline_dots_flag(self.first_spline,
                                                                first_spline_points,
                                                                [x, y],
                                                                self.spline_polygon)
                    first_spline_points = False
                    self.spline_polygon.append(self.dxf_shape_utl.scaling_coordinates(x, y))
                self.first_spline = False
                if self.config.SPLIT_SPLINES:
                    self.all_shapes.append(self.spline_polygon)

            elif e.dxftype() == 'LWPOLYLINE':
                if self.config.SPLIT_SPLINES:
                    self.spline_polygon = []
                first_spline_points = True
                xy_pts = e.get_points(format='xy')
                for x, y in xy_pts:
                    if not self.config.SPLIT_SPLINES:
                        self.dxf_shape_utl.add_spline_dots_flag(first_spline=self.first_spline,
                                                                first_spline_points=first_spline_points,
                                                                points=[x, y],
                                                                spline_polygon=self.spline_polygon)
                    first_spline_points = False
                    self.spline_polygon.append(self.dxf_shape_utl.scaling_coordinates(x, y))
                self.first_spline = False
                if self.config.SPLIT_SPLINES:
                    self.all_shapes.append(self.spline_polygon)

        if not self.config.SPLIT_SPLINES and len(self.spline_polygon):
            self.all_shapes.append(self.spline_polygon)

        return self.all_shapes


class DXFShapeUtils:
    config: NestConfig

    def __init__(self, config: NestConfig):
        self.config = config

    def scaling_coordinates(self, x, y):
        return [x * self.config.CONTOUR_SCALING, y * self.config.CONTOUR_SCALING]

    def add_spline_dots_flag(self, first_spline, first_spline_points, points, spline_polygon, use_scaling=True):
        if first_spline or not first_spline_points:
            return
        x = points[0]
        y = points[1]
        if use_scaling:
            spline_polygon.append(self.scaling_coordinates(x=x, y=y))
            spline_polygon.append(self.scaling_coordinates(x=x, y=y))
            spline_polygon.append(self.scaling_coordinates(x=x, y=y))
        else:
            spline_polygon.append([x, y])
            spline_polygon.append([x, y])
            spline_polygon.append([x, y])

    @staticmethod
    def find_flags_and_break_shapes(shapes):
        new_shapes = []

        for i, shape_points in enumerate(shapes):
            shape_points_length = len(shape_points)
            new_shape_points = []
            skip = 0
            for j, shape_point in enumerate(shape_points):
                if skip > 0:
                    skip -= 1
                    continue
                x, y = shape_point
                if j < shape_points_length - 5 and \
                        shape_points[j + 1][0] == x and \
                        shape_points[j + 1][1] == y and \
                        shape_points[j + 2][0] == x and \
                        shape_points[j + 2][1] == y and \
                        shape_points[j + 3][0] == x and \
                        shape_points[j + 3][1] == y:
                    new_shapes.append(new_shape_points)
                    new_shape_points = []
                    skip = 3
                    continue
                new_shape_points.append((x, y))
            new_shapes.append(new_shape_points)

        return new_shapes


if __name__ == '__main__':
    # s = find_shape_from_dxf('/input_data/T9.dxf')
    # print(s)
    # print(len(s))
    pass
