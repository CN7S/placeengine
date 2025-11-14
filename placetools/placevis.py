import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Rectangle, Circle, FancyBboxPatch
import numpy as np
from typing import List, Dict, Tuple, Optional
import json

class PlacementVisualizer:
    """布局可视化器"""
    
    def __init__(self, figsize=(12, 10)):
        self.figsize = figsize
        self.colors = plt.cm.Set3(np.linspace(0, 1, 12))
        self.micro_colors = {}
        
    def _get_micro_color(self, micro_name: str):
        """为每个 micro 分配颜色"""
        if micro_name not in self.micro_colors:
            color_idx = len(self.micro_colors) % len(self.colors)
            self.micro_colors[micro_name] = self.colors[color_idx]
        return self.micro_colors[micro_name]
    
    def plot_placement(self, placements: List[Dict], 
                      output_file: str = "placement_plot.png",
                      show_labels: bool = True,
                      show_grid: bool = True,
                      title: str = "Cell Placement Visualization"):
        """绘制布局图"""
        
        fig, ax = plt.subplots(1, 1, figsize=self.figsize)
        
        # 收集数据
        micros = set()
        cells_by_micro = {}
        
        for placement in placements:
            micro_name = placement.get('micro', 'unknown')
            micros.add(micro_name)
            
            if micro_name not in cells_by_micro:
                cells_by_micro[micro_name] = []
            
            cells_by_micro[micro_name].append(placement)
        
        # 绘制每个 micro 的 cells
        for micro_name, cells in cells_by_micro.items():
            color = self._get_micro_color(micro_name)
            
            # 绘制 cells
            x_coords = [cell['x'] for cell in cells]
            y_coords = [cell['y'] for cell in cells]
            cell_names = [cell['cell'] for cell in cells]
            
            # 绘制 cell 位置点
            scatter = ax.scatter(x_coords, y_coords, 
                               c=[color], alpha=0.7, s=50,
                               label=micro_name, edgecolors='black', linewidth=0.5)
            
            # 添加 cell 标签
            if show_labels:
                for i, (x, y, name) in enumerate(zip(x_coords, y_coords, cell_names)):
                    # 只显示部分标签，避免过于拥挤
                    if i % max(1, len(cells) // 20) == 0 or len(cells) < 20:
                        ax.annotate(name, (x, y), 
                                  xytext=(5, 5), textcoords='offset points',
                                  fontsize=6, alpha=0.7,
                                  bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.7))
        
        # 设置图形属性
        ax.set_xlabel('X Coordinate', fontsize=12)
        ax.set_ylabel('Y Coordinate', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        
        # 添加网格
        if show_grid:
            ax.grid(True, alpha=0.3, linestyle='--')
        
        # 添加图例
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=10)
        
        # 自动调整坐标轴范围
        all_x = [p['x'] for p in placements]
        all_y = [p['y'] for p in placements]
        x_margin = (max(all_x) - min(all_x)) * 0.1
        y_margin = (max(all_y) - min(all_y)) * 0.1
        
        ax.set_xlim(min(all_x) - x_margin, max(all_x) + x_margin)
        ax.set_ylim(min(all_y) - y_margin, max(all_y) + y_margin)
        
        # 设置等比例
        ax.set_aspect('equal', adjustable='box')
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Placement plot saved to: {output_file}")
        plt.show()
        
        return fig, ax
    
    def plot_placement_with_bbox(self, placements: List[Dict], 
                               output_file: str = "placement_with_bbox.png",
                               show_density: bool = True):
        """绘制带边界框和密度信息的布局图"""
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
        
        # 左图：基础布局
        self._plot_basic_placement(ax1, placements, "Cell Placement")
        
        # 右图：带边界框和密度
        self._plot_placement_with_analysis(ax2, placements, "Placement with Bounding Box")
        
        # 计算统计信息
        stats = self._calculate_placement_stats(placements)
        
        # 添加统计信息文本框
        stats_text = f"Total Cells: {stats['total_cells']}\n"
        stats_text += f"Total Micros: {stats['total_micros']}\n"
        stats_text += f"Bounding Box: {stats['bbox_width']:.2f} x {stats['bbox_height']:.2f}\n"
        stats_text += f"Area: {stats['area']:.2f}\n"
        stats_text += f"Density: {stats['density']:.2%}"
        
        ax2.text(0.02, 0.98, stats_text, transform=ax2.transAxes, 
                fontsize=10, verticalalignment='top',
                bbox=dict(boxstyle="round,pad=0.5", fc="lightyellow", alpha=0.8))
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Enhanced placement plot saved to: {output_file}")
        plt.show()
        
        return fig, (ax1, ax2)
    
    def _plot_basic_placement(self, ax, placements: List[Dict], title: str):
        """绘制基础布局图"""
        micros = set(p['micro'] for p in placements)
        
        for micro_name in micros:
            color = self._get_micro_color(micro_name)
            micro_placements = [p for p in placements if p['micro'] == micro_name]
            
            x_coords = [p['x'] for p in micro_placements]
            y_coords = [p['y'] for p in micro_placements]
            
            ax.scatter(x_coords, y_coords, c=[color], alpha=0.7, s=30,
                     label=micro_name, edgecolors='black', linewidth=0.5)
        
        ax.set_xlabel('X Coordinate')
        ax.set_ylabel('Y Coordinate')
        ax.set_title(title)
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8)
        ax.set_aspect('equal', adjustable='box')
    
    def _plot_placement_with_analysis(self, ax, placements: List[Dict], title: str):
        """绘制带分析的布局图"""
        # 绘制基础布局
        self._plot_basic_placement(ax, placements, title)
        
        # 计算并绘制边界框
        all_x = [p['x'] for p in placements]
        all_y = [p['y'] for p in placements]
        
        min_x, max_x = min(all_x), max(all_x)
        min_y, max_y = min(all_y), max(all_y)
        
        # 绘制边界框
        bbox = patches.Rectangle((min_x, min_y), max_x-min_x, max_y-min_y,
                               linewidth=2, edgecolor='red', facecolor='none',
                               linestyle='--', alpha=0.8)
        ax.add_patch(bbox)
        
        # 绘制密度热力图
        x_coords = np.array(all_x)
        y_coords = np.array(all_y)
        
        # 创建2D直方图
        heatmap, xedges, yedges = np.histogram2d(x_coords, y_coords, bins=20)
        
        # 绘制热力图
        extent = [xedges[0], xedges[-1], yedges[0], yedges[-1]]
        im = ax.imshow(heatmap.T, extent=extent, origin='lower', 
                      cmap='YlOrRd', alpha=0.3, aspect='auto')
        
        # 添加颜色条
        plt.colorbar(im, ax=ax, label='Cell Density')
    
    def _calculate_placement_stats(self, placements: List[Dict]) -> Dict:
        """计算布局统计信息"""
        all_x = [p['x'] for p in placements]
        all_y = [p['y'] for p in placements]
        micros = set(p['micro'] for p in placements)
        
        min_x, max_x = min(all_x), max(all_x)
        min_y, max_y = min(all_y), max(all_y)
        
        bbox_width = max_x - min_x
        bbox_height = max_y - min_y
        area = bbox_width * bbox_height
        
        # 计算密度（假设每个 cell 占用 1x1 单位面积）
        density = len(placements) / area if area > 0 else 0
        
        return {
            'total_cells': len(placements),
            'total_micros': len(micros),
            'min_x': min_x,
            'max_x': max_x,
            'min_y': min_y,
            'max_y': max_y,
            'bbox_width': bbox_width,
            'bbox_height': bbox_height,
            'area': area,
            'density': density
        }
    
    def plot_micro_hierarchy(self, placements: List[Dict], 
                           output_file: str = "micro_hierarchy.png"):
        """绘制 micro 层次结构图"""
        
        # 分析层次结构
        hierarchy = {}
        for placement in placements:
            cell_path = placement['cell']
            micro_name = placement['micro']
            
            if micro_name not in hierarchy:
                hierarchy[micro_name] = set()
            
            # 解析层次路径
            parts = cell_path.split('/')
            if len(parts) > 1:
                # 有层次结构
                hierarchy[micro_name].add(tuple(parts))
            else:
                # 顶层 cell
                hierarchy[micro_name].add((micro_name, parts[0]))
        
        fig, ax = plt.subplots(1, 1, figsize=(14, 10))
        
        y_pos = 0
        micro_spacing = 2
        
        for micro_name, cell_paths in hierarchy.items():
            color = self._get_micro_color(micro_name)
            
            # 绘制 micro 节点
            ax.text(-1, y_pos, micro_name, fontsize=12, fontweight='bold',
                   bbox=dict(boxstyle="round,pad=0.5", fc=color, alpha=0.7),
                   ha='center', va='center')
            
            # 组织层次结构
            tree = {}
            for path in cell_paths:
                current = tree
                for part in path:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
            
            # 绘制层次树
            x_pos = 1
            self._plot_tree(ax, tree, x_pos, y_pos, color, micro_name)
            
            y_pos -= micro_spacing
        
        ax.set_xlim(-2, 20)
        ax.set_ylim(y_pos - 1, 1)
        ax.set_title('Micro Hierarchy Structure', fontsize=14, fontweight='bold')
        ax.axis('off')
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Hierarchy plot saved to: {output_file}")
        plt.show()
        
        return fig, ax
    
    def _plot_tree(self, ax, tree: Dict, x: float, y: float, color: Tuple, 
                  parent: str = None, level: int = 0):
        """递归绘制层次树"""
        for node, children in tree.items():
            # 绘制节点
            node_y = y - level * 0.3
            
            if children:  # 有子节点
                # 绘制矩形框
                ax.text(x, node_y, node, fontsize=10 - level,
                       bbox=dict(boxstyle="round,pad=0.3", fc=color, alpha=0.5),
                       ha='left', va='center')
            else:
                # 绘制叶节点
                ax.plot(x, node_y, 'o', color=color, markersize=8)
                ax.text(x + 0.1, node_y, node, fontsize=8, va='center')
            
            # 绘制连接线
            if parent:
                ax.plot([x - 1, x], [y - (level-1)*0.3, node_y], 
                       'gray', alpha=0.5, linewidth=1)
            
            # 递归绘制子节点
            if children:
                self._plot_tree(ax, children, x + 1.5, node_y, color, node, level + 1)

def load_placements_from_tcl(tcl_file: str) -> List[Dict]:
    """从 TCL 文件加载布局数据"""
    placements = []
    
    with open(tcl_file, 'r') as f:
        lines = f.readlines()
    
    for line in lines:
        line = line.strip()
        if line.startswith('set_attribute') and 'origin' in line:
            # 解析 set_attribute 命令
            try:
                parts = line.split()
                cell_name = parts[1]
                origin_data = line.split('{')[1].split('}')[0]
                x, y = map(float, origin_data.split())
                
                # 从 cell 名称推断 micro
                if '/' in cell_name:
                    micro_name = cell_name.split('/')[0]
                else:
                    micro_name = 'unknown'
                
                placements.append({
                    'cell': cell_name,
                    'x': x,
                    'y': y,
                    'micro': micro_name
                })
            except (IndexError, ValueError) as e:
                print(f"Warning: Could not parse line: {line}")
                continue
    
    return placements

def load_placements_from_json(json_file: str) -> List[Dict]:
    """从 JSON 文件加载布局数据"""
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    placements = []
    
    if 'global_placements' in data:
        # 引擎导出的格式
        placements = data['global_placements']
    elif isinstance(data, list):
        # 简单的 placements 列表
        placements = data
    
    return placements

def demo_visualization():
    """演示可视化功能"""
    
    # 创建示例数据
    sample_placements = [
        {"cell": "MACRO_LEFT/INPUT_PAD", "x": 0.0, "y": 0.0, "micro": "MACRO_LEFT"},
        {"cell": "MACRO_LEFT/BUFFER_CHAIN_1/BUF1", "x": 1.0, "y": 0.0, "micro": "MACRO_LEFT"},
        {"cell": "MACRO_LEFT/BUFFER_CHAIN_1/BUF2", "x": 2.0, "y": 0.0, "micro": "MACRO_LEFT"},
        {"cell": "MACRO_LEFT/BUFFER_CHAIN_1/BUF3", "x": 3.0, "y": 0.0, "micro": "MACRO_LEFT"},
        {"cell": "MACRO_LEFT/INVERTER_PAIR_1/INV1", "x": 2.0, "y": 1.0, "micro": "MACRO_LEFT"},
        {"cell": "MACRO_LEFT/INVERTER_PAIR_1/INV2", "x": 3.0, "y": 1.0, "micro": "MACRO_LEFT"},
        {"cell": "MACRO_LEFT/OUTPUT_PAD", "x": 5.0, "y": 0.0, "micro": "MACRO_LEFT"},
        
        {"cell": "MACRO_RIGHT/INPUT_PAD", "x": 10.0, "y": 0.0, "micro": "MACRO_RIGHT"},
        {"cell": "MACRO_RIGHT/BUFFER_CHAIN_1/BUF1", "x": 11.0, "y": 0.0, "micro": "MACRO_RIGHT"},
        {"cell": "MACRO_RIGHT/BUFFER_CHAIN_1/BUF2", "x": 12.0, "y": 0.0, "micro": "MACRO_RIGHT"},
        {"cell": "MACRO_RIGHT/BUFFER_CHAIN_1/BUF3", "x": 13.0, "y": 0.0, "micro": "MACRO_RIGHT"},
        {"cell": "MACRO_RIGHT/INVERTER_PAIR_1/INV1", "x": 12.0, "y": 1.0, "micro": "MACRO_RIGHT"},
        {"cell": "MACRO_RIGHT/INVERTER_PAIR_1/INV2", "x": 13.0, "y": 1.0, "micro": "MACRO_RIGHT"},
        {"cell": "MACRO_RIGHT/OUTPUT_PAD", "x": 15.0, "y": 0.0, "micro": "MACRO_RIGHT"},
        
        {"cell": "POWER_ISLAND/U1", "x": 6.0, "y": 3.0, "micro": "POWER_ISLAND"},
        {"cell": "POWER_ISLAND/U2", "x": 7.0, "y": 3.0, "micro": "POWER_ISLAND"},
        {"cell": "POWER_ISLAND/U3", "x": 6.0, "y": 4.0, "micro": "POWER_ISLAND"},
        {"cell": "POWER_ISLAND/U4", "x": 7.0, "y": 4.0, "micro": "POWER_ISLAND"},
    ]
    
    # 创建可视化器
    viz = PlacementVisualizer()
    
    # 1. 生成基础布局图
    print("Generating basic placement plot...")
    viz.plot_placement(sample_placements, "basic_placement.png", 
                      title="Sample Cell Placement")
    
    # 2. 生成增强布局图
    print("Generating enhanced placement plot...")
    viz.plot_placement_with_bbox(sample_placements, "enhanced_placement.png")
    
    # 3. 生成层次结构图
    print("Generating hierarchy plot...")
    viz.plot_micro_hierarchy(sample_placements, "micro_hierarchy.png")
    
    # 4. 显示统计信息
    stats = viz._calculate_placement_stats(sample_placements)
    print("\n=== Placement Statistics ===")
    for key, value in stats.items():
        print(f"{key}: {value}")

# 使用示例
if __name__ == "__main__":
    # 方法1: 使用示例数据
    demo_visualization()
    
    # 方法2: 从 TCL 文件加载数据
    # placements = load_placements_from_tcl("place_cell.tcl")
    # viz = PlacementVisualizer()
    # viz.plot_placement(placements, "from_tcl_placement.png")
    
    # 方法3: 从 JSON 文件加载数据  
    # placements = load_placements_from_json("placement_data.json")
    # viz = PlacementVisualizer()
    # viz.plot_placement(placements, "from_json_placement.png")