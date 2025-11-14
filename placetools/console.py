#!/usr/bin/env python3
"""
Place Cell Engine Console Interface
提供交互式命令行界面来操作布局引擎
"""

import os
import sys
import cmd
import shlex
import readline
from typing import List, Dict, Tuple, Optional

# 添加引擎模块路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from place_engine import PlaceCellEngine, Micro, Cell, SiteInfo, Orientation

class PlaceEngineConsole(cmd.Cmd):
    """Place Cell Engine 控制台界面"""
    
    intro = """
╔══════════════════════════════════════════════════════════════╗
║                 Place Cell Engine Console                   ║
║                布局引擎交互式控制台界面                    ║
╚══════════════════════════════════════════════════════════════╝

输入 'help' 或 '?' 查看可用命令
输入 'exit' 或 'quit' 退出程序

"""
    prompt = '(place_engine) > '
    
    # 命令补全数据
    COMMANDS = [
        'site_info', 'create_micro', 'create_cell', 'place_micro', 'place_micro_grid',
        'move_micro', 'list_micros', 'show_micro', 'hierarchy', 'add_submicro',
        'save_micro', 'load_micro', 'list_library', 'generate_tcl', 'stats',
        'remove_micro', 'save_config', 'load_config', 'demo', 'clear', 'exit', 'quit', 'help'
    ]
    
    ORIENTATIONS = ['N', 'S', 'FN', 'FS']
    
    def __init__(self):
        super().__init__()
        self.engine = None
        self._initialize_engine()
        self._setup_readline()
    
    def _setup_readline(self):
        """设置 readline 自动补全"""
        try:
            # 在 macOS 和 Linux 上设置 tab 补全
            readline.set_completer_delims(' \t\n`~!@#$%^&*()-=+[{]}\\|;:\'",<>?')
            readline.parse_and_bind("tab: complete")
            readline.set_completer(self.complete)
        except ImportError:
            # Windows 系统可能没有 readline
            try:
                import pyreadline3 as readline
                readline.set_completer_delims(' \t\n`~!@#$%^&*()-=+[{]}\\|;:\'",<>?')
                readline.parse_and_bind("tab: complete")
                readline.set_completer(self.complete)
            except ImportError:
                print("注意: 该系统不支持 Tab 自动补全")
    
    def _initialize_engine(self):
        """初始化引擎"""
        try:
            # 使用默认 site 信息初始化引擎
            site_info = SiteInfo(width=0.14, height=0.9)
            self.engine = PlaceCellEngine(site_info=site_info)
            print("✓ 引擎初始化成功")
            print(f"✓ Site 信息: 宽度={site_info.width}μm, 高度={site_info.height}μm")
        except Exception as e:
            print(f"✗ 引擎初始化失败: {e}")
            self.engine = PlaceCellEngine()
    
    def complete(self, text, state):
        """通用的自动补全函数"""
        if state == 0:
            # 第一次调用，生成补全列表
            line = readline.get_line_buffer()
            words = line.split()
            
            if not words:
                self.matches = [cmd for cmd in self.COMMANDS if cmd.startswith(text)]
            else:
                cmd = words[0]
                if len(words) == 1 and not line.endswith(' '):
                    # 命令补全
                    self.matches = [cmd for cmd in self.COMMANDS if cmd.startswith(text)]
                else:
                    # 参数补全
                    self.matches = self._complete_args(cmd, words, text)
            
            # 如果没有匹配项，返回 None
            if not self.matches:
                self.matches = [None]
        
        try:
            return self.matches[state]
        except IndexError:
            return None
    
    def _complete_args(self, cmd, words, text):
        """根据命令补全参数"""
        arg_index = len(words) - 1
        if text:  # 如果正在输入文本，arg_index 需要调整
            arg_index = len(words) - 2 if words[-1] == text else len(words) - 1
        
        # 获取可用的 micro 名称
        micro_names = self.engine.list_active_micros()
        library_micros = self.engine.library.list_available_micros()
        
        if cmd == 'create_micro':
            if arg_index == 0:
                return []  # 第一个参数是 micro 名称，没有补全
            elif arg_index in [1, 2]:
                return self._complete_number(text)
        
        elif cmd == 'create_cell':
            if arg_index == 0:
                return [name for name in micro_names if name.startswith(text)]
            elif arg_index == 1:
                return []  # cell 名称，没有补全
            elif arg_index in [2, 3, 4, 5]:
                return self._complete_number(text)
            elif arg_index == 6:
                return [orient for orient in self.ORIENTATIONS if orient.startswith(text)]
        
        elif cmd in ['place_micro', 'move_micro']:
            if arg_index == 0:
                return [name for name in micro_names if name.startswith(text)]
            elif arg_index in [1, 2]:
                return self._complete_number(text)
        
        elif cmd == 'place_micro_grid':
            if arg_index == 0:
                return [name for name in micro_names if name.startswith(text)]
            elif arg_index in [1, 2]:
                return self._complete_number(text, integer=True)
        
        elif cmd in ['show_micro', 'remove_micro', 'save_micro']:
            if arg_index == 0:
                return [name for name in micro_names if name.startswith(text)]
        
        elif cmd == 'add_submicro':
            if arg_index == 0:
                return [name for name in micro_names if name.startswith(text)]
            elif arg_index == 1:
                return [name for name in micro_names if name.startswith(text)]
            elif arg_index in [2, 3]:
                return self._complete_number(text)
        
        elif cmd == 'load_micro':
            if arg_index == 0:
                return [name for name in library_micros if name.startswith(text)]
            elif arg_index == 1:
                return []  # 实例名称，没有补全
        
        elif cmd == 'hierarchy':
            if arg_index == 0:
                return [name for name in micro_names if name.startswith(text)]
        
        elif cmd in ['generate_tcl', 'save_config', 'load_config']:
            if arg_index == 0:
                return self._complete_filename(text)
        
        return []
    
    def _complete_number(self, text, integer=False):
        """补全数字参数"""
        if not text:
            return ['0.0'] if not integer else ['0']
        try:
            if integer:
                int(text)
            else:
                float(text)
            return [text]
        except ValueError:
            return []
    
    def _complete_filename(self, text):
        """补全文件名"""
        if not text:
            text = ''
        
        # 获取当前目录的文件
        files = []
        for f in os.listdir('.'):
            if f.startswith(text):
                if os.path.isdir(f):
                    files.append(f + '/')
                else:
                    files.append(f)
        
        return files
    
    # 原有的命令方法保持不变，这里只展示几个关键方法的补全实现
    
    def complete_create_micro(self, text, line, begidx, endidx):
        """create_micro 命令的自动补全"""
        return self._complete_generic(text, line)
    
    def complete_create_cell(self, text, line, begidx, endidx):
        """create_cell 命令的自动补全"""
        return self._complete_generic(text, line)
    
    def complete_place_micro(self, text, line, begidx, endidx):
        """place_micro 命令的自动补全"""
        return self._complete_generic(text, line)
    
    def complete_place_micro_grid(self, text, line, begidx, endidx):
        """place_micro_grid 命令的自动补全"""
        return self._complete_generic(text, line)
    
    def complete_move_micro(self, text, line, begidx, endidx):
        """move_micro 命令的自动补全"""
        return self._complete_generic(text, line)
    
    def complete_show_micro(self, text, line, begidx, endidx):
        """show_micro 命令的自动补全"""
        return self._complete_generic(text, line)
    
    def complete_remove_micro(self, text, line, begidx, endidx):
        """remove_micro 命令的自动补全"""
        return self._complete_generic(text, line)
    
    def complete_add_submicro(self, text, line, begidx, endidx):
        """add_submicro 命令的自动补全"""
        return self._complete_generic(text, line)
    
    def complete_load_micro(self, text, line, begidx, endidx):
        """load_micro 命令的自动补全"""
        return self._complete_generic(text, line)
    
    def complete_hierarchy(self, text, line, begidx, endidx):
        """hierarchy 命令的自动补全"""
        return self._complete_generic(text, line)
    
    def complete_generate_tcl(self, text, line, begidx, endidx):
        """generate_tcl 命令的自动补全"""
        return self._complete_generic(text, line)
    
    def complete_save_config(self, text, line, begidx, endidx):
        """save_config 命令的自动补全"""
        return self._complete_generic(text, line)
    
    def complete_load_config(self, text, line, begidx, endidx):
        """load_config 命令的自动补全"""
        return self._complete_generic(text, line)
    
    def _complete_generic(self, text, line):
        """通用的补全方法"""
        words = line.split()
        if not words:
            return []
        
        cmd = words[0]
        arg_index = len(words) - 1
        if text:  # 如果正在输入文本，arg_index 需要调整
            arg_index = len(words) - 2 if words[-1] == text else len(words) - 1
        
        # 调用主要的补全逻辑
        matches = self._complete_args(cmd, words, text)
        return matches

    # 原有的命令实现保持不变
    def do_site_info(self, arg):
        """
        显示或设置 site 信息
        用法: site_info [width height]
        示例: 
          site_info              # 显示当前 site 信息
          site_info 0.14 0.9     # 设置 site 尺寸
        """
        args = shlex.split(arg)
        if not args:
            # 显示当前 site 信息
            site = self.engine.site_info
            print(f"当前 Site 信息:")
            print(f"  宽度: {site.width} μm")
            print(f"  高度: {site.height} μm")
            print(f"  Grid: {site.to_grid_coords(1.0, 1.0)} sites/μm")
        else:
            # 设置 site 信息
            if len(args) != 2:
                print("错误: 需要提供宽度和高度两个参数")
                return
            
            try:
                width = float(args[0])
                height = float(args[1])
                self.engine.site_info = SiteInfo(width=width, height=height)
                print(f"✓ Site 信息已更新: 宽度={width}μm, 高度={height}μm")
            except ValueError:
                print("错误: 宽度和高度必须是数字")
    
    def do_create_micro(self, arg):
        """
        创建新的 micro
        用法: create_micro <name> [x y [description]]
        示例:
          create_micro MACRO1
          create_micro MACRO2 10.0 5.0 "测试宏模块"
        """
        args = shlex.split(arg)
        if not args:
            print("错误: 需要提供 micro 名称")
            return
        
        name = args[0]
        x = float(args[1]) if len(args) > 1 else 0.0
        y = float(args[2]) if len(args) > 2 else 0.0
        description = args[3] if len(args) > 3 else ""
        
        try:
            micro = self.engine.create_micro(name, x, y, description)
            grid_x, grid_y = micro.grid_x, micro.grid_y
            print(f"✓ Micro '{name}' 创建成功")
            print(f"  位置: ({x}, {y})")
            print(f"  Grid: ({grid_x}, {grid_y})")
            if description:
                print(f"  描述: {description}")
        except Exception as e:
            print(f"✗ 创建 micro 失败: {e}")
    
    def do_create_cell(self, arg):
        """
        创建 cell 并添加到指定 micro
        用法: create_cell <micro_name> <cell_name> <x> <y> [width height orientation]
        示例:
          create_cell MACRO1 CELL1 0.0 0.0
          create_cell MACRO1 CELL2 0.14 0.0 0.14 0.9 N
        """
        args = shlex.split(arg)
        if len(args) < 4:
            print("错误: 需要提供 micro名称, cell名称, x坐标, y坐标")
            return
        
        micro_name = args[0]
        cell_name = args[1]
        x = float(args[2])
        y = float(args[3])
        width = float(args[4]) if len(args) > 4 else 0.14
        height = float(args[5]) if len(args) > 5 else 0.9
        orientation = Orientation(args[6]) if len(args) > 6 else Orientation.N
        
        micro = self.engine.get_micro(micro_name)
        if not micro:
            print(f"错误: Micro '{micro_name}' 不存在")
            return
        
        try:
            cell = Cell(cell_name, x, y, orientation, width, height)
            micro.add_cell(cell)
            grid_x, grid_y = cell.grid_x, cell.grid_y
            print(f"✓ Cell '{cell_name}' 添加到 micro '{micro_name}'")
            print(f"  相对位置: ({x}, {y})")
            print(f"  绝对位置: ({cell.absolute_x}, {cell.absolute_y})")
            print(f"  Grid: ({grid_x}, {grid_y})")
            print(f"  尺寸: {width} x {height}")
            print(f"  方向: {orientation.value}")
        except Exception as e:
            print(f"✗ 添加 cell 失败: {e}")
    
    def do_place_micro(self, arg):
        """
        放置 micro 到指定位置
        用法: place_micro <micro_name> <x> <y>
        示例:
          place_micro MACRO1 5.0 3.0
        """
        args = shlex.split(arg)
        if len(args) != 3:
            print("错误: 需要提供 micro名称, x坐标, y坐标")
            return
        
        micro_name = args[0]
        x = float(args[1])
        y = float(args[2])
        
        try:
            self.engine.place_micro(micro_name, x, y)
            micro = self.engine.get_micro(micro_name)
            grid_x, grid_y = micro.grid_x, micro.grid_y
            print(f"✓ Micro '{micro_name}' 已放置到位置 ({x}, {y})")
            print(f"  Grid 坐标: ({grid_x}, {grid_y})")
        except Exception as e:
            print(f"✗ 放置 micro 失败: {e}")
    
    def do_place_micro_grid(self, arg):
        """
        使用 grid 坐标放置 micro
        用法: place_micro_grid <micro_name> <grid_x> <grid_y>
        示例:
          place_micro_grid MACRO1 5 3
        """
        args = shlex.split(arg)
        if len(args) != 3:
            print("错误: 需要提供 micro名称, grid_x, grid_y")
            return
        
        micro_name = args[0]
        grid_x = int(args[1])
        grid_y = int(args[2])
        
        try:
            self.engine.place_micro_by_grid(micro_name, grid_x, grid_y)
            micro = self.engine.get_micro(micro_name)
            x, y = micro.origin_x, micro.origin_y
            print(f"✓ Micro '{micro_name}' 已放置到 grid 位置 ({grid_x}, {grid_y})")
            print(f"  实际坐标: ({x}, {y})")
        except Exception as e:
            print(f"✗ 放置 micro 失败: {e}")
    
    def do_move_micro(self, arg):
        """
        移动 micro
        用法: move_micro <micro_name> <dx> <dy>
        示例:
          move_micro MACRO1 1.0 0.5
        """
        args = shlex.split(arg)
        if len(args) != 3:
            print("错误: 需要提供 micro名称, dx, dy")
            return
        
        micro_name = args[0]
        dx = float(args[1])
        dy = float(args[2])
        
        try:
            self.engine.move_micro(micro_name, dx, dy)
            micro = self.engine.get_micro(micro_name)
            x, y = micro.origin_x, micro.origin_y
            grid_x, grid_y = micro.grid_x, micro.grid_y
            print(f"✓ Micro '{micro_name}' 已移动")
            print(f"  新位置: ({x}, {y})")
            print(f"  新Grid: ({grid_x}, {grid_y})")
        except Exception as e:
            print(f"✗ 移动 micro 失败: {e}")
    
    def do_list_micros(self, arg):
        """
        列出所有活跃的 micro
        用法: list_micros
        """
        micros = self.engine.list_active_micros()
        if not micros:
            print("当前没有活跃的 micro")
            return
        
        print(f"活跃的 Micro ({len(micros)} 个):")
        for i, name in enumerate(micros, 1):
            micro = self.engine.get_micro(name)
            cells_count = len(micro.get_all_cells())
            sub_micros_count = len(micro.get_all_sub_micros())
            print(f"  {i}. {name}")
            print(f"     位置: ({micro.origin_x}, {micro.origin_y})")
            print(f"     Grid: ({micro.grid_x}, {micro.grid_y})")
            print(f"     Cells: {cells_count}, 子Micro: {sub_micros_count}")
            if micro.description:
                print(f"     描述: {micro.description}")
    
    def do_show_micro(self, arg):
        """
        显示指定 micro 的详细信息
        用法: show_micro <micro_name>
        示例: show_micro MACRO1
        """
        args = shlex.split(arg)
        if not args:
            print("错误: 需要提供 micro 名称")
            return
        
        micro_name = args[0]
        micro = self.engine.get_micro(micro_name)
        if not micro:
            print(f"错误: Micro '{micro_name}' 不存在")
            return
        
        print(f"Micro: {micro.name}")
        print(f"  路径: {micro.hierarchical_path}")
        print(f"  位置: ({micro.origin_x}, {micro.origin_y})")
        print(f"  Grid: ({micro.grid_x}, {micro.grid_y})")
        print(f"  描述: {micro.description}")
        
        # 显示 cells
        cells = micro.cells
        if cells:
            print(f"  Cells ({len(cells)} 个):")
            for i, cell in enumerate(cells, 1):
                placement_x, placement_y = cell.get_placement_origin()
                print(f"    {i}. {cell.name}")
                print(f"       存储位置: ({cell.x}, {cell.y})")
                print(f"       绝对位置: ({cell.absolute_x}, {cell.absolute_y})")
                print(f"       布局位置: ({placement_x}, {placement_y})")
                print(f"       Grid: ({cell.grid_x}, {cell.grid_y})")
                print(f"       尺寸: {cell.width} x {cell.height}")
                print(f"       方向: {cell.orientation.value}")
        
        # 显示子 micros
        sub_micros = micro.sub_micros
        if sub_micros:
            print(f"  子Micros ({len(sub_micros)} 个):")
            for i, sub_micro in enumerate(sub_micros, 1):
                print(f"    {i}. {sub_micro.name}")
                print(f"       相对位置: ({sub_micro.origin_x}, {sub_micro.origin_y})")
                print(f"       绝对位置: ({sub_micro.origin_x + micro.origin_x}, {sub_micro.origin_y + micro.origin_y})")
    
    def do_hierarchy(self, arg):
        """
        显示层次结构
        用法: hierarchy [micro_name]
        示例:
          hierarchy        # 显示所有 micro 的层次结构
          hierarchy MACRO1 # 显示指定 micro 的层次结构
        """
        args = shlex.split(arg)
        if not args:
            # 显示所有 micro 的层次结构
            self.engine.print_hierarchy()
        else:
            # 显示指定 micro 的层次结构
            micro_name = args[0]
            micro = self.engine.get_micro(micro_name)
            if micro:
                print(f"=== {micro_name} 的层次结构 ===")
                micro.print_hierarchy()
            else:
                print(f"错误: Micro '{micro_name}' 不存在")
    
    def do_add_submicro(self, arg):
        """
        添加子 micro
        用法: add_submicro <parent_micro> <child_micro> [x y]
        示例:
          add_submicro MAIN_MACRO BUFFER_CHAIN 1.0 0.0
        """
        args = shlex.split(arg)
        if len(args) < 2:
            print("错误: 需要提供父micro名称和子micro名称")
            return
        
        parent_name = args[0]
        child_name = args[1]
        x = float(args[2]) if len(args) > 2 else 0.0
        y = float(args[3]) if len(args) > 3 else 0.0
        
        parent = self.engine.get_micro(parent_name)
        child = self.engine.get_micro(child_name)
        
        if not parent:
            print(f"错误: 父Micro '{parent_name}' 不存在")
            return
        if not child:
            print(f"错误: 子Micro '{child_name}' 不存在")
            return
        
        try:
            # 创建子 micro 的副本
            child_copy = child.clone(f"{child_name}_INST")
            child_copy.set_origin(x, y)
            parent.add_sub_micro(child_copy)
            print(f"✓ 子Micro '{child_name}' 已添加到 '{parent_name}'")
            print(f"  相对位置: ({x}, {y})")
        except Exception as e:
            print(f"✗ 添加子micro失败: {e}")
    
    def do_save_micro(self, arg):
        """
        保存 micro 到库中
        用法: save_micro <micro_name>
        示例: save_micro MACRO1
        """
        args = shlex.split(arg)
        if not args:
            print("错误: 需要提供 micro 名称")
            return
        
        micro_name = args[0]
        try:
            self.engine.save_micro_to_library(micro_name)
            print(f"✓ Micro '{micro_name}' 已保存到库中")
        except Exception as e:
            print(f"✗ 保存 micro 失败: {e}")
    
    def do_load_micro(self, arg):
        """
        从库中加载 micro
        用法: load_micro <micro_name> [instance_name]
        示例:
          load_micro BUFFER_CHAIN
          load_micro BUFFER_CHAIN BUF_INST1
        """
        args = shlex.split(arg)
        if not args:
            print("错误: 需要提供 micro 名称")
            return
        
        micro_name = args[0]
        instance_name = args[1] if len(args) > 1 else micro_name
        
        try:
            micro = self.engine.load_micro_from_library(micro_name, instance_name)
            if micro:
                print(f"✓ Micro '{micro_name}' 已加载为 '{instance_name}'")
                print(f"  位置: ({micro.origin_x}, {micro.origin_y})")
            else:
                print(f"✗ Micro '{micro_name}' 在库中不存在")
        except Exception as e:
            print(f"✗ 加载 micro 失败: {e}")
    
    def do_list_library(self, arg):
        """
        列出库中所有可用的 micro
        用法: list_library
        """
        micros = self.engine.library.list_available_micros()
        if not micros:
            print("库中没有可用的 micro")
            return
        
        print(f"库中的 Micro ({len(micros)} 个):")
        for i, name in enumerate(micros, 1):
            print(f"  {i}. {name}")
    
    def do_generate_tcl(self, arg):
        """
        生成 TCL 布局脚本
        用法: generate_tcl [filename]
        示例:
          generate_tcl              # 使用默认文件名
          generate_tcl layout.tcl   # 指定文件名
        """
        args = shlex.split(arg)
        filename = args[0] if args else "place_cell.tcl"
        
        try:
            placements = self.engine.generate_tcl_script(filename)
            print(f"✓ TCL 脚本已生成: {filename}")
            print(f"  包含 {len(placements)} 个 cell 的布局信息")
        except Exception as e:
            print(f"✗ 生成 TCL 脚本失败: {e}")
    
    def do_stats(self, arg):
        """
        显示布局统计信息
        用法: stats
        """
        try:
            stats = self.engine.get_placement_statistics()
            print("=== 布局统计信息 ===")
            print(f"总 Cells 数量: {stats['total_cells']}")
            print(f"总 Micros 数量: {stats['total_micros']}")
            print(f"总子Micros数量: {stats['total_sub_micros']}")
            print(f"Site 信息: {stats['site_info']}")
            
            bbox = stats['bounding_box']
            print(f"边界框:")
            print(f"  最小: ({bbox['min_x']}, {bbox['min_y']})")
            print(f"  最大: ({bbox['max_x']}, {bbox['max_y']})")
            print(f"  尺寸: {bbox['width']} x {bbox['height']}")
            
            print("\nMicros 详细信息:")
            for name, info in stats['micros_info'].items():
                print(f"  {name}:")
                print(f"    Cells: {info['cells_count']}")
                print(f"    子Micros: {info['sub_micros_count']}")
                print(f"    位置: {info['origin']}")
                print(f"    Grid: {info['grid_origin']}")
                
        except Exception as e:
            print(f"✗ 获取统计信息失败: {e}")
    
    def do_remove_micro(self, arg):
        """
        移除 micro
        用法: remove_micro <micro_name>
        示例: remove_micro MACRO1
        """
        args = shlex.split(arg)
        if not args:
            print("错误: 需要提供 micro 名称")
            return
        
        micro_name = args[0]
        if self.engine.remove_micro(micro_name):
            print(f"✓ Micro '{micro_name}' 已移除")
        else:
            print(f"✗ Micro '{micro_name}' 不存在")
    
    def do_save_config(self, arg):
        """
        保存引擎配置到文件
        用法: save_config [filename]
        示例:
          save_config              # 使用默认文件名
          save_config config.json  # 指定文件名
        """
        args = shlex.split(arg)
        filename = args[0] if args else "engine_config.json"
        
        try:
            self.engine.save_configuration(filename)
            print(f"✓ 引擎配置已保存: {filename}")
        except Exception as e:
            print(f"✗ 保存配置失败: {e}")
    
    def do_load_config(self, arg):
        """
        从文件加载引擎配置
        用法: load_config [filename]
        示例:
          load_config              # 使用默认文件名
          load_config config.json  # 指定文件名
        """
        args = shlex.split(arg)
        filename = args[0] if args else "engine_config.json"
        
        try:
            self.engine.load_configuration(filename)
            print(f"✓ 引擎配置已加载: {filename}")
        except Exception as e:
            print(f"✗ 加载配置失败: {e}")
    
    def do_demo(self, arg):
        """
        运行演示示例
        用法: demo
        """
        try:
            from place_engine import demo_enhanced_micro
            print("正在运行演示示例...")
            demo_enhanced_micro()
            print("✓ 演示示例运行完成")
        except Exception as e:
            print(f"✗ 运行演示失败: {e}")
    
    def do_clear(self, arg):
        """
        清空所有 micro
        用法: clear
        """
        micro_names = list(self.engine.active_micros.keys())
        for name in micro_names:
            self.engine.remove_micro(name)
        print(f"✓ 已清空所有 micro ({len(micro_names)} 个)")
    
    def do_exit(self, arg):
        """退出程序"""
        print("感谢使用 Place Cell Engine!")
        return True
    
    def do_quit(self, arg):
        """退出程序"""
        return self.do_exit(arg)
    
    def emptyline(self):
        """空行时不执行任何操作"""
        pass
    
    def default(self, line):
        """处理未知命令"""
        print(f"未知命令: {line}")
        print("输入 'help' 查看可用命令")

def main():
    """主函数"""
    try:
        console = PlaceEngineConsole()
        console.cmdloop()
    except KeyboardInterrupt:
        print("\n\n程序被用户中断")
    except Exception as e:
        print(f"程序运行出错: {e}")

if __name__ == "__main__":
    main()