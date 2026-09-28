from __future__ import annotations

import threading
import sys
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from backend.review_engine import Finding, ReviewResult, SUPPORTED_SUFFIXES, review_paths


COLORS = {
    "app": "#0B0E12", "sidebar": "#10141A", "panel": "#141920", "panel_alt": "#181E26",
    "border": "#27303B", "text": "#F2F5F7", "muted": "#8D98A5", "accent": "#4BE0AE",
    "accent_hover": "#68E8BC", "accent_dark": "#123C31", "danger": "#FF6B6B",
    "warning": "#FFB454", "medium": "#F2D06B", "info": "#70B7FF",
}

SEVERITY_META = {
    "blocking": ("阻断", COLORS["danger"]), "high": ("高风险", COLORS["warning"]),
    "medium": ("需关注", COLORS["medium"]), "info": ("提示", COLORS["info"]),
}

SCENARIOS = {
    "competition": {
        "title": "大学生竞赛审查", "subtitle": "核对材料完整性、团队信息和跨文件一致性",
        "hint": "建议添加比赛通知、报名表、项目书和承诺书",
    },
    "contract": {
        "title": "合同审查", "subtitle": "检查付款比例、验收期限和关键条款风险",
        "hint": "建议添加合同正文、报价单、交付清单和内部规则",
    },
}


def resource_path(relative: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / relative


class MingJianApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("明鉴 · 材料审查工具")
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        window_width = min(1380, max(1120, screen_width - 64))
        window_height = min(860, max(700, screen_height - 80))
        position_x = max(0, (screen_width - window_width) // 2)
        position_y = max(0, (screen_height - window_height) // 2)
        self.geometry(f"{window_width}x{window_height}+{position_x}+{position_y}")
        self.minsize(min(1120, window_width), min(700, window_height))
        self.configure(fg_color=COLORS["app"])
        icon_path = resource_path("assets/mingjian.ico")
        if icon_path.exists():
            self.iconbitmap(str(icon_path))

        self.scenario = "competition"
        self.paths: list[Path] = []
        self.result: ReviewResult | None = None
        self.selected_finding: Finding | None = None
        self.resolved_ids: set[str] = set()
        self.scenario_buttons: dict[str, ctk.CTkButton] = {}

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._build_sidebar()
        self._build_main()
        self._render_files()
        self._set_scenario("competition")

    def _build_sidebar(self) -> None:
        sidebar = ctk.CTkFrame(self, width=238, corner_radius=0, fg_color=COLORS["sidebar"])
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)
        sidebar.grid_rowconfigure(8, weight=1)

        brand = ctk.CTkFrame(sidebar, fg_color="transparent")
        brand.grid(row=0, column=0, padx=24, pady=(26, 42), sticky="ew")
        brand.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(
            brand, text="明", width=38, height=38, corner_radius=9, fg_color=COLORS["accent"],
            text_color="#062018", font=("Microsoft YaHei UI", 18, "bold"),
        ).grid(row=0, column=0, rowspan=2, padx=(0, 12))
        ctk.CTkLabel(
            brand, text="明鉴", anchor="w", text_color=COLORS["text"],
            font=("Microsoft YaHei UI", 20, "bold"),
        ).grid(row=0, column=1, sticky="sw")
        ctk.CTkLabel(
            brand, text="MATERIAL REVIEW", anchor="w", text_color=COLORS["muted"], font=("Cascadia Mono", 9),
        ).grid(row=1, column=1, sticky="nw")

        ctk.CTkLabel(
            sidebar, text="审查场景", anchor="w", text_color="#66717D",
            font=("Microsoft YaHei UI", 11, "bold"),
        ).grid(row=1, column=0, padx=25, pady=(0, 10), sticky="ew")
        for row, (scenario_id, label) in enumerate([
            ("competition", "竞赛材料审查"), ("contract", "合同条款审查"),
        ], start=2):
            button = ctk.CTkButton(
                sidebar, text=label, height=44, corner_radius=8, anchor="w", border_spacing=16,
                font=("Microsoft YaHei UI", 13, "bold"), fg_color="transparent",
                hover_color=COLORS["panel_alt"], text_color="#B4BDC6",
                command=lambda value=scenario_id: self._set_scenario(value),
            )
            button.grid(row=row, column=0, padx=12, pady=3, sticky="ew")
            self.scenario_buttons[scenario_id] = button

        ctk.CTkLabel(
            sidebar, text="更多能力", anchor="w", text_color="#66717D",
            font=("Microsoft YaHei UI", 11, "bold"),
        ).grid(row=4, column=0, padx=25, pady=(30, 10), sticky="ew")
        ctk.CTkButton(
            sidebar, text="科研材料审查   即将推出", height=42, corner_radius=8, anchor="w",
            border_spacing=16, font=("Microsoft YaHei UI", 12), state="disabled",
            fg_color="transparent", text_color_disabled="#59636E",
        ).grid(row=5, column=0, padx=12, pady=3, sticky="ew")

        privacy = ctk.CTkFrame(sidebar, fg_color="#0D2B23", corner_radius=10)
        privacy.grid(row=9, column=0, padx=16, pady=(12, 16), sticky="sew")
        ctk.CTkLabel(
            privacy, text="本地处理", anchor="w", text_color=COLORS["accent"],
            font=("Microsoft YaHei UI", 12, "bold"),
        ).pack(fill="x", padx=16, pady=(14, 4))
        ctk.CTkLabel(
            privacy, text="材料只在本机解析\n无需账户与网络连接", justify="left", anchor="w",
            text_color="#A9BFB8", font=("Microsoft YaHei UI", 11),
        ).pack(fill="x", padx=16, pady=(0, 14))
        ctk.CTkLabel(
            sidebar, text="v0.3 · Native Desktop", text_color="#56606B", font=("Cascadia Mono", 9),
        ).grid(row=10, column=0, padx=24, pady=(0, 20), sticky="w")

    def _build_main(self) -> None:
        main = ctk.CTkFrame(self, corner_radius=0, fg_color=COLORS["app"])
        main.grid(row=0, column=1, sticky="nsew")
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(3, weight=1)

        header = ctk.CTkFrame(main, height=104, corner_radius=0, fg_color="transparent")
        header.grid(row=0, column=0, padx=30, pady=(24, 10), sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        self.title_label = ctk.CTkLabel(
            header, text="", anchor="w", text_color=COLORS["text"],
            font=("Microsoft YaHei UI", 28, "bold"),
        )
        self.title_label.grid(row=0, column=0, sticky="w")
        self.subtitle_label = ctk.CTkLabel(
            header, text="", anchor="w", text_color=COLORS["muted"], font=("Microsoft YaHei UI", 12),
        )
        self.subtitle_label.grid(row=1, column=0, pady=(5, 0), sticky="w")
        self.add_button = ctk.CTkButton(
            header, text="＋ 添加材料", width=118, height=42, corner_radius=8,
            fg_color=COLORS["panel_alt"], hover_color=COLORS["border"], border_width=1,
            border_color=COLORS["border"], text_color=COLORS["text"],
            font=("Microsoft YaHei UI", 12, "bold"), command=self._choose_files,
        )
        self.add_button.grid(row=0, column=1, rowspan=2, padx=(12, 10))
        self.review_button = ctk.CTkButton(
            header, text="开始审查", width=118, height=42, corner_radius=8,
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"], text_color="#071B14",
            font=("Microsoft YaHei UI", 12, "bold"), command=self._start_review,
        )
        self.review_button.grid(row=0, column=2, rowspan=2)

        metrics = ctk.CTkFrame(main, fg_color="transparent")
        metrics.grid(row=1, column=0, padx=30, pady=(4, 18), sticky="ew")
        for index in range(4):
            metrics.grid_columnconfigure(index, weight=1, uniform="metric")
        self.metric_values: list[ctk.CTkLabel] = []
        for index, label in enumerate(["已添加材料", "发现问题", "高风险项", "整改进度"]):
            card = ctk.CTkFrame(
                metrics, height=88, fg_color=COLORS["panel"], corner_radius=10,
                border_width=1, border_color=COLORS["border"],
            )
            card.grid(row=0, column=index, padx=(0 if index == 0 else 6, 0 if index == 3 else 6), sticky="ew")
            card.grid_propagate(False)
            ctk.CTkLabel(card, text=label, anchor="w", text_color=COLORS["muted"], font=("Microsoft YaHei UI", 11)).pack(fill="x", padx=16, pady=(13, 2))
            value = ctk.CTkLabel(card, text="0", anchor="w", text_color=COLORS["text"], font=("Cascadia Mono", 23, "bold"))
            value.pack(fill="x", padx=16)
            self.metric_values.append(value)

        self.progress = ctk.CTkProgressBar(
            main, height=3, corner_radius=0, progress_color=COLORS["accent"], fg_color=COLORS["border"],
        )
        self.progress.grid(row=2, column=0, padx=30, sticky="ew")
        self.progress.set(0)

        workspace = ctk.CTkFrame(main, fg_color="transparent")
        workspace.grid(row=3, column=0, padx=30, pady=(15, 12), sticky="nsew")
        workspace.grid_rowconfigure(0, weight=1)
        workspace.grid_columnconfigure(0, weight=0, minsize=242)
        workspace.grid_columnconfigure(1, weight=0, minsize=330)
        workspace.grid_columnconfigure(2, weight=1, minsize=410)

        self.file_panel = self._panel(workspace, 0, "材料清单", "0 个文件")
        self.file_list = ctk.CTkScrollableFrame(self.file_panel, fg_color="transparent", scrollbar_button_color=COLORS["border"])
        self.file_list.pack(fill="both", expand=True, padx=8, pady=(2, 10))
        self.finding_panel = self._panel(workspace, 1, "审查结果", "等待审查")
        self.finding_list = ctk.CTkScrollableFrame(self.finding_panel, fg_color="transparent", scrollbar_button_color=COLORS["border"])
        self.finding_list.pack(fill="both", expand=True, padx=8, pady=(2, 10))
        self.detail_panel = self._panel(workspace, 2, "问题详情", "证据可追溯")
        self.detail_content = ctk.CTkScrollableFrame(self.detail_panel, fg_color="transparent", scrollbar_button_color=COLORS["border"])
        self.detail_content.pack(fill="both", expand=True, padx=18, pady=(4, 14))

        footer = ctk.CTkFrame(main, height=32, fg_color="transparent")
        footer.grid(row=4, column=0, padx=30, pady=(0, 13), sticky="ew")
        footer.grid_columnconfigure(0, weight=1)
        self.status_label = ctk.CTkLabel(footer, text="就绪", anchor="w", text_color=COLORS["muted"], font=("Microsoft YaHei UI", 10))
        self.status_label.grid(row=0, column=0, sticky="w")
        self.export_button = ctk.CTkButton(
            footer, text="导出审查报告", width=108, height=28, corner_radius=6, fg_color="transparent",
            hover_color=COLORS["panel_alt"], border_width=1, border_color=COLORS["border"],
            text_color=COLORS["muted"], font=("Microsoft YaHei UI", 10),
            command=self._export_report, state="disabled",
        )
        self.export_button.grid(row=0, column=1, sticky="e")

    def _panel(self, parent: ctk.CTkFrame, column: int, title: str, meta: str) -> ctk.CTkFrame:
        panel = ctk.CTkFrame(
            parent, fg_color=COLORS["panel"], corner_radius=10, border_width=1, border_color=COLORS["border"],
        )
        panel.grid(row=0, column=column, padx=(0 if column == 0 else 6, 0 if column == 2 else 6), sticky="nsew")
        heading = ctk.CTkFrame(panel, height=54, fg_color="transparent")
        heading.pack(fill="x", padx=16, pady=(4, 0))
        heading.pack_propagate(False)
        ctk.CTkLabel(heading, text=title, anchor="w", text_color=COLORS["text"], font=("Microsoft YaHei UI", 13, "bold")).pack(side="left", fill="y")
        meta_label = ctk.CTkLabel(heading, text=meta, anchor="e", text_color=COLORS["muted"], font=("Microsoft YaHei UI", 10))
        meta_label.pack(side="right", fill="y")
        panel.meta_label = meta_label  # type: ignore[attr-defined]
        return panel

    def _set_scenario(self, scenario: str) -> None:
        self.scenario = scenario
        info = SCENARIOS[scenario]
        self.title_label.configure(text=info["title"])
        self.subtitle_label.configure(text=info["subtitle"])
        for scenario_id, button in self.scenario_buttons.items():
            if scenario_id == scenario:
                button.configure(fg_color=COLORS["accent_dark"], text_color=COLORS["accent"])
            else:
                button.configure(fg_color="transparent", text_color="#B4BDC6")
        self.result = None
        self.selected_finding = None
        self.resolved_ids.clear()
        self._render_findings()
        self._render_detail()
        self._update_metrics()
        self.status_label.configure(text=info["hint"])

    def _choose_files(self) -> None:
        selected = filedialog.askopenfilenames(
            title="选择需要审查的材料",
            filetypes=[("支持的材料", "*.pdf *.docx *.xlsx *.txt *.md *.csv *.json"), ("所有文件", "*.*")],
        )
        if not selected:
            return
        known = {str(path).lower() for path in self.paths}
        rejected: list[str] = []
        for item in selected:
            path = Path(item)
            if path.suffix.lower() not in SUPPORTED_SUFFIXES:
                rejected.append(path.name)
            elif str(path).lower() not in known:
                self.paths.append(path)
                known.add(str(path).lower())
        self._render_files()
        self._update_metrics()
        self.status_label.configure(text=f"已添加 {len(self.paths)} 个文件，可以开始审查")
        if rejected:
            messagebox.showwarning("部分文件未添加", "暂不支持：\n" + "\n".join(rejected))

    def _remove_file(self, path: Path) -> None:
        self.paths = [item for item in self.paths if item != path]
        self.result = None
        self.resolved_ids.clear()
        self._render_files()
        self._render_findings()
        self._render_detail()
        self._update_metrics()

    def _render_files(self) -> None:
        for child in self.file_list.winfo_children():
            child.destroy()
        self.file_panel.meta_label.configure(text=f"{len(self.paths)} 个文件")  # type: ignore[attr-defined]
        if not self.paths:
            ctk.CTkLabel(
                self.file_list, text="还没有材料\n\n点击右上角“添加材料”", justify="center",
                text_color="#68737E", font=("Microsoft YaHei UI", 11),
            ).pack(pady=70)
            return
        for path in self.paths:
            row = ctk.CTkFrame(self.file_list, fg_color=COLORS["panel_alt"], corner_radius=8)
            row.pack(fill="x", pady=4)
            row.grid_columnconfigure(1, weight=1)
            ext = path.suffix.upper().lstrip(".") or "FILE"
            ctk.CTkLabel(
                row, text=ext, width=42, height=30, corner_radius=6, fg_color="#202A33",
                text_color=COLORS["accent"], font=("Cascadia Mono", 9, "bold"),
            ).grid(row=0, column=0, rowspan=2, padx=(10, 8), pady=10)
            ctk.CTkLabel(row, text=path.name, anchor="w", text_color=COLORS["text"], font=("Microsoft YaHei UI", 11, "bold")).grid(row=0, column=1, pady=(10, 0), sticky="ew")
            ctk.CTkLabel(row, text=self._file_size(path), anchor="w", text_color=COLORS["muted"], font=("Cascadia Mono", 9)).grid(row=1, column=1, pady=(0, 10), sticky="ew")
            ctk.CTkButton(
                row, text="×", width=28, height=28, corner_radius=6, fg_color="transparent",
                hover_color="#342126", text_color="#8C969F", font=("Segoe UI", 16),
                command=lambda value=path: self._remove_file(value),
            ).grid(row=0, column=2, rowspan=2, padx=8)

    def _render_findings(self) -> None:
        for child in self.finding_list.winfo_children():
            child.destroy()
        if not self.result:
            self.finding_panel.meta_label.configure(text="等待审查")  # type: ignore[attr-defined]
            ctk.CTkLabel(
                self.finding_list, text="添加材料并运行审查后，\n问题会按风险等级排列在这里。",
                justify="center", text_color="#68737E", font=("Microsoft YaHei UI", 11),
            ).pack(pady=70)
            return
        self.finding_panel.meta_label.configure(text=f"{len(self.result.findings)} 项")  # type: ignore[attr-defined]
        for finding in self.result.findings:
            selected = self.selected_finding and self.selected_finding.finding_id == finding.finding_id
            resolved = finding.finding_id in self.resolved_ids
            label, color = SEVERITY_META[finding.severity]
            row = ctk.CTkButton(
                self.finding_list, text="", height=86, corner_radius=8,
                fg_color=COLORS["accent_dark"] if selected else COLORS["panel_alt"],
                hover_color="#1E2831", command=lambda value=finding: self._select_finding(value),
            )
            row.pack(fill="x", pady=4)
            row.grid_columnconfigure(1, weight=1)
            ctk.CTkLabel(
                row, text="✓" if resolved else label, width=54, height=24, corner_radius=5,
                fg_color="#173129" if resolved else "#252A30", text_color=COLORS["accent"] if resolved else color,
                font=("Microsoft YaHei UI", 9, "bold"),
            ).grid(row=0, column=0, padx=(11, 8), pady=(14, 4), sticky="nw")
            ctk.CTkLabel(
                row, text=finding.title, anchor="w", justify="left", wraplength=215,
                text_color="#7D8985" if resolved else COLORS["text"], font=("Microsoft YaHei UI", 11, "bold"),
            ).grid(row=0, column=1, padx=(0, 10), pady=(13, 3), sticky="ew")
            source = finding.evidence[0].file if finding.evidence else "审查规则"
            ctk.CTkLabel(
                row, text=f"{finding.finding_id} · {source}", anchor="w", text_color=COLORS["muted"],
                font=("Cascadia Mono", 8),
            ).grid(row=1, column=1, padx=(0, 10), pady=(0, 12), sticky="ew")

    def _select_finding(self, finding: Finding) -> None:
        self.selected_finding = finding
        self._render_findings()
        self._render_detail()

    def _render_detail(self) -> None:
        for child in self.detail_content.winfo_children():
            child.destroy()
        finding = self.selected_finding
        if not finding:
            ctk.CTkLabel(
                self.detail_content, text="选择一条审查问题\n查看结论、证据和整改建议",
                justify="center", text_color="#68737E", font=("Microsoft YaHei UI", 12),
            ).pack(pady=90)
            return
        severity_label, severity_color = SEVERITY_META[finding.severity]
        ctk.CTkLabel(
            self.detail_content, text=severity_label, width=72, height=27, corner_radius=6,
            fg_color="#252A30", text_color=severity_color, font=("Microsoft YaHei UI", 10, "bold"),
        ).pack(anchor="w", pady=(8, 14))
        ctk.CTkLabel(
            self.detail_content, text=finding.title, anchor="w", justify="left", wraplength=520,
            text_color=COLORS["text"], font=("Microsoft YaHei UI", 21, "bold"),
        ).pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(
            self.detail_content, text=finding.detail, anchor="w", justify="left", wraplength=520,
            text_color="#B6BFC8", font=("Microsoft YaHei UI", 12),
        ).pack(fill="x", pady=(0, 22))
        evidence = finding.evidence[0] if finding.evidence else None
        evidence_card = ctk.CTkFrame(
            self.detail_content, fg_color="#10151B", corner_radius=8, border_width=1, border_color=COLORS["border"],
        )
        evidence_card.pack(fill="x", pady=(0, 14))
        ctk.CTkLabel(evidence_card, text="原文证据", anchor="w", text_color=COLORS["accent"], font=("Microsoft YaHei UI", 10, "bold")).pack(fill="x", padx=16, pady=(14, 8))
        ctk.CTkLabel(
            evidence_card, text=f'“{evidence.excerpt if evidence else "暂无原文证据"}”', anchor="w",
            justify="left", wraplength=490, text_color="#D8DEE3", font=("Microsoft YaHei UI", 12),
        ).pack(fill="x", padx=16)
        ctk.CTkLabel(
            evidence_card, text=f"{evidence.file if evidence else '审查规则'}  ·  第 {evidence.page if evidence else 1} 页",
            anchor="w", text_color=COLORS["muted"], font=("Cascadia Mono", 9),
        ).pack(fill="x", padx=16, pady=(9, 14))
        ctk.CTkLabel(self.detail_content, text="整改建议", anchor="w", text_color=COLORS["muted"], font=("Microsoft YaHei UI", 10, "bold")).pack(fill="x", pady=(4, 7))
        ctk.CTkLabel(
            self.detail_content, text=finding.suggestion, anchor="w", justify="left", wraplength=520,
            text_color=COLORS["text"], font=("Microsoft YaHei UI", 12),
        ).pack(fill="x", pady=(0, 22))
        resolved = finding.finding_id in self.resolved_ids
        ctk.CTkButton(
            self.detail_content, text="恢复为待处理" if resolved else "标记为已解决", height=40,
            corner_radius=8, fg_color=COLORS["panel_alt"] if resolved else COLORS["accent"],
            hover_color=COLORS["border"] if resolved else COLORS["accent_hover"],
            text_color=COLORS["text"] if resolved else "#071B14",
            font=("Microsoft YaHei UI", 11, "bold"), command=self._toggle_resolved,
        ).pack(fill="x")

    def _toggle_resolved(self) -> None:
        if not self.selected_finding:
            return
        finding_id = self.selected_finding.finding_id
        if finding_id in self.resolved_ids:
            self.resolved_ids.remove(finding_id)
        else:
            self.resolved_ids.add(finding_id)
        self._render_findings()
        self._render_detail()
        self._update_metrics()

    def _start_review(self) -> None:
        if not self.paths:
            messagebox.showinfo("添加材料", "请先添加需要审查的文件。")
            return
        self.review_button.configure(state="disabled", text="正在审查…")
        self.add_button.configure(state="disabled")
        self.progress.set(0.04)
        self.status_label.configure(text="正在准备解析材料")
        threading.Thread(target=self._review_worker, daemon=True).start()

    def _review_worker(self) -> None:
        try:
            result = review_paths(self.scenario, list(self.paths), self._on_worker_progress)
            self.after(0, lambda: self._finish_review(result))
        except Exception as error:
            self.after(0, lambda message=str(error): self._fail_review(message))

    def _on_worker_progress(self, current: int, total: int, message: str) -> None:
        value = 0.08 + (current / max(total, 1)) * 0.82
        self.after(0, lambda: (self.progress.set(value), self.status_label.configure(text=message)))

    def _finish_review(self, result: ReviewResult) -> None:
        self.result = result
        self.resolved_ids.clear()
        self.selected_finding = result.findings[0] if result.findings else None
        self.progress.set(1)
        self.review_button.configure(state="normal", text="重新审查")
        self.add_button.configure(state="normal")
        self.export_button.configure(state="normal")
        characters = sum(item.characters for item in result.files)
        self.status_label.configure(text=f"审查完成 · 解析 {len(result.files)} 个文件，共 {characters:,} 个字符")
        self._render_findings()
        self._render_detail()
        self._update_metrics()

    def _fail_review(self, detail: str) -> None:
        self.progress.set(0)
        self.review_button.configure(state="normal", text="开始审查")
        self.add_button.configure(state="normal")
        self.status_label.configure(text="审查失败，请检查文件后重试")
        messagebox.showerror("审查失败", detail)

    def _update_metrics(self) -> None:
        findings = self.result.findings if self.result else []
        open_findings = [item for item in findings if item.finding_id not in self.resolved_ids]
        high_risk = [item for item in open_findings if item.severity in {"blocking", "high"}]
        completion = round((len(self.resolved_ids) / len(findings)) * 100) if findings else 0
        values = [str(len(self.paths)), str(len(open_findings)), str(len(high_risk)), f"{completion}%"]
        for label, value in zip(self.metric_values, values):
            label.configure(text=value)
        self.metric_values[2].configure(text_color=COLORS["danger"] if high_risk else COLORS["text"])

    def _export_report(self) -> None:
        if not self.result:
            return
        target = filedialog.asksaveasfilename(
            title="导出审查报告", defaultextension=".txt", filetypes=[("文本报告", "*.txt")],
            initialfile=f"{SCENARIOS[self.scenario]['title']}-审查报告.txt",
        )
        if not target:
            return
        lines = [
            "明鉴材料审查报告", f"审查场景：{SCENARIOS[self.scenario]['title']}",
            f"材料数量：{len(self.result.files)}", f"问题数量：{len(self.result.findings)}", "",
        ]
        for index, finding in enumerate(self.result.findings, start=1):
            evidence = finding.evidence[0] if finding.evidence else None
            lines.extend([
                f"{index}. [{SEVERITY_META[finding.severity][0]}] {finding.title}",
                f"编号：{finding.finding_id}", f"说明：{finding.detail}",
                f"证据：{evidence.excerpt if evidence else '暂无'}",
                f"来源：{evidence.file if evidence else '审查规则'} 第 {evidence.page if evidence else 1} 页",
                f"建议：{finding.suggestion}",
                f"状态：{'已解决' if finding.finding_id in self.resolved_ids else '待处理'}", "",
            ])
        Path(target).write_text("\n".join(lines), encoding="utf-8")
        self.status_label.configure(text=f"报告已导出到 {target}")

    @staticmethod
    def _file_size(path: Path) -> str:
        size = path.stat().st_size
        return f"{size / (1024 * 1024):.1f} MB" if size >= 1024 * 1024 else f"{max(1, round(size / 1024))} KB"


def main() -> None:
    ctk.set_appearance_mode("dark")
    app = MingJianApp()
    app.mainloop()


if __name__ == "__main__":
    main()
