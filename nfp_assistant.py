import copy
import csv
import json
import pandas as pd
from nfp import NFP
from shapely.geometry import Polygon
from util.array_util import delete_redundancy, get_index_multi
from util.polygon_util import get_point, get_slide


class NFPAssistant(object):
    def __init__(self, polys, **kw):
        self.polys = delete_redundancy(copy.deepcopy(polys))
        self.area_list, self.first_vec_list, self.centroid_list = [], [], []  # 作为参考
        for poly in self.polys:
            P = Polygon(poly)
            self.centroid_list.append(get_point(P.centroid))
            self.area_list.append(int(P.area))
            self.first_vec_list.append(
                [poly[1][0] - poly[0][0], poly[1][1] - poly[0][1]]
            )
        self.nfp_list = [[0] * len(self.polys) for i in range(len(self.polys))]
        
        # Инициализация кэша NFP
        self._nfp_cache = {}
        
        self.load_history = False
        self.history_path = None
        self.history = None
        if "history_path" in kw:
            self.history_path = kw["history_path"]

        if "load_history" in kw:
            if kw["load_history"] == True:
                # 从内存中加载history 直接传递pandas的df对象 缩短I/O时间
                if "history" in kw:
                    self.history = kw["history"]
                self.load_history = True
                self.loadHistory()

        self.store_nfp = False
        if "store_nfp" in kw:
            if kw["store_nfp"] == True:
                self.store_nfp = True

        self.store_path = None
        if "store_path" in kw:
            self.store_path = kw["store_path"]

        if "get_all_nfp" in kw:
            if kw["get_all_nfp"] == True and self.load_history == False:
                self.getAllNFP()

    def loadHistory(self):
        if not self.history:
            if not self.history_path:
                path = "history/nfp.csv"
            else:
                path = self.history_path
            df = pd.read_csv(path, header=None)
        else:
            df = self.history
        for index in range(df.shape[0]):
            i = self.getPolyIndex(json.loads(df[0][index]))
            j = self.getPolyIndex(json.loads(df[1][index]))
            if i >= 0 and j >= 0:
                self.nfp_list[i][j] = json.loads(df[2][index])
        # print(self.nfp_list)

    # 获得一个形状的index
    def getPolyIndex(self, target):
        area = int(Polygon(target).area)
        first_vec = [target[1][0] - target[0][0], target[1][1] - target[0][1]]
        area_index = get_index_multi(area, self.area_list)
        if len(area_index) == 1:  # 只有一个的情况
            return area_index[0]
        else:
            vec_index = get_index_multi(first_vec, self.first_vec_list)
            index = [x for x in area_index if x in vec_index]
            if len(index) == 0:
                return -1
            return index[0]  # 一般情况就只有一个了

    # 获得所有的形状
    def getAllNFP(self):
        for i, poly1 in enumerate(self.polys):
            for j, poly2 in enumerate(self.polys):
                nfp_object = NFP(poly1, poly2)
                if nfp_object.error < 0:
                    print(f"Error happened in NFP calculation for poly {i} and {j}")
                nfp = nfp_object.nfp
                # NFP(poly1, poly2).showResult()
                self.nfp_list[i][j] = get_slide(
                    nfp, -self.centroid_list[i][0], -self.centroid_list[i][1]
                )
        if self.store_nfp == True:
            self.storeNFP()

    def storeNFP(self):
        if self.store_path == None:
            path = "history/nfp.csv"
        else:
            path = self.store_path
        with open(path, "a+") as csvfile:
            writer = csv.writer(csvfile)
            for i in range(len(self.polys)):
                for j in range(len(self.polys)):
                    writer.writerows(
                        [[self.polys[i], self.polys[j], self.nfp_list[i][j]]]
                    )

    # 输入形状获得NFP
    def getDirectNFP(self, poly1, poly2, **kw):
        # Добавляем кэширование на основе геометрических характеристик
        cache_key = self._get_cache_key(poly1, poly2)
        if cache_key in self._nfp_cache:
            return self._nfp_cache[cache_key]
        
        if "index" in kw:
            i = kw["index"][0]
            j = kw["index"][1]
            centroid = get_point(Polygon(self.polys[i]).centroid)
        else:
            i = self.getPolyIndex(poly1)
            j = self.getPolyIndex(poly2)
            centroid = get_point(Polygon(poly1).centroid)

        if self.nfp_list[i][j] == 0:
            # Добавляем проверку на симметричность NFP
            if i != j and self.nfp_list[j][i] != 0:
                nfp = self._get_symmetric_nfp(self.nfp_list[j][i])
            else:
                nfp = NFP(poly1, poly2).nfp
            
            self._nfp_cache[cache_key] = nfp
            
            if self.store_nfp:
                with open("history/nfp.csv", "a+") as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerows([[poly1, poly2, nfp]])
            return nfp
        else:
            return get_slide(self.nfp_list[i][j], centroid[0], centroid[1])

    def _get_cache_key(self, poly1, poly2):
        """Генерация ключа кэша на основе геометрических характеристик"""
        p1_area = Polygon(poly1).area
        p2_area = Polygon(poly2).area
        return f"{p1_area:.6f}_{p2_area:.6f}"

    def _get_symmetric_nfp(self, nfp):
        """Получение симметричного NFP"""
        return [[-p[0], -p[1]] for p in nfp]
