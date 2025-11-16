import json
import os
from typing import List, Dict, Tuple, Optional, Any, Union
from dataclasses import dataclass, asdict
import copy
from enum import Enum
import time

__version__ = 'v1.2'

class Orientation(Enum):
    """Cell 方向枚举"""
    N = "N"   # 正常方向
    S = "S"   # 翻转180度
    FN = "FN" # 翻转Y轴
    FS = "FS" # 翻转X轴

@dataclass
class SiteInfo:
    """Site 信息类"""
    width: float = 0.14
    height: float = 0.9
    
    def snap_to_grid(self, x: float, y: float) -> Tuple[float, float]:
        """将坐标对齐到 site grid"""
        grid_x = round(x / self.width) * self.width
        grid_y = round(y / self.height) * self.height
        return grid_x, grid_y
    
    def to_grid_coords(self, x: float, y: float) -> Tuple[int, int]:
        """将绝对坐标转换为 grid 坐标"""
        grid_x = int(round(x / self.width))
        grid_y = int(round(y / self.height))
        return grid_x, grid_y
    
    def from_grid_coords(self, grid_x: int, grid_y: int) -> Tuple[float, float]:
        """将 grid 坐标转换为绝对坐标"""
        x = grid_x * self.width
        y = grid_y * self.height
        return x, y

@dataclass
class Cell:
    """表示单个 Cell 的类"""
    name: str
    x: float  # 始终以 N 方向保存的坐标
    y: float  # 始终以 N 方向保存的坐标
    orientation: Orientation = Orientation.N
    width: float = 0.14   # 标准单元宽度
    height: float = 0.9   # 标准单元高度
    
    def __post_init__(self):
        self.absolute_x = self.x
        self.absolute_y = self.y
        self.hierarchical_path = self.name
        self.site_info = SiteInfo()  # 默认 site 信息
        self._update_grid_coordinates()
        self._update_bbox()
    
    def _update_grid_coordinates(self):
        """更新 grid 坐标"""
        self.grid_x, self.grid_y = self.site_info.to_grid_coords(self.absolute_x, self.absolute_y)
        self.rel_grid_x, self.rel_grid_y = self.site_info.to_grid_coords(self.x, self.y)
    
    def _update_bbox(self):
        """更新边界框（始终基于 N 方向计算）"""
        # Cell 内部始终以 N 方向计算边界框
        self.bbox_min_x = self.absolute_x
        self.bbox_min_y = self.absolute_y
        self.bbox_max_x = self.absolute_x + self.width
        self.bbox_max_y = self.absolute_y + self.height
    
    def set_rel_position(self, rel_x: float, rel_y: float, site_info: SiteInfo = None):
        """设置相对于 origin 的相对位置"""
        if site_info:
            self.site_info = site_info
        
        self.x = rel_x
        self.y = rel_y
        self._update_grid_coordinates()
        self._update_bbox()

    def set_absolute_position(self, origin_x: float, origin_y: float, site_info: SiteInfo = None):
        """设置相对于 origin 的绝对位置"""
        if site_info:
            self.site_info = site_info
        
        self.absolute_x = origin_x + self.x
        self.absolute_y = origin_y + self.y
        self._update_grid_coordinates()
        self._update_bbox()
    
    def set_hierarchical_path(self, parent_path: str):
        """设置层次化路径"""
        if parent_path:
            self.hierarchical_path = f"{parent_path}/{self.name}"
        else:
            self.hierarchical_path = self.name
    
    def set_orientation(self, orientation: Orientation):
        """设置 cell 方向"""
        self.orientation = orientation
        # 方向改变不影响内部存储的坐标，只影响输出时的计算
    
    def set_size(self, width: float, height: float):
        """设置 cell 尺寸"""
        self.width = width
        self.height = height
        self._update_bbox()
    
    def get_placement_origin(self) -> Tuple[float, float]:
        """根据方向计算实际的 placement origin（用于 TCL 输出）"""
        if self.orientation == Orientation.N:
            # N 方向：原点在左下角
            return self.absolute_x, self.absolute_y
        elif self.orientation == Orientation.S:
            # S 方向：翻转180度，原点在右上角
            return self.absolute_x + self.width, self.absolute_y + self.height
        elif self.orientation == Orientation.FN:
            # FN 方向：翻转Y轴，原点在右下角
            return self.absolute_x + self.width, self.absolute_y
        elif self.orientation == Orientation.FS:
            # FS 方向：翻转X轴，原点在左上角
            return self.absolute_x, self.absolute_y + self.height
        return self.absolute_x, self.absolute_y
    
    def get_orientation_for_row(self, row_y: float) -> Orientation:
        """根据所在行位置确定方向(x翻转)"""
        grid_y = int(round(row_y / self.site_info.height))
        left_ori = [Orientation.FS, Orientation.N]
        right_ori = [Orientation.FN, Orientation.S]
        orientation_type = 1 if self.orientation in left_ori else 0
        if orientation_type:
            if grid_y % 2 == 0:
                return Orientation.FS
            else:
                return Orientation.N
        else:
            if grid_y % 2 == 0:
                return Orientation.S
            else:
                return Orientation.FN
    
    def flip_oritentation(self):
        """flip Cell"""
        if self.orientation == Orientation.N:
            self.orientation = Orientation.FN
        elif self.orientation == Orientation.S:
            self.orientation = Orientation.FS
        elif self.orientation == Orientation.FN:
            self.orientation = Orientation.N
        elif self.orientation == Orientation.FS:
            self.orientation = Orientation.S

    def get_bbox(self) -> Tuple[float, float, float, float]:
        """获取边界框（始终基于 N 方向）"""
        return self.bbox_min_x, self.bbox_min_y, self.bbox_max_x, self.bbox_max_y
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        placement_x, placement_y = self.get_placement_origin()
        return {
            "name": self.name,
            "rel_x": self.x,
            "rel_y": self.y,
            "rel_grid_x": self.rel_grid_x,
            "rel_grid_y": self.rel_grid_y,
            "abs_x": round(self.absolute_x, 3),
            "abs_y": round(self.absolute_y, 3),
            "placement_x": round(placement_x, 3),
            "placement_y": round(placement_y, 3),
            "grid_x": self.grid_x,
            "grid_y": self.grid_y,
            "width": self.width,
            "height": self.height,
            "orientation": self.orientation.value,
            "bbox": {
                "min_x": round(self.bbox_min_x, 3),
                "min_y": round(self.bbox_min_y, 3),
                "max_x": round(self.bbox_max_x, 3),
                "max_y": round(self.bbox_max_y, 3)
            },
            "hierarchical_path": self.hierarchical_path
        }
    
    def clone(self) -> 'Cell':
        """创建 Cell 的副本"""
        new_cell = Cell(self.name, self.x, self.y, self.orientation, self.width, self.height)
        new_cell.hierarchical_path = self.hierarchical_path
        new_cell.site_info = self.site_info
        new_cell.absolute_x = self.absolute_x
        new_cell.absolute_y = self.absolute_y
        new_cell._update_grid_coordinates()
        return new_cell
    
    def __repr__(self):
        placement_x, placement_y = self.get_placement_origin()
        return f"Cell('{self.name}', stored:({self.x}, {self.y}), abs:({self.absolute_x}, {self.absolute_y}), placement:({placement_x}, {placement_y}), grid:({self.grid_x}, {self.grid_y}), size:({self.width}x{self.height}), orient:{self.orientation.value}, path:'{self.hierarchical_path}')"

class Micro:
    """表示一个 Micro，可以包含 Cells 和 sub-Micros"""
    def __init__(self, name: str, origin_x: float = 0, origin_y: float = 0, description: str = "", site_info: SiteInfo = None):
        self.name = name
        self.origin_x = origin_x
        self.origin_y = origin_y
        self.description = description
        self.site_info = site_info or SiteInfo()
        self.cells: List[Cell] = []
        self.sub_micros: List['Micro'] = []
        self.parent: Optional['Micro'] = None
        self.hierarchical_path = name
        
        # Grid coordinates
        self.grid_x, self.grid_y = self.site_info.to_grid_coords(self.origin_x, self.origin_y)
        self.rel_grid_x, self.rel_grid_y = 0, 0  # 相对于父 micro 的 grid 坐标
        
        self._update_absolute_positions()
    
    def set_hierarchical_path(self, parent_path: str):
        """设置层次化路径"""
        if parent_path:
            self.hierarchical_path = f"{parent_path}/{self.name}"
        else:
            self.hierarchical_path = self.name
        
        # 更新所有子元素的路径
        for cell in self.cells:
            cell.set_hierarchical_path(self.hierarchical_path)
        for sub_micro in self.sub_micros:
            sub_micro.set_hierarchical_path(self.hierarchical_path)
    
    def add_cell(self, cell: Cell) -> 'Micro':
        """添加一个 Cell 到 micro 中"""
        cell_cpy = cell.clone()
        cell_cpy.set_absolute_position(self.origin_x, self.origin_y, self.site_info)
        cell_cpy.set_hierarchical_path(self.hierarchical_path)
        self.cells.append(cell_cpy)
        return self
    
    def add_cells(self, cells: List[Cell]) -> 'Micro':
        """批量添加 Cells"""
        for cell in cells:
            self.add_cell(cell)
        return self
    
    def add_sub_micro(self, sub_micro: 'Micro') -> 'Micro':
        """添加一个 sub-micro"""
        sub_micro_cpy = sub_micro.clone()
        sub_micro_cpy.parent = self
        sub_micro_cpy.set_hierarchical_path(self.hierarchical_path)
        sub_micro_cpy.set_origin(self.origin_x + sub_micro_cpy.origin_x, 
                               self.origin_y + sub_micro_cpy.origin_y)
        self.sub_micros.append(sub_micro_cpy)
        return self
    
    def remove_cell(self, cell_name: str) -> bool:
        """根据名称移除 cell"""
        for i, cell in enumerate(self.cells):
            if cell.name == cell_name:
                self.cells.pop(i)
                return True
        return False
    
    def remove_sub_micro(self, micro_name: str) -> bool:
        """根据名称移除 sub-micro"""
        for i, sub_micro in enumerate(self.sub_micros):
            if sub_micro.name == micro_name:
                self.sub_micros.pop(i)
                return True
        return False
    
    def set_origin(self, x: float, y: float) -> 'Micro':
        """设置 micro 的 origin 位置，并更新所有内容的绝对位置"""
        # 对齐到 site grid
        snapped_x, snapped_y = self.site_info.snap_to_grid(x, y)
        self.origin_x = snapped_x
        self.origin_y = snapped_y
        self._update_grid_coordinates()
        self._update_absolute_positions()
        return self
    
    def set_origin_by_grid(self, grid_x: int, grid_y: int) -> 'Micro':
        """通过 grid 坐标设置 origin"""
        x, y = self.site_info.from_grid_coords(grid_x, grid_y)
        return self.set_origin(x, y)
    
    def move_by(self, dx: float, dy: float) -> 'Micro':
        """相对移动 micro"""
        # 对齐到 site grid 的增量
        snapped_dx, snapped_dy = self.site_info.snap_to_grid(dx, dy)
        self.origin_x += snapped_dx
        self.origin_y += snapped_dy
        self._update_grid_coordinates()
        self._update_absolute_positions()
        return self
    
    def move_by_grid(self, dgrid_x: int, dgrid_y: int) -> 'Micro':
        """通过 grid 坐标相对移动"""
        dx = dgrid_x * self.site_info.width
        dy = dgrid_y * self.site_info.height
        return self.move_by(dx, dy)
    
    def flip_horizontal(self) :
        min_x = self.calculate_bounding_box()[0]
        max_x = self.calculate_bounding_box()[2]
        max_x -= min_x
        # 更新 cells
        for cell in self.cells:
            cell.set_rel_position(max_x - cell.x - (cell.bbox_max_x - cell.bbox_min_x), cell.y, self.site_info)
            cell.flip_oritentation()
        
        # 更新 sub-micros（相对位置叠加）
        for sub_micro in self.sub_micros:
            sub_micro_min_x = sub_micro.calculate_bounding_box()[0]
            sub_micro_max_x = sub_micro.calculate_bounding_box()[2]
            sub_micro_max_x -= sub_micro_min_x
            sub_micro.set_origin(max_x - sub_micro.origin_x - sub_micro_max_x, sub_micro.origin_y)
            sub_micro.flip_horizontal()

        self._update_grid_coordinates()
        self._update_absolute_positions()



    def _update_grid_coordinates(self):
        """更新 grid 坐标"""
        self.grid_x, self.grid_y = self.site_info.to_grid_coords(self.origin_x, self.origin_y)
        
        # 计算相对于父 micro 的 grid 坐标
        if self.parent:
            parent_grid_x, parent_grid_y = self.parent.site_info.to_grid_coords(
                self.parent.origin_x, self.parent.origin_y)
            self.rel_grid_x = self.grid_x - parent_grid_x
            self.rel_grid_y = self.grid_y - parent_grid_y
        else:
            self.rel_grid_x = self.grid_x
            self.rel_grid_y = self.grid_y
    
    def _update_absolute_positions(self):
        """更新所有 cells 和 sub-micros 的绝对位置"""
        # 更新 cells
        for cell in self.cells:
            cell.set_absolute_position(self.origin_x, self.origin_y, self.site_info)
            # 根据行位置自动设置方向
            cell_orientation = cell.get_orientation_for_row(cell.absolute_y)
            cell.set_orientation(cell_orientation)
        
        # 更新 sub-micros（相对位置叠加）
        for sub_micro in self.sub_micros:
            sub_micro.set_origin(self.origin_x + sub_micro.origin_x, 
                               self.origin_y + sub_micro.origin_y)
    
    def get_all_cells(self) -> List[Cell]:
        """获取所有 cells（包括 sub-micros 中的 cells）"""
        all_cells = []
        
        # 添加当前 micro 的 cells
        all_cells.extend(self.cells)
        
        # 递归添加 sub-micros 的 cells
        for sub_micro in self.sub_micros:
            all_cells.extend(sub_micro.get_all_cells())
        
        return all_cells
    
    def get_all_sub_micros(self) -> List['Micro']:
        """获取所有 sub-micros（递归）"""
        all_sub_micros = []
        
        for sub_micro in self.sub_micros:
            all_sub_micros.append(sub_micro)
            all_sub_micros.extend(sub_micro.get_all_sub_micros())
        
        return all_sub_micros
    
    def get_cell_placements(self) -> List[Dict]:
        """获取所有 cells 的绝对位置信息（用于 TCL 脚本）"""
        placements = []
        all_cells = self.get_all_cells()
        
        for cell in all_cells:
            placement_x, placement_y = cell.get_placement_origin()
            placements.append({
                "cell": cell.hierarchical_path,
                "x": round(placement_x, 3),
                "y": round(placement_y, 3),
                "orientation": cell.orientation.value,
                "micro": self.name
            })
        
        return placements
    
    def get_cell_by_path(self, hierarchical_path: str) -> Optional[Cell]:
        """根据层次化路径查找 cell"""
        for cell in self.get_all_cells():
            if cell.hierarchical_path == hierarchical_path:
                return cell
        return None
    
    def get_sub_micro_by_path(self, hierarchical_path: str) -> Optional['Micro']:
        """根据层次化路径查找 sub-micro"""
        if self.hierarchical_path == hierarchical_path:
            return self
        
        for sub_micro in self.sub_micros:
            result = sub_micro.get_sub_micro_by_path(hierarchical_path)
            if result:
                return result
        
        return None
    
    def calculate_bounding_box(self) -> Tuple[float, float, float, float]:
        """计算 micro 内所有内容的边界框（基于实际边界框）"""
        all_cells = self.get_all_cells()
        
        if not all_cells:
            return 0, 0, 0, 0
        
        # 使用边界框
        min_x = min(cell.get_bbox()[0] for cell in all_cells)
        max_x = max(cell.get_bbox()[2] for cell in all_cells)
        min_y = min(cell.get_bbox()[1] for cell in all_cells)
        max_y = max(cell.get_bbox()[3] for cell in all_cells)
        
        return min_x, min_y, max_x, max_y
    
    def to_dict(self) -> Dict:
        """转换为字典格式（用于导出）"""
        return {
            "name": self.name,
            "origin_x": self.origin_x,
            "origin_y": self.origin_y,
            "grid_x": self.grid_x,
            "grid_y": self.grid_y,
            "rel_grid_x": self.rel_grid_x,
            "rel_grid_y": self.rel_grid_y,
            "site_info": {
                "width": self.site_info.width,
                "height": self.site_info.height
            },
            "description": self.description,
            "hierarchical_path": self.hierarchical_path,
            "cells": [cell.to_dict() for cell in self.cells],
            "sub_micros": [sub_micro.to_dict() for sub_micro in self.sub_micros],
            "bounding_box": {
                "min_x": self.calculate_bounding_box()[0],
                "min_y": self.calculate_bounding_box()[1],
                "max_x": self.calculate_bounding_box()[2],
                "max_y": self.calculate_bounding_box()[3]
            }
        }
    
    def clone(self, new_name: str = None) -> 'Micro':
        """创建 Micro 的副本（深度复制）"""
        cloned_micro = Micro(new_name or f"{self.name}", 
                           self.origin_x, self.origin_y, self.description,
                           SiteInfo(self.site_info.width, self.site_info.height))
        
        # 复制 cells
        for cell in self.cells:
            cloned_micro.add_cell(cell.clone())
        
        # 递归复制 sub-micros
        for sub_micro in self.sub_micros:
            cloned_micro.add_sub_micro(sub_micro.clone())
        
        return cloned_micro
    
    def export_to_file(self, filename: str):
        """导出 Micro 到 JSON 文件"""
        micro_data = self.to_dict()
        with open(filename, 'w') as f:
            json.dump(micro_data, f, indent=2)
        print(f"Micro '{self.name}' exported to: {filename}")
    
    @classmethod
    def load_from_file(cls, filename: str) -> 'Micro':
        """从 JSON 文件加载 Micro"""
        with open(filename, 'r') as f:
            micro_data = json.load(f)
        
        site_info_data = micro_data.get("site_info", {})
        site_info = SiteInfo(
            width=site_info_data.get("width", 0.14),
            height=site_info_data.get("height", 0.9)
        )
        
        micro = cls(
            name=micro_data["name"],
            origin_x=micro_data["origin_x"],
            origin_y=micro_data["origin_y"],
            description=micro_data.get("description", ""),
            site_info=site_info
        )
        
        # 加载 cells
        for cell_data in micro_data["cells"]:
            cell = Cell(
                name=cell_data["name"],
                x=cell_data["rel_x"],
                y=cell_data["rel_y"],
                orientation=Orientation(cell_data.get("orientation", "N")),
                width=cell_data.get("width", 0.14),
                height=cell_data.get("height", 0.9)
            )
            micro.add_cell(cell)
        
        # 递归加载 sub-micros
        for sub_micro_data in micro_data.get("sub_micros", []):
            sub_micro = cls._load_from_dict(sub_micro_data)
            micro.add_sub_micro(sub_micro)
        
        return micro
    
    @classmethod
    def _load_from_dict(cls, micro_data: Dict) -> 'Micro':
        """从字典加载 Micro（递归）"""
        site_info_data = micro_data.get("site_info", {})
        site_info = SiteInfo(
            width=site_info_data.get("width", 0.14),
            height=site_info_data.get("height", 0.9)
        )
        
        micro = cls(
            name=micro_data["name"],
            origin_x=micro_data["origin_x"],
            origin_y=micro_data["origin_y"],
            description=micro_data.get("description", ""),
            site_info=site_info
        )
        
        # 加载 cells
        for cell_data in micro_data["cells"]:
            cell = Cell(
                name=cell_data["name"],
                x=cell_data["rel_x"],
                y=cell_data["rel_y"],
                orientation=Orientation(cell_data.get("orientation", "N")),
                width=cell_data.get("width", 0.14),
                height=cell_data.get("height", 0.9)
            )
            micro.add_cell(cell)
        
        # 递归加载 sub-micros
        for sub_micro_data in micro_data.get("sub_micros", []):
            sub_micro = cls._load_from_dict(sub_micro_data)
            micro.add_sub_micro(sub_micro)
        
        return micro
    
    def print_hierarchy(self, level: int = 0):
        """打印层次结构"""
        indent = "  " * level
        print(f"{indent}Micro: {self.name} (path: {self.hierarchical_path})")
        print(f"{indent}  Origin: ({self.origin_x}, {self.origin_y}) grid:({self.grid_x}, {self.grid_y})")
        
        for cell in self.cells:
            placement_x, placement_y = cell.get_placement_origin()
            print(f"{indent}  Cell: {cell.name} -> {cell.hierarchical_path}")
            print(f"{indent}    Stored: ({cell.x}, {cell.y})")
            print(f"{indent}    Absolute: ({cell.absolute_x}, {cell.absolute_y})")
            print(f"{indent}    Placement: ({placement_x}, {placement_y}) orient:{cell.orientation.value}")
            print(f"{indent}    Grid: ({cell.grid_x}, {cell.grid_y})")
            print(f"{indent}    Size: {cell.width}x{cell.height}")
        
        for sub_micro in self.sub_micros:
            sub_micro.print_hierarchy(level + 1)
    
    def __repr__(self):
        return f"Micro('{self.name}', origin:({self.origin_x}, {self.origin_y}), grid:({self.grid_x}, {self.grid_y}), cells:{len(self.cells)}, sub_micros:{len(self.sub_micros)})"

# MicroLibrary 和 PlaceCellEngine 类保持不变（与之前相同）
# 由于篇幅限制，这里省略了这些类的完整代码，它们与之前的版本基本相同
# 只需要确保在创建 Cell 时传递 width 和 height 参数

class MicroLibrary:
    """Micro 库管理类"""
    def __init__(self, library_path: str = "micro_library"):
        self.library_path = library_path
        self.micro_templates: Dict[str, Micro] = {}
        self._ensure_library_directory()
    
    def _ensure_library_directory(self):
        """确保库目录存在"""
        os.makedirs(self.library_path, exist_ok=True)
    
    def save_micro(self, micro: Micro):
        """保存 Micro 到库中"""
        filename = os.path.join(self.library_path, f"{micro.name}.json")
        micro.export_to_file(filename)
        self.micro_templates[micro.name] = micro.clone()
    
    def load_micro(self, micro_name: str) -> Optional[Micro]:
        """从库中加载 Micro"""
        filename = os.path.join(self.library_path, f"{micro_name}.json")
        if os.path.exists(filename):
            micro = Micro.load_from_file(filename)
            self.micro_templates[micro_name] = micro
            return micro
        else:
            print(f"Micro '{micro_name}' not found in library")
            return None
    
    def list_available_micros(self) -> List[str]:
        """列出库中所有可用的 Micro"""
        micro_files = [f for f in os.listdir(self.library_path) if f.endswith('.json')]
        return [os.path.splitext(f)[0] for f in micro_files]
    
    def create_micro_from_template(self, template_name: str, new_name: str, 
                                 origin_x: float = 0, origin_y: float = 0) -> Optional[Micro]:
        """从模板创建新的 Micro 实例"""
        if template_name in self.micro_templates:
            template = self.micro_templates[template_name]
            new_micro = template.clone(new_name)
            new_micro.set_origin(origin_x, origin_y)
            return new_micro
        else:
            # 尝试从文件加载模板
            micro = self.load_micro(template_name)
            if micro:
                new_micro = micro.clone(new_name)
                new_micro.set_origin(origin_x, origin_y)
                return new_micro
        return None

class PlaceCellEngine:
    """Place Cell 引擎主类"""
    def __init__(self, library_path: str = "micro_library", site_info: SiteInfo = None):

        self.active_micros: Dict[str, Micro] = {}
        self.library = MicroLibrary(library_path)
        self.global_placements: List[Dict] = []
        self.site_info = site_info or SiteInfo()
    
    def create_micro(self, name: str, origin_x: float = 0, origin_y: float = 0, 
                   description: str = "") -> Micro:
        """创建一个新的 micro"""
        micro = Micro(name, origin_x, origin_y, description, self.site_info)
        self.active_micros[name] = micro
        return micro
    
    def create_micro_from_cells(self, name: str, cells: List[Dict], 
                              origin_x: float = 0, origin_y: float = 0) -> Micro:
        """从 cell 数据列表创建 micro"""
        micro = self.create_micro(name, origin_x, origin_y)
        
        for cell_data in cells:
            orientation = Orientation(cell_data.get("orientation", "N"))
            width = cell_data.get("width", 0.14)
            height = cell_data.get("height", 0.9)
            cell = Cell(cell_data["cell"], cell_data["x"], cell_data["y"], orientation, width, height)
            micro.add_cell(cell)
        
        return micro
    
    def create_micro_from_template(self, template_name: str, new_name: str,
                                 origin_x: float = 0, origin_y: float = 0) -> Optional[Micro]:
        """从库模板创建 micro"""
        micro = self.library.create_micro_from_template(template_name, new_name, origin_x, origin_y)
        if micro:
            # 更新 site info 为引擎的配置
            micro.site_info = self.site_info
            micro.set_origin(origin_x, origin_y)  # 重新对齐到 grid
            self.active_micros[new_name] = micro
        return micro
    
    def place_micro(self, micro_name: str, origin_x: float, origin_y: float):
        """放置 micro 到指定位置（自动对齐到 site grid）"""
        if micro_name not in self.active_micros:
            raise ValueError(f"Micro '{micro_name}' not found")
        
        self.active_micros[micro_name].set_origin(origin_x, origin_y)
    
    def place_micro_by_grid(self, micro_name: str, grid_x: int, grid_y: int):
        """通过 grid 坐标放置 micro"""
        if micro_name not in self.active_micros:
            raise ValueError(f"Micro '{micro_name}' not found")
        
        self.active_micros[micro_name].set_origin_by_grid(grid_x, grid_y)
    
    def move_micro(self, micro_name: str, dx: float, dy: float):
        """移动 micro（自动对齐到 site grid）"""
        if micro_name not in self.active_micros:
            raise ValueError(f"Micro '{micro_name}' not found")
        
        self.active_micros[micro_name].move_by(dx, dy)
    
    def move_micro_by_grid(self, micro_name: str, dgrid_x: int, dgrid_y: int):
        """通过 grid 坐标移动 micro"""
        if micro_name not in self.active_micros:
            raise ValueError(f"Micro '{micro_name}' not found")
        
        self.active_micros[micro_name].move_by_grid(dgrid_x, dgrid_y)

    def flip_micro_horizontal(self, micro_name : str):
        """水平翻转 micro"""
        if micro_name not in self.active_micros:
            raise ValueError(f"Micro '{micro_name}' not found")
        self.active_micros[micro_name].flip_horizontal()

    
    def remove_micro(self, micro_name: str) -> bool:
        """移除 micro"""
        if micro_name in self.active_micros:
            del self.active_micros[micro_name]
            return True
        return False
    
    def get_micro(self, micro_name: str) -> Optional[Micro]:
        """获取 micro"""
        return self.active_micros.get(micro_name)
    
    def list_active_micros(self) -> List[str]:
        """列出所有活跃的 micro"""
        return list(self.active_micros.keys())
    
    def save_micro_to_library(self, micro_name: str):
        """保存 micro 到库中"""
        if micro_name in self.active_micros:
            self.library.save_micro(self.active_micros[micro_name])
        else:
            raise ValueError(f"Micro '{micro_name}' not found")
    
    def load_micro_from_library(self, micro_name: str, instance_name: str = None) -> Optional[Micro]:
        """从库中加载 micro"""
        micro = self.library.load_micro(micro_name)
        if micro:
            instance_name = instance_name or micro_name
            micro.name = instance_name
            micro.site_info = self.site_info  # 使用引擎的 site info
            micro.set_hierarchical_path('')
            self.active_micros[instance_name] = micro
            return micro
        return None
    
    def generate_global_placements(self) -> List[Dict]:
        """生成所有 micro 中所有 cell 的全局位置"""
        self.global_placements = []
        
        for micro_name, micro in self.active_micros.items():
            micro_placements = micro.get_cell_placements()
            self.global_placements.extend(micro_placements)
        
        return self.global_placements
    
    def generate_tcl_script(self, filename: str = "place_cell.tcl"):
        """生成 TCL 布局脚本"""
        placements = self.generate_global_placements()
        
        with open(filename, 'w') as f:
            f.write("# Auto-generated placement script\n")
            f.write(f"# TIME : {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}\n")
            f.write("# Generated by Place Cell Engine\n")
            f.write(f"# Version : {__version__}\n")
            f.write("# Hierarchical cell names\n\n")
            
            # 按 micro 分组添加注释
            current_micro = None
            for placement in placements:
                if placement["micro"] != current_micro:
                    current_micro = placement["micro"]
                    f.write(f"\n# Micro: {current_micro}\n")
                # 添加方向设置
                cmd = f"set_attribute {placement['cell']} origin {{{placement['x']:.3f} {placement['y']:.3f}}}"
                f.write(cmd + "\n")
                orient_cmd = f"set_attribute {placement['cell']} orientation {placement['orientation']}"
                f.write(orient_cmd + "\n")
                

            
            f.write("\n# Fix all placed cells\n")
            for placement in placements:
                cmd = f"set_attribute [get_cells {placement['cell']}] is_fixed true"
                f.write(cmd + "\n")
        
        print(f"TCL script generated: {filename}")
        return placements
    
    def get_placement_statistics(self) -> Dict:
        """获取布局统计信息"""
        placements = self.generate_global_placements()
        min_x, min_y, max_x, max_y = self.calculate_bounding_box()
        
        total_cells = len(placements)
        total_sub_micros = sum(len(micro.get_all_sub_micros()) for micro in self.active_micros.values())
        
        stats = {
            "total_cells": total_cells,
            "total_micros": len(self.active_micros),
            "total_sub_micros": total_sub_micros,
            "site_info": {
                "width": self.site_info.width,
                "height": self.site_info.height
            },
            "bounding_box": {
                "min_x": min_x,
                "min_y": min_y,
                "max_x": max_x,
                "max_y": max_y,
                "width": max_x - min_x,
                "height": max_y - min_y
            },
            "micros_info": {name: {
                "cells_count": len(micro.get_all_cells()),
                "sub_micros_count": len(micro.get_all_sub_micros()),
                "origin": (micro.origin_x, micro.origin_y),
                "grid_origin": (micro.grid_x, micro.grid_y)
            } for name, micro in self.active_micros.items()}
        }
        
        return stats
    
    def calculate_bounding_box(self) -> Tuple[float, float, float, float]:
        """计算所有 cell 的边界框"""
        placements = self.generate_global_placements()
        
        if not placements:
            return 0, 0, 0, 0
        
        min_x = min(p['x'] for p in placements)
        max_x = max(p['x'] for p in placements)
        min_y = min(p['y'] for p in placements)
        max_y = max(p['y'] for p in placements)
        
        return min_x, min_y, max_x, max_y
    
    def print_hierarchy(self):
        """打印所有 micro 的层次结构"""
        for micro_name, micro in self.active_micros.items():
            print(f"\n=== Hierarchy for {micro_name} ===")
            micro.print_hierarchy()
    
    def save_configuration(self, filename: str):
        """保存引擎配置到 JSON 文件"""
        config = {
            "site_info": {
                "width": self.site_info.width,
                "height": self.site_info.height
            },
            "active_micros": {name: micro.to_dict() for name, micro in self.active_micros.items()}
        }
        
        with open(filename, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"Engine configuration saved: {filename}")
    
    def load_configuration(self, filename: str):
        """从 JSON 文件加载引擎配置"""
        with open(filename, 'r') as f:
            config = json.load(f)
        
        # 更新 site info
        site_info_data = config.get("site_info", {})
        self.site_info = SiteInfo(
            width=site_info_data.get("width", 0.14),
            height=site_info_data.get("height", 0.9)
        )
        
        self.active_micros.clear()
        
        for micro_name, micro_data in config["active_micros"].items():
            micro = Micro._load_from_dict(micro_data)
            micro.site_info = self.site_info  # 使用引擎的 site info
            self.active_micros[micro_name] = micro
        
        print(f"Engine configuration loaded: {filename}")

# 示例使用和测试
def demo_enhanced_micro():
    """演示增强的 Micro 功能"""
    # 创建引擎实例，指定 site 信息
    site_info = SiteInfo(width=0.14, height=0.9)
    engine = PlaceCellEngine(site_info=site_info)
    
    print(f"Using site info: {site_info.width} x {site_info.height}")
    
    # 1. 创建基础 cell 模板数据，包含不同尺寸的 cell
    buffer_cells = [
        {"cell": "BUF1", "x": 0.0, "y": 0.0, "width": 0.14, "height": 0.9},
        {"cell": "BUF2", "x": 0.14, "y": 0.0, "width": 0.28, "height": 0.9},  # 2倍宽度
        {"cell": "BUF3", "x": 0.42, "y": 0.0, "width": 0.14, "height": 0.9},
    ]
    
    inverter_cells = [
        {"cell": "INV1", "x": 0.0, "y": 0.9, "width": 0.14, "height": 0.9},
        {"cell": "INV2", "x": 0.14, "y": 0.9, "width": 0.14, "height": 1.8},  # 2倍高度
    ]
    
    # 2. 创建子 Micro（Buffer Chain）
    buffer_chain = engine.create_micro_from_cells("BUFFER_CHAIN", buffer_cells, 0, 0)
    buffer_chain.description = "Basic buffer chain with different cell sizes"
    
    # 3. 创建子 Micro（Inverter Pair）
    inverter_pair = engine.create_micro_from_cells("INVERTER_PAIR", inverter_cells, 0, 0)
    inverter_pair.description = "Inverter pair with different cell sizes"
    
    # 4. 创建主 Micro（包含子 Micro）
    main_macro = engine.create_micro("MAIN_MACRO", 0, 0, "Main hierarchical macro")
    
    # 添加直接 cells（不同尺寸）
    main_macro.add_cell(Cell("INPUT_PAD", 0.0, 0.0, Orientation.N, 0.14, 0.9))
    main_macro.add_cell(Cell("OUTPUT_PAD", 1.4, 0.0, Orientation.N, 0.28, 0.9))  # 2倍宽度
    
    # 添加子 Micro 实例
    buffer_instance1 = buffer_chain.clone("BUFFER_CHAIN_1")
    buffer_instance1.set_origin_by_grid(1, 0)  # 使用 grid 坐标
    
    buffer_instance2 = buffer_chain.clone("BUFFER_CHAIN_2") 
    buffer_instance2.set_origin_by_grid(3, 0)  # 使用 grid 坐标
    
    inverter_instance = inverter_pair.clone("INVERTER_PAIR_1")
    inverter_instance.set_origin_by_grid(2, 1)  # 使用 grid 坐标
    
    main_macro.add_sub_micro(buffer_instance1)
    main_macro.add_sub_micro(buffer_instance2)
    main_macro.add_sub_micro(inverter_instance)
    
    # 5. 保存到库中
    engine.save_micro_to_library("BUFFER_CHAIN")
    engine.save_micro_to_library("INVERTER_PAIR") 
    engine.save_micro_to_library("MAIN_MACRO")
    
    # 6. 创建多个主 Micro 实例，使用 grid 坐标放置
    engine.create_micro_from_template("MAIN_MACRO", "MACRO_LEFT", 0, 0)
    engine.create_micro_from_template("MAIN_MACRO", "MACRO_RIGHT", 5.6, 0)  # 40个 site 宽度
    
    # 7. 显示层次结构
    print("\n=== Hierarchical Structure ===")
    engine.print_hierarchy()
    
    # 8. 显示统计信息
    print("\n=== Placement Statistics ===")
    stats = engine.get_placement_statistics()
    print(f"Total cells: {stats['total_cells']}")
    print(f"Total micros: {stats['total_micros']}")
    print(f"Total sub-micros: {stats['total_sub_micros']}")
    print(f"Site info: {stats['site_info']}")
    print(f"Bounding box: {stats['bounding_box']}")
    
    # 9. 生成 TCL 脚本
    print("\n=== Generating TCL Script ===")
    placements = engine.generate_tcl_script("enhanced_placement.tcl")
    
    # 显示一些布局示例
    print("\n=== Sample Placements (with hierarchical names, orientations and placement origins) ===")
    for placement in placements[:10]:
        print(f"  {placement['cell']} -> ({placement['x']}, {placement['y']}) orient:{placement['orientation']}")
    
    return engine

if __name__ == "__main__":
    demo_enhanced_micro()