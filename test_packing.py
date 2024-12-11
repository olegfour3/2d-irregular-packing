import json
import time
import pandas as pd
from shapely.geometry import Polygon
from bottom_left_fill import BottomLeftFill
from nfp_assistant import NFPAssistant
from util.polygon_util import scale_polygon
import matplotlib.pyplot as plt
import numpy as np

def calculate_total_area(polygons):
    """Вычисление общей площади всех полигонов"""
    return sum(Polygon(poly).area for poly in polygons)

def calculate_container_efficiency(polygons, width, length):
    """Вычисление эффективности использования контейнера"""
    total_poly_area = calculate_total_area(polygons)
    container_area = width * length
    return (total_poly_area / container_area) * 100

def visualize_packing_result(polygons, width, length):
    """Визуализация только финального результата упаковки"""
    fig, ax = plt.subplots(figsize=(10, length/width * 10))
    
    # Отрисовка контейнера
    container = plt.Rectangle((0, 0), width, length, fill=False, color='black', linewidth=2)
    ax.add_patch(container)
    
    # Отрисовка полигонов разными цветами
    colors = plt.cm.rainbow(np.linspace(0, 1, len(polygons)))
    for poly, color in zip(polygons, colors):
        polygon = Polygon(poly)
        x, y = polygon.exterior.xy
        ax.fill(x, y, alpha=0.5, fc=color, ec='black')
    
    ax.set_xlim(-1, width + 1)
    ax.set_ylim(-1, length + 1)
    ax.set_aspect('equal')
    plt.title('Результат упаковки')
    plt.show()

def test_packing_algorithm():
    """Тестирование алгоритма упаковки с различными фигурами"""
    
    # Создаем набор разнообразных фигур
    test_polygons = [
        # Прямоугольники разных размеров
        [[0,0], [4,0], [4,2], [0,2]],
        [[0,0], [3,0], [3,1], [0,1]],
        
        # Треугольники
        [[0,0], [2,0], [1,2]],
        
        [[0,0], [2,0], [2,3], [0,3]],
        
        [[0,0], [3,0], [1.5,2.5]],
        
        
        # L-образные фигуры
        [[0,0], [2,0], [2,2], [1,2], [1,1], [0,1]],
        
        # Сложные многоугольники
        [[0,0], [2,0], [3,1], [2,2], [1,2], [0,1]],
        
        [[0,0], [3,0], [3,3], [2,3], [2,1], [0,1]],
        
        [[0,0], [4,0], [4,1], [3,1], [3,2], [1,2], [1,1], [0,1]],
        
        [[0,0], [4,0], [4,2], [0,2]],
        
        [[0,0], [3,0], [3,1], [0,1]],
        
        # Треугольники
        [[0,0], [2,0], [1,2]],
        
        [[0,0], [2,0], [2,3], [0,3]],
        
        [[0,0], [3,0], [1.5,2.5]]
    ]
    
    # Создаем тестовый набор с повторениями
    test_data = {
        'polygon': [json.dumps(p) for p in test_polygons],
        'num': [3, 4, 3, 5, 3, 2, 2, 2, 2, 3, 4, 3, 5, 3]  # Количество повторений каждой фигуры
    }
    df = pd.DataFrame(test_data)
    
    # Подготовка полигонов
    polygons = []
    for _, row in df.iterrows():
        num = int(row["num"])
        polygon = json.loads(row["polygon"])
        for _ in range(num):
            polygons.append(polygon)
    
    print(f"Всего фигур для упаковки: {len(polygons)}")
    
    # Масштабирование полигонов
    scaled_polygons = [scale_polygon(polygon, 1) for polygon in polygons]
    
    # Замер времени выполнения
    start_time = time.time()
    
    # Создание NFP Assistant и выполнение упаковки
    print("Создание NFP Assistant...")
    nfp_assistant = NFPAssistant(
        polys=scaled_polygons,
        store_nfp=True,
        get_all_nfp=True
    )
    
    # Параметры контейнера
    container_width = 25
    container_height = 18  # Фиксированная высота
    
    print("Выполнение упаковки...")
    try:
        bfl = BottomLeftFill(
            width=container_width,
            height=container_height,
            original_polygons=scaled_polygons,
            nfp_assistant=nfp_assistant
        )
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Расчет эффективности
        efficiency = calculate_container_efficiency(
            bfl.polygons, 
            container_width, 
            container_height  # Используем фиксированную высоту
        )
        
        # Вывод результатов
        print("\nРезультаты тестирования:")
        print(f"Время выполнения: {execution_time:.2f} секунд")
        print(f"Эффективность использования пространства: {efficiency:.2f}%")
        
        # Визуализация
        visualize_packing_result(bfl.polygons, container_width, container_height)
        
    except ValueError as e:
        print(f"\nОшибка упаковки: {str(e)}")
        print("Попробуйте увеличить размеры контейнера или уменьшить количество фигур")

if __name__ == '__main__':
    test_packing_algorithm() 