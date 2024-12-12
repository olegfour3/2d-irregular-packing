import os
from settings import NestConfig
from input_utls import DXFShapeFinder
from bottom_left_fill import BottomLeftFill
from nfp_assistant import NFPAssistant
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
from shapely.geometry import Polygon
from typing import List, Dict, Tuple

def visualize_packing_result(polygons, width, length, title="Результат упаковки"):
    """Визуализация результата упаковки"""
    fig, ax = plt.subplots(figsize=(12, length/width * 12))
    
    # Отрисовка контейнера
    container = plt.Rectangle((0, 0), width, length, fill=False, color='black', linewidth=2)
    ax.add_patch(container)
    
    # Отрисовка полигонов разными цветами с метками файлов
    colors = plt.cm.rainbow(np.linspace(0, 1, len(polygons)))
    for (poly, source_file), color in zip(polygons, colors):
        polygon = Polygon(poly)
        x, y = polygon.exterior.xy
        ax.fill(x, y, alpha=0.5, fc=color, ec='black', label=source_file)
    
    ax.set_xlim(-10, width + 10)
    ax.set_ylim(-10, length + 10)
    ax.set_aspect('equal')
    plt.title(title)
    plt.grid(True)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.show()

def calculate_efficiency(polygons: List[Tuple[List, str]], width: float, height: float) -> float:
    """Расчет эффективности упаковки"""
    total_poly_area = sum(Polygon(poly).area for poly, _ in polygons)
    container_area = width * height
    return (total_poly_area / container_area) * 100

def load_all_dxf_files(dxf_folder: str, config: NestConfig) -> List[Tuple[List, str]]:
    """Загрузка всех фигур из всех DXF файлов"""
    all_polygons = []
    
    print("\nЗагрузка DXF файлов:")
    for file_name in os.listdir(dxf_folder):
        if file_name.endswith(".dxf"):
            dxf_file_path = os.path.join(dxf_folder, file_name)
            print(f"Обработка файла: {file_name}")
            
            # Загрузка фигур из DXF
            shape_finder = DXFShapeFinder(dxf_file_path, config)
            polygons = shape_finder.input_polygon()
            
            # Добавляем информацию об источнике для каждого полигона
            file_polygons = [(poly, file_name + '_' + str(i)) for i, poly in enumerate(polygons) if len(poly) > 10]
            all_polygons.extend(file_polygons)
            
            print(f"  Загружено фигур: {len(polygons)}")
    
    print(f"\nВсего загружено фигур: {len(all_polygons)}")
    return all_polygons

def simplify_polygons(polygons: List[Tuple[List, str]], config: NestConfig) -> List[Tuple[List, str]]:
    """Упрощение полигонов с адаптивным коэффициентом"""
    simplified = []
    total_points_before = 0
    total_points_after = 0
    
    print("\nСтатистика упрощения полигонов:")
    print("-" * 70)
    print(f"{'Файл':<40} {'До':<10} {'После':<10} {'Разница %':<10} {'Валидность':<10}")
    print("-" * 70)
    
    # Группируем полигоны по файлам для статистики
    file_stats = {}
    for poly, source_file in polygons:
        if source_file not in file_stats:
            file_stats[source_file] = {'before': 0, 'after': 0}
        file_stats[source_file]['before'] += len(poly)
        total_points_before += len(poly)
    
    for poly, source_file in polygons:
        shape = Polygon(poly)
        original_area = shape.area
        
        # Адаптивное упрощени�� с сохранением минимального количества точек
        tolerance = 0.1  # Начальное значение tolerance
        min_points = 8   # Минимальное количество точек
        max_area_diff = 0.01  # Максимальное допустимое отклонение площади (1%)
        
        while True:
            simplified_shape = shape.simplify(tolerance=tolerance, preserve_topology=True)
            coords = [[float(x), float(y)] for x, y in simplified_shape.exterior.coords[:-1]]
            
            # Проверяем количество точек и отклонение площади
            area_diff = abs(simplified_shape.area - original_area) / original_area
            if len(coords) >= min_points and area_diff <= max_area_diff:
                break
                
            tolerance /= 2  # Уменьшаем tolerance, если результат неудовлетворительный
            if tolerance < 0.0001:  # Предотвращаем бесконечный цикл
                coords = poly  # Используем оригинальный полигон
                break
        
        simplified.append((coords, source_file))
        file_stats[source_file]['after'] += len(coords)
        file_stats[source_file]['valid'] = simplified_shape.is_valid
        total_points_after += len(coords)
    
    # Вывод статистики
    for file_name, stats in file_stats.items():
        points_before = stats['before']
        points_after = stats['after']
        reduction = ((points_before - points_after) / points_before * 100) if points_before > 0 else 0
        print(f"{file_name[:40]:<40} {points_before:<10} {points_after:<10} {reduction:>6.1f}% {stats['valid']}")
    
    print("-" * 70)
    total_reduction = ((total_points_before - total_points_after) / total_points_before * 100) if total_points_before > 0 else 0
    print(f"{'ИТОГО:':<40} {total_points_before:<10} {total_points_after:<10} {total_reduction:>6.1f}%")
    print("-" * 70)
    
    return simplified

def pack_all_shapes(polygons: List[Tuple[List, str]], config: NestConfig):
    """Упаковка всех фигур"""
    # Упрощаем полигоны перед созданием NFP Assistant
    print("\nУпрощение полигонов...")
    simplified_polygons = simplify_polygons(polygons, config)
    
    # Извлекаем только полигоны для NFP Assistant (без информации об источнике)
    poly_list = [poly for poly, _ in simplified_polygons]
    
    start_time = datetime.now()
    
    # Создание NFP Assistant
    print("\nСоздание NFP Assistant...")
    nfp_assistant = NFPAssistant(
        polys=poly_list,
        store_nfp=True,
        get_all_nfp=True
    )
    
    # Выполнение упаковки
    print("Выполнение упаковки...")
    try:
        bfl = BottomLeftFill(
            width=config.BIN_WIDTH,
            height=config.BIN_HEIGHT,
            original_polygons=poly_list,
            nfp_assistant=nfp_assistant
        )
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        # Добавляем информацию об источнике к результатам
        result_polygons = [(poly, source) for poly, (_, source) in zip(bfl.polygons, polygons)]
        
        # Расчет эффективности
        efficiency = calculate_efficiency(
            result_polygons,
            config.BIN_WIDTH,
            config.BIN_HEIGHT
        )
        
        # Вывод результатов
        print("\nРезультаты:")
        print(f"Время выполнения: {execution_time:.2f} секунд")
        print(f"Эффективность упаковки: {efficiency:.2f}%")
        
        # Визуа��изация результата
        visualize_packing_result(result_polygons, config.BIN_WIDTH, config.BIN_HEIGHT,
                               f"Результат упаковки (Эффективность: {efficiency:.1f}%)")
        
        # Анализ распределения фигур по файлам
        file_stats = {}
        for _, source in result_polygons:
            file_stats[source] = file_stats.get(source, 0) + 1
            
        print("\nРаспределение фигур по файлам:")
        for file_name, count in file_stats.items():
            print(f"{file_name}: {count} фигур")
        
    except Exception as e:
        print(f"\nОшибка при упаковке: {str(e)}")

def main():
    """Основная функция для тестирования"""
    # Конфигурация для тестирования
    config = NestConfig({
        'BIN_WIDTH': 2580,
        'BIN_HEIGHT': 1380,
        'POPULATION_SIZE': 30,
        'MUTA_RATE': 15,
        'ROTATIONS': 4,
        'GROUP_ROTATION': False,
        'SPACING': 6.3,
        'CONTOUR_SCALING': 10,
        'SPLIT_SPLINES': True,
        'SIMPLIFYING_POLYGONS': True,
        'SPLINE_FLATTENING_DISTANCE': 0.5,
        'SPLINE_FLATTENING_SEGMENTS': 50,
        'APPROX_EPSILON': 0.01
    })
    
    # Путь к папке с DXF файлами
    dxf_folder = "dxf_for_test"
    
    # Загрузка всех фигур
    all_polygons = load_all_dxf_files(dxf_folder, config)
    
    # Упаковка всех фигур
    if all_polygons:
        pack_all_shapes(all_polygons, config)
    else:
        print("Не найдено фигур для упаковки")

if __name__ == '__main__':
    main() 