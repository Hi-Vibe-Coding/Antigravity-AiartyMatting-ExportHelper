"""
Exclusive Data Table Widget (Module 2 Right Box)
Displays analysis results matching Module 1 items against Module 2's source folder.
Shows status: '已匹配' vs '无法找到' with high-contrast colors and tooltips.
"""
import os
import subprocess
from pathlib import Path
from typing import List

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QBrush, QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QHeaderView, QTableWidgetItem
)
from qfluentwidgets import (
    TableWidget, SubtitleLabel, CaptionLabel, PushButton, PrimaryPushButton, FluentIcon,
    CheckBox, isDarkTheme, IndeterminateProgressBar, ProgressBar
)

from src.core.tracer import LogicalTraceItem
from src.core.logger import logger


class TraceResultTableWidget(QWidget):
    """
    模块2右侧：对照数据表
    """
    copy_requested = Signal()  # 触发“开始复制”操作信号
    def __init__(self, parent=None):
        super().__init__(parent)
        self.trace_items: List[LogicalTraceItem] = []

        self._init_ui()
        self.update_theme(isDarkTheme())

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        # 头部标题与统计
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        self.title = SubtitleLabel("对照数据表", self)
        self.title.setStyleSheet("font-size: 15px; font-weight: 600;")
        header_layout.addWidget(self.title)

        self.count_label = CaptionLabel("(0 项)", self)
        header_layout.addWidget(self.count_label)

        # 需求：添加勾选框“先删除同名图片文件”（默认不勾选）
        self.delete_existing_checkbox = CheckBox("先删除同名图片文件", self)
        self.delete_existing_checkbox.setChecked(False)
        self.delete_existing_checkbox.setToolTip("勾选后，复制写入新图片前，将先清理目标同名文件夹中该名称的所有格式旧图片（如 .png/.jpg/.jpeg/.webp）")
        self.delete_existing_checkbox.stateChanged.connect(self._on_delete_option_changed)
        header_layout.addWidget(self.delete_existing_checkbox)

        header_layout.addStretch()

        self.rule_tip = CaptionLabel("状态匹配: 在目标源文件夹下查找同名逻辑父文件夹", self)
        header_layout.addWidget(self.rule_tip)

        layout.addLayout(header_layout)

        # 进度指示器
        self.progress_bar = IndeterminateProgressBar(self)
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        # 对照数据表格（5列：序号、原文件、预期重命名、状态、跳转）
        self.table = TableWidget(self)
        self.table.setColumnCount(5)
        headers = [
            "序号", "原文件", "预期重命名", "状态", "跳转"
        ]
        self.table.setHorizontalHeaderLabels(headers)
        self.table.verticalHeader().hide()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectRightClickedRow(True)

        # 对齐方式
        self.table.horizontalHeaderItem(0).setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.horizontalHeaderItem(1).setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.table.horizontalHeaderItem(2).setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.table.horizontalHeaderItem(3).setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.table.horizontalHeaderItem(4).setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        # 列宽模式
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)          # 序号
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)        # 原文件
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)    # 预期重命名
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)        # 状态
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)          # 跳转

        self.table.setColumnWidth(0, 52)
        self.table.setColumnWidth(2, 170)
        self.table.setColumnWidth(4, 100)

        layout.addWidget(self.table, stretch=1)

        # 空状态提示
        self.empty_label = QLabel(
            "暂无分析数据\n请在左侧拖入「源文件夹」并点击【开始分析】\n系统将自动校验每个逻辑父文件夹并计算写入目标",
            self
        )
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.empty_label)

        # 底部状态栏
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(12)

        self.status_label = CaptionLabel("等待分析指令...", self)
        bottom_layout.addWidget(self.status_label, stretch=1)

        # 复制进度条（复制进行中时显示百分比进度）
        self.copy_progress_bar = ProgressBar(self)
        self.copy_progress_bar.setFixedHeight(8)
        self.copy_progress_bar.setFixedWidth(160)
        self.copy_progress_bar.hide()
        bottom_layout.addWidget(self.copy_progress_bar)

        self.clear_btn = PushButton(FluentIcon.DELETE, "清空列表", self)
        self.clear_btn.setFixedHeight(32)
        self.clear_btn.clicked.connect(self.clear_results)
        self.clear_btn.setEnabled(False)
        bottom_layout.addWidget(self.clear_btn)

        # 需求：右下角添加按钮“开始复制”
        self.copy_btn = PrimaryPushButton(FluentIcon.SAVE_COPY, "开始复制", self)
        self.copy_btn.setFixedHeight(32)
        self.copy_btn.clicked.connect(self.copy_requested.emit)
        self.copy_btn.setEnabled(False)
        bottom_layout.addWidget(self.copy_btn)

        layout.addLayout(bottom_layout)

        self._update_view()

    def set_results(self, items: List[LogicalTraceItem]):
        self.trace_items = items
        self._refresh_table()

    def _on_delete_option_changed(self):
        """勾选或取消'先删除同名图片文件'时，动态更新各行状态展示与底部统计"""
        self._refresh_table()

    def _open_target_folder(self, folder_path: Path):
        """兼容保留：在 Windows 资源管理器中打开目标文件夹"""
        if not folder_path:
            return
        try:
            resolved = folder_path.resolve()
            if resolved.exists():
                norm_folder = os.path.normpath(str(resolved))
                os.startfile(norm_folder)
                logger.info(f"成功打开目标文件夹: {norm_folder}")
            else:
                logger.warning(f"目标文件夹不存在，无法打开: {resolved}")
        except Exception as e:
            logger.error(f"打开目标文件夹失败: {folder_path}, 错误: {e}")

    def _jump_to_target(self, item: LogicalTraceItem):
        """
        在 Windows 资源管理器中打开目标文件夹，并让目标图片文件被选中 (explorer.exe /select,"<file>")
        注意：
        1. 引号必须仅包裹路径本身，不能包裹 /select, 开关，否则 Windows explorer 会因无法解析而错误打开“我的文档”。
        2. 若目标物理文件尚未生成，直接以文件夹路径打开，避免 explorer 因找不到文件而回退到“我的文档”。
        """
        if not item or not item.matched_target_folder:
            return

        target_folder = item.matched_target_folder.resolve()
        dest_file = item.dest_file_path.resolve() if item.dest_file_path else None

        # 检查是否有真实存在的物理文件可供定位选中
        target_file_to_select = None
        if dest_file and dest_file.exists():
            target_file_to_select = dest_file
        elif item.existing_same_stem_files:
            for old_file in item.existing_same_stem_files:
                if old_file and old_file.exists():
                    target_file_to_select = old_file.resolve()
                    break

        if target_file_to_select:
            try:
                # 规范化反斜杠，并构造原生无误的命令字符串
                norm_file = os.path.normpath(str(target_file_to_select))
                cmd = f'explorer.exe /select,"{norm_file}"'
                subprocess.Popen(cmd)
                logger.info(f"成功打开目标文件夹并选中目标文件: {norm_file}")
                return
            except Exception as e:
                logger.error(f"使用 explorer /select 打开文件失败: {target_file_to_select}, 错误: {e}")

        # 若目标物理文件尚未写入生成，直接在资源管理器中打开目标逻辑父文件夹
        try:
            if target_folder.exists():
                norm_folder = os.path.normpath(str(target_folder))
                os.startfile(norm_folder)
                logger.info(f"目标文件尚未物理生成，成功打开目标所在文件夹: {norm_folder}")
            else:
                logger.warning(f"目标文件夹不存在，无法打开: {target_folder}")
        except Exception as e:
            logger.error(f"打开目标文件夹失败: {target_folder}, 错误: {e}")
            try:
                norm_folder = os.path.normpath(str(target_folder))
                subprocess.Popen(f'explorer.exe "{norm_folder}"')
            except Exception:
                pass

    def _refresh_table(self):
        self.table.setRowCount(0)
        is_dark = isDarkTheme()

        # 调色板定义
        text_color = QColor("#ffffff" if is_dark else "#1a1a1a")
        accent_blue = QColor("#60cdff" if is_dark else "#0078d4")
        success_green = QColor("#52c41a" if is_dark else "#237804")
        warning_orange = QColor("#fa8c16" if is_dark else "#d46b08")  # 警示橙色（覆盖警告/同名不唯一/删除旧文件提示）
        vivid_red = QColor("#ff4d4f" if is_dark else "#e81123")       # 错误大红色
        muted_color = QColor("#8c8c8c" if is_dark else "#8c8c8c")

        delete_checked = self.delete_existing_checkbox.isChecked()

        for row, item in enumerate(self.trace_items):
            self.table.insertRow(row)

            # 0. 序号 (居中)
            item_idx = QTableWidgetItem(str(row + 1))
            item_idx.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_idx.setForeground(QBrush(text_color))
            self.table.setItem(row, 0, item_idx)

            # 1. 原文件 (左对齐，显示原文件名)
            item_orig = QTableWidgetItem(item.raw_file_display)
            item_orig.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            item_orig.setForeground(QBrush(text_color))
            if item.full_source_file:
                item_orig.setToolTip(f"原文件完整物理路径：\n{item.full_source_file}")
            self.table.setItem(row, 1, item_orig)

            # 2. 预期重命名 (左对齐，加粗)
            item_expected = QTableWidgetItem(item.expected_rename)
            item_expected.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            item_expected.setForeground(QBrush(text_color))
            f = item_expected.font()
            f.setBold(True)
            item_expected.setFont(f)
            self.table.setItem(row, 2, item_expected)

            # 动态计算未复制完成项的状态文本
            if not item.is_copied and item.matched_target_folder:
                if delete_checked:
                    if item.existing_same_stem_files:
                        del_names = "、".join(f.name for f in item.existing_same_stem_files)
                        item.status_display = f"即将被写入到[{item.dest_folder_display}]，原文件夹的{del_names}会被删除"
                        item.status_type = "override"
                    else:
                        item.status_display = f"即将被写入到[{item.dest_folder_display}]"
                        item.status_type = "normal"
                else:
                    if item.dest_file_path and item.dest_file_path.exists():
                        item.status_display = f"即将被写入到[{item.dest_folder_display}](同名文件将覆盖!)"
                        item.status_type = "override"
                    else:
                        item.status_display = f"即将被写入到[{item.dest_folder_display}]"
                        item.status_type = "normal"

            # 3. 状态 (原生文本呈现并高亮)
            status_item = QTableWidgetItem(item.status_display)
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            f_status = status_item.font()
            f_status.setBold(True)
            status_item.setFont(f_status)

            if item.status_type == "normal":
                # 即将被写入到[XXXX]
                status_item.setForeground(QBrush(success_green))
                if item.dest_file_path:
                    status_item.setToolTip(f"目标完整路径：\n{item.dest_file_path}")
            elif item.status_type == "override":
                # 即将被写入到[XXXX](同名文件将覆盖!) 或 提示先删除同名文件
                status_item.setForeground(QBrush(warning_orange))
                if item.dest_file_path:
                    if delete_checked and item.existing_same_stem_files:
                        del_names = "、".join(f.name for f in item.existing_same_stem_files)
                        status_item.setToolTip(f"[注意] 复制前将先物理删除目标文件夹中的同名旧图片：{del_names}\n目标写入完整路径：\n{item.dest_file_path}")
                    else:
                        status_item.setToolTip(f"[注意] 该目标路径下已存在同名图片文件，继续操作将被覆盖：\n{item.dest_file_path}")
            elif item.status_display == "同名文件夹不唯一":
                status_item.setForeground(QBrush(warning_orange))
                cand_str = "\n".join(str(p) for p in (item.candidate_folders or []))
                status_item.setToolTip(f"[冲突] 源文件夹下存在多个名为「{item.logical_parent}」的子文件夹：\n{cand_str}")
            else:
                # 无法找到 或 源文件不存在
                status_item.setForeground(QBrush(vivid_red))
                status_item.setToolTip(f"在源文件夹中未找到名为「{item.logical_parent}」的文件夹！")

            self.table.setItem(row, 3, status_item)

            # 4. 跳转 (操作按钮：点击在 Windows 资源管理器中打开目标文件夹)
            cell_widget = QWidget(self.table)
            cell_layout = QHBoxLayout(cell_widget)
            cell_layout.setContentsMargins(2, 2, 2, 2)
            cell_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            jump_btn = PushButton(FluentIcon.FOLDER, "跳转", cell_widget)
            jump_btn.setFixedSize(80, 28)
            jump_btn.setCursor(Qt.CursorShape.PointingHandCursor)

            if item.matched_target_folder and item.matched_target_folder.exists():
                target_item = item
                jump_btn.clicked.connect(lambda _, it=target_item: self._jump_to_target(it))
                if item.dest_file_path:
                    jump_btn.setToolTip(f"点击在资源管理器中打开并选中目标图片文件：\n{item.dest_file_path}")
                else:
                    jump_btn.setToolTip(f"点击在资源管理器中打开目标文件夹：\n{item.matched_target_folder}")
            else:
                jump_btn.setEnabled(False)
                jump_btn.setToolTip("未匹配到有效目标文件夹")

            cell_layout.addWidget(jump_btn)
            self.table.setCellWidget(row, 4, cell_widget)

        self._update_view()

    def clear_results(self):
        self.trace_items.clear()
        self.table.setRowCount(0)
        self.status_label.setText("列表已清空")
        self._update_view()

    def set_copying_state(self, is_copying: bool):
        """设置复制状态与进度控件展现"""
        if is_copying:
            self.copy_progress_bar.setValue(0)
            self.copy_progress_bar.show()
            self.copy_btn.setEnabled(False)
            self.clear_btn.setEnabled(False)
        else:
            self.copy_progress_bar.hide()
            self.clear_btn.setEnabled(True)
            self._update_view()

    def update_copy_progress(self, current: int, total: int, filename: str):
        """实时更新复制进度"""
        if total > 0:
            val = int(current / total * 100)
            self.copy_progress_bar.setValue(val)
        self.status_label.setText(f"正在复制 ({current}/{total}): {filename}")

    def update_copy_finished(self, success_count: int, fail_count: int, items: List[LogicalTraceItem]):
        """复制完成"""
        self.set_copying_state(False)
        self.set_results(items)
        self.status_label.setText(f"复制完成：成功传输 {success_count} 项，失败 {fail_count} 项")

    def _update_view(self):
        total = len(self.trace_items)
        # 统计尚未复制的待写入项
        pending_normal = sum(1 for it in self.trace_items if it.status_type == "normal" and not it.is_copied)
        pending_override = sum(1 for it in self.trace_items if it.status_type == "override" and not it.is_copied)
        copied_count = sum(1 for it in self.trace_items if it.is_copied)
        ambiguous_count = sum(1 for it in self.trace_items if it.status_display == "同名文件夹不唯一")
        not_found_count = sum(1 for it in self.trace_items if it.status_display == "无法找到")

        # 检查是否还有未复制的有效待写入项
        can_copy = (pending_normal + pending_override) > 0

        if total > 0:
            count_parts = []
            if copied_count > 0:
                count_parts.append(f"已写入: {copied_count}")
            if pending_normal > 0:
                count_parts.append(f"待写入: {pending_normal}")
            if pending_override > 0:
                count_parts.append(f"将覆盖: {pending_override}")
            if ambiguous_count > 0:
                count_parts.append(f"同名不唯一: {ambiguous_count}")
            if not_found_count > 0:
                count_parts.append(f"无法找到: {not_found_count}")

            self.count_label.setText(f"(共 {total} 项 · " + " · ".join(count_parts) + ")")
            if copied_count > 0 and not can_copy:
                self.status_label.setText(f"所有有效项已全部成功复制写入（共 {copied_count} 项）")
            else:
                self.status_label.setText(
                    f"分析完成：共检索 {total} 条数据，{pending_normal} 项待写入，{pending_override} 项将覆盖，{copied_count} 项已写入"
                )
        else:
            self.count_label.setText("(0 项)")

        has_items = total > 0
        self.table.setVisible(has_items)
        self.empty_label.setVisible(not has_items)
        self.clear_btn.setEnabled(has_items)

        # 需求：如果已经成功执行了“开始复制”，则按钮置灰（不可点击）
        self.copy_btn.setEnabled(can_copy)
        if can_copy:
            self.copy_btn.setText(f"开始复制 ({pending_normal + pending_override})")
        elif copied_count > 0:
            self.copy_btn.setText("已全部复制")
        else:
            self.copy_btn.setText("开始复制")

    def update_theme(self, is_dark: bool):
        if is_dark:
            self.count_label.setStyleSheet("color: rgba(255, 255, 255, 0.65); font-weight: 500;")
            self.rule_tip.setStyleSheet("color: rgba(255, 255, 255, 0.60);")
            self.empty_label.setStyleSheet("color: rgba(255, 255, 255, 0.55); font-size: 14px; line-height: 1.6;")
            self.table.setStyleSheet("""
                QTableView {
                    background-color: transparent;
                    color: #ffffff;
                    gridline-color: rgba(255, 255, 255, 0.08);
                }
                QTableView::item {
                    padding: 4px 8px;
                }
                QHeaderView::section {
                    color: rgba(255, 255, 255, 0.85);
                    background-color: rgba(255, 255, 255, 0.04);
                    font-weight: 600;
                    padding-left: 8px;
                    padding-right: 8px;
                }
            """)
        else:
            self.count_label.setStyleSheet("color: rgba(0, 0, 0, 0.60); font-weight: 500;")
            self.rule_tip.setStyleSheet("color: rgba(0, 0, 0, 0.55);")
            self.empty_label.setStyleSheet("color: rgba(0, 0, 0, 0.45); font-size: 14px; line-height: 1.6;")
            self.table.setStyleSheet("""
                QTableView {
                    background-color: transparent;
                    color: #1a1a1a;
                    gridline-color: rgba(0, 0, 0, 0.06);
                }
                QTableView::item {
                    padding: 4px 8px;
                }
                QHeaderView::section {
                    color: rgba(0, 0, 0, 0.75);
                    background-color: rgba(0, 0, 0, 0.02);
                    font-weight: 600;
                    padding-left: 8px;
                    padding-right: 8px;
                }
            """)
        self._refresh_table()
