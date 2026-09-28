from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QObject, QSettings, QSize, Qt, QThread, QTimer, Signal, Slot
from PySide6.QtGui import QColor, QDragEnterEvent, QDropEvent, QFont, QIcon, QPalette, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from backend.model_provider import ModelConfig, list_models
from backend.review_engine import Finding, ReviewResult, SUPPORTED_SUFFIXES, review_paths


COLORS = {
    "app": "#0A0E13",
    "sidebar": "#0E131A",
    "panel": "#111820",
    "panel_alt": "#161E27",
    "border": "#27323D",
    "text": "#F3F6F8",
    "muted": "#8D99A6",
    "accent": "#49DDAA",
    "accent_hover": "#6BE8BC",
    "accent_dark": "#10392E",
    "danger": "#FF6B73",
    "warning": "#FFB45D",
    "medium": "#E9CB68",
    "info": "#6FB7FF",
}

SEVERITY_META = {
    "blocking": ("阻断", COLORS["danger"]),
    "high": ("高风险", COLORS["warning"]),
    "medium": ("需关注", COLORS["medium"]),
    "info": ("提示", COLORS["info"]),
}

SCENARIOS = {
    "competition": {
        "title": "大学生竞赛审查",
        "nav": "竞赛材料审查",
        "subtitle": "核对材料完整性、团队信息和跨文件一致性",
        "hint": "建议添加比赛通知、报名表、项目书和承诺书",
    },
    "contract": {
        "title": "合同审查",
        "nav": "合同条款审查",
        "subtitle": "检查付款比例、验收期限和关键条款风险",
        "hint": "建议添加合同正文、报价单、交付清单和内部规则",
    },
}

MODEL_PROVIDERS = {
    "embedded": ("内置 Qwen2.5 0.5B", "", "Qwen2.5-0.5B-Instruct Q4_K_M"),
    "openai": ("OpenAI", "https://api.openai.com/v1", "gpt-4.1-mini"),
    "anthropic": ("Anthropic Claude", "https://api.anthropic.com/v1", "claude-sonnet-4-5"),
    "gemini": ("Google Gemini", "https://generativelanguage.googleapis.com/v1beta", "gemini-2.5-flash"),
    "deepseek": ("DeepSeek", "https://api.deepseek.com/v1", "deepseek-chat"),
    "dashscope": ("阿里云百炼 / 通义千问", "https://dashscope.aliyuncs.com/compatible-mode/v1", "qwen-plus"),
    "zhipu": ("智谱 GLM", "https://open.bigmodel.cn/api/paas/v4", "glm-4-flash"),
    "moonshot": ("Moonshot / Kimi", "https://api.moonshot.cn/v1", "moonshot-v1-8k"),
    "siliconflow": ("硅基流动", "https://api.siliconflow.cn/v1", "Qwen/Qwen3-8B"),
    "volcengine": ("火山方舟 / 豆包", "https://ark.cn-beijing.volces.com/api/v3", ""),
    "openrouter": ("OpenRouter", "https://openrouter.ai/api/v1", "qwen/qwen3-8b"),
    "ollama": ("Ollama 本地模型", "http://127.0.0.1:11434", "qwen3:4b"),
    "custom": ("其他 OpenAI 兼容服务", "", ""),
}


def resource_path(relative: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / relative


class ReviewWorker(QObject):
    progress = Signal(int, int, str)
    completed = Signal(object)
    failed = Signal(str)

    def __init__(self, scenario: str, paths: list[Path], model_config: ModelConfig) -> None:
        super().__init__()
        self.scenario = scenario
        self.paths = paths
        self.model_config = model_config

    @Slot()
    def run(self) -> None:
        try:
            result = review_paths(self.scenario, self.paths, self.progress.emit, self.model_config)
            self.completed.emit(result)
        except Exception as error:
            self.failed.emit(str(error))


class MetricCard(QFrame):
    def __init__(self, label: str) -> None:
        super().__init__()
        self.setObjectName("metricCard")
        self.setMinimumHeight(82)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 13, 16, 12)
        layout.setSpacing(2)
        caption = QLabel(label)
        caption.setObjectName("metricCaption")
        self.value = QLabel("0")
        self.value.setObjectName("metricValue")
        layout.addWidget(caption)
        layout.addWidget(self.value)


class Panel(QFrame):
    def __init__(self, title: str, meta: str) -> None:
        super().__init__()
        self.setObjectName("panel")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        heading = QWidget()
        heading.setFixedHeight(54)
        heading_layout = QHBoxLayout(heading)
        heading_layout.setContentsMargins(18, 0, 18, 0)
        title_label = QLabel(title)
        title_label.setObjectName("panelTitle")
        self.meta_label = QLabel(meta)
        self.meta_label.setObjectName("panelMeta")
        heading_layout.addWidget(title_label)
        heading_layout.addStretch()
        heading_layout.addWidget(self.meta_label)
        self.layout.addWidget(heading)


class FileRow(QWidget):
    remove_requested = Signal(Path)

    def __init__(self, path: Path) -> None:
        super().__init__()
        self.path = path
        self.setObjectName("listCard")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 9, 9, 9)
        layout.setSpacing(10)
        suffix = QLabel(path.suffix.upper().lstrip(".") or "FILE")
        suffix.setObjectName("fileType")
        suffix.setAlignment(Qt.AlignmentFlag.AlignCenter)
        suffix.setFixedSize(42, 34)
        text = QVBoxLayout()
        text.setSpacing(2)
        name = QLabel(path.name)
        name.setObjectName("fileName")
        name.setToolTip(str(path))
        size = QLabel(format_file_size(path))
        size.setObjectName("fileSize")
        text.addWidget(name)
        text.addWidget(size)
        remove = QPushButton("×")
        remove.setObjectName("iconButton")
        remove.setFixedSize(28, 28)
        remove.setToolTip("移除材料")
        remove.clicked.connect(lambda: self.remove_requested.emit(self.path))
        layout.addWidget(suffix)
        layout.addLayout(text, 1)
        layout.addWidget(remove)


class FindingRow(QWidget):
    def __init__(self, finding: Finding, resolved: bool) -> None:
        super().__init__()
        self.setObjectName("findingCard")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(11)
        label, color = SEVERITY_META[finding.severity]
        badge = QLabel("已解决" if resolved else label)
        badge.setProperty("role", "resolved" if resolved else finding.severity)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setFixedSize(54, 24)
        texts = QVBoxLayout()
        texts.setSpacing(4)
        title = QLabel(finding.title)
        title.setObjectName("findingTitleResolved" if resolved else "findingTitle")
        title.setWordWrap(True)
        source = finding.evidence[0].file if finding.evidence else "审查规则"
        origin = "大模型" if finding.source == "model" else "规则"
        meta = QLabel(f"{finding.finding_id}  ·  {origin}  ·  {source}")
        meta.setObjectName("findingMeta")
        texts.addWidget(title)
        texts.addWidget(meta)
        layout.addWidget(badge, 0, Qt.AlignmentFlag.AlignTop)
        layout.addLayout(texts, 1)
        self.setStyleSheet(f"QLabel[role='{finding.severity}'] {{ color: {color}; }}")


class ModelSettingsDialog(QDialog):
    def __init__(self, config: ModelConfig, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("模型接口")
        self.setMinimumWidth(540)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 20)
        layout.setSpacing(15)
        title = QLabel("审查模型")
        title.setObjectName("dialogTitle")
        description = QLabel("默认使用内置 Qwen2.5 离线审查。也可连接 OpenAI、Claude、Gemini、DeepSeek、通义千问、智谱、Kimi、豆包、硅基流动、OpenRouter、Ollama 或其他兼容服务。")
        description.setObjectName("dialogDescription")
        description.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(description)

        form = QFormLayout()
        form.setSpacing(12)
        self.enabled = QCheckBox("启用 AI 智能审查")
        self.enabled.setChecked(config.enabled)
        self.provider = QComboBox()
        for provider_id, (label, _, _) in MODEL_PROVIDERS.items():
            self.provider.addItem(label, provider_id)
        provider_index = self.provider.findData(config.provider)
        self.provider.setCurrentIndex(max(0, provider_index))
        self.base_url = QLineEdit(config.base_url)
        self.model = QComboBox()
        self.model.setEditable(True)
        self.model.addItems([preset[2] for preset in MODEL_PROVIDERS.values() if preset[2]])
        self.model.setCurrentText(config.model)
        self.api_key = QLineEdit(config.api_key)
        self.api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key.setPlaceholderText("本地 Ollama 无需填写")
        form.addRow("状态", self.enabled)
        form.addRow("接口类型", self.provider)
        form.addRow("接口地址", self.base_url)
        form.addRow("模型名称", self.model)
        form.addRow("API Key", self.api_key)
        layout.addLayout(form)

        note = QLabel("内置模型完全在本机运行。外部接口会把抽取后的材料文本发送给所选服务商，API Key 仅保存在当前 Windows 用户配置中。")
        note.setObjectName("settingsNote")
        note.setWordWrap(True)
        layout.addWidget(note)
        test_row = QHBoxLayout()
        self.test_status = QLabel("接口尚未检测")
        self.test_status.setObjectName("testStatus")
        test_button = QPushButton("检测连接")
        test_button.setObjectName("secondaryButton")
        test_button.setFixedHeight(36)
        test_button.clicked.connect(self._test_connection)
        test_row.addWidget(self.test_status, 1)
        test_row.addWidget(test_button)
        layout.addLayout(test_row)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Save)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.provider.currentIndexChanged.connect(lambda _index: self._provider_changed(apply_defaults=True))
        self._provider_changed(apply_defaults=False)

    def _provider_changed(self, apply_defaults: bool = True) -> None:
        provider_id = self.provider.currentData()
        is_embedded = provider_id == "embedded"
        is_ollama = provider_id == "ollama"
        self.base_url.setEnabled(not is_embedded)
        self.model.setEnabled(not is_embedded)
        self.api_key.setEnabled(not is_embedded and not is_ollama)
        self.api_key.setPlaceholderText("本地模型无需填写" if is_ollama else "输入所选服务商的 API Key")
        if apply_defaults:
            _, default_url, default_model = MODEL_PROVIDERS[provider_id]
            self.base_url.setText(default_url)
            self.model.setCurrentText(default_model)
        if is_embedded:
            self.api_key.clear()

    def config(self) -> ModelConfig:
        return ModelConfig(
            enabled=self.enabled.isChecked(),
            provider=self.provider.currentData(),
            base_url=self.base_url.text().strip(),
            model=self.model.currentText().strip(),
            api_key=self.api_key.text().strip(),
        )

    def _test_connection(self) -> None:
        self.test_status.setText("正在检测…")
        QApplication.processEvents()
        config = self.config()
        config.timeout = 8
        try:
            models = list_models(config)
        except RuntimeError as error:
            self.test_status.setText(str(error))
            self.test_status.setProperty("ok", False)
        else:
            for model in models:
                if self.model.findText(model) < 0:
                    self.model.addItem(model)
            if config.provider == "embedded":
                self.test_status.setText("内置模型完整，可离线使用")
            else:
                self.test_status.setText(f"连接成功 · 发现 {len(models)} 个模型")
            self.test_status.setProperty("ok", True)
        self.test_status.style().unpolish(self.test_status)
        self.test_status.style().polish(self.test_status)


class MingJianWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("明鉴 · 材料审查工具")
        icon_path = resource_path("assets/mingjian-v2.ico")
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self.scenario = "competition"
        self.paths: list[Path] = []
        self.result: ReviewResult | None = None
        self.selected_finding: Finding | None = None
        self.resolved_ids: set[str] = set()
        self.thread: QThread | None = None
        self.worker: ReviewWorker | None = None
        self.settings = QSettings("MingJian", "MingJian")
        self.model_config = self._load_model_config()
        self.setAcceptDrops(True)

        screen = QApplication.primaryScreen().availableGeometry()
        width = min(1320, max(1060, int(screen.width() * 0.82)))
        height = min(860, max(680, int(screen.height() * 0.82)))
        self.resize(width, height)
        self.setMinimumSize(1040, 680)
        self.move(screen.center() - self.rect().center())

        self.setStyleSheet(APP_STYLE)
        self._build_ui()
        self._set_scenario("competition")

    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("root")
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        root_layout.addWidget(self._build_sidebar())
        root_layout.addWidget(self._build_workspace(), 1)
        self.setCentralWidget(root)

    def _build_sidebar(self) -> QWidget:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(212)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(18, 24, 18, 18)
        layout.setSpacing(6)

        brand = QHBoxLayout()
        brand.setSpacing(11)
        mark = QLabel()
        mark.setObjectName("brandMark")
        mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mark.setFixedSize(44, 44)
        logo_path = resource_path("assets/mingjian-icon-v2.png")
        if logo_path.exists():
            mark.setPixmap(QPixmap(str(logo_path)).scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        brand_text = QVBoxLayout()
        brand_text.setSpacing(0)
        name = QLabel("明鉴")
        name.setObjectName("brandName")
        english = QLabel("MATERIAL REVIEW")
        english.setObjectName("brandEnglish")
        brand_text.addWidget(name)
        brand_text.addWidget(english)
        brand.addWidget(mark)
        brand.addLayout(brand_text, 1)
        layout.addLayout(brand)
        layout.addSpacing(42)

        section = QLabel("审查场景")
        section.setObjectName("sectionLabel")
        layout.addWidget(section)
        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        self.nav_buttons: dict[str, QPushButton] = {}
        for scenario_id, info in SCENARIOS.items():
            button = QPushButton(info["nav"])
            button.setObjectName("navButton")
            button.setCheckable(True)
            button.setMinimumHeight(44)
            button.clicked.connect(lambda checked=False, value=scenario_id: self._set_scenario(value))
            self.nav_group.addButton(button)
            self.nav_buttons[scenario_id] = button
            layout.addWidget(button)

        layout.addSpacing(24)
        more = QLabel("更多能力")
        more.setObjectName("sectionLabel")
        layout.addWidget(more)
        upcoming = QPushButton("科研材料审查    即将推出")
        upcoming.setObjectName("navButton")
        upcoming.setEnabled(False)
        upcoming.setMinimumHeight(44)
        layout.addWidget(upcoming)
        layout.addStretch()

        privacy = QFrame()
        privacy.setObjectName("privacyCard")
        privacy_layout = QVBoxLayout(privacy)
        privacy_layout.setContentsMargins(15, 13, 15, 13)
        privacy_layout.setSpacing(4)
        privacy_title = QLabel("本地处理")
        privacy_title.setObjectName("privacyTitle")
        privacy_body = QLabel("内置模型本机推理\n无需账户与网络连接")
        privacy_body.setObjectName("privacyBody")
        privacy_layout.addWidget(privacy_title)
        privacy_layout.addWidget(privacy_body)
        layout.addWidget(privacy)
        version = QLabel("DESKTOP · LOCAL AI")
        version.setObjectName("version")
        layout.addWidget(version)
        return sidebar

    def _build_workspace(self) -> QWidget:
        workspace = QWidget()
        layout = QVBoxLayout(workspace)
        layout.setContentsMargins(28, 24, 28, 15)
        layout.setSpacing(14)

        header = QHBoxLayout()
        header_text = QVBoxLayout()
        header_text.setSpacing(3)
        self.title_label = QLabel()
        self.title_label.setObjectName("pageTitle")
        self.subtitle_label = QLabel()
        self.subtitle_label.setObjectName("pageSubtitle")
        header_text.addWidget(self.title_label)
        header_text.addWidget(self.subtitle_label)
        header.addLayout(header_text, 1)
        self.model_button = QPushButton()
        self.model_button.setObjectName("modelButton")
        self.model_button.setMinimumSize(112, 42)
        self.model_button.clicked.connect(self._open_model_settings)
        self._update_model_button()
        self.add_button = QPushButton("＋  添加材料")
        self.add_button.setObjectName("secondaryButton")
        self.add_button.setMinimumSize(112, 42)
        self.add_button.clicked.connect(self._choose_files)
        self.review_button = QPushButton("开始审查")
        self.review_button.setObjectName("primaryButton")
        self.review_button.setMinimumSize(112, 42)
        self.review_button.clicked.connect(self._start_review)
        header.addWidget(self.model_button)
        header.addWidget(self.add_button)
        header.addWidget(self.review_button)
        layout.addLayout(header)

        metrics = QHBoxLayout()
        metrics.setSpacing(10)
        self.metric_cards = [MetricCard(label) for label in ["已添加材料", "待处理问题", "高风险项", "整改进度"]]
        for card in self.metric_cards:
            metrics.addWidget(card, 1)
        layout.addLayout(metrics)

        self.progress_line = QFrame()
        self.progress_line.setObjectName("progressLine")
        self.progress_line.setFixedHeight(3)
        layout.addWidget(self.progress_line)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setObjectName("workspaceSplitter")
        splitter.setChildrenCollapsible(False)
        self.file_panel = Panel("材料清单", "0 个文件")
        self.file_list = QListWidget()
        self.file_list.setObjectName("fileList")
        self.file_list.setSpacing(6)
        self.file_panel.layout.addWidget(self.file_list, 1)
        self.finding_panel = Panel("审查结果", "等待审查")
        self.finding_list = QListWidget()
        self.finding_list.setObjectName("findingList")
        self.finding_list.setSpacing(6)
        self.finding_list.currentItemChanged.connect(self._on_current_finding_changed)
        self.finding_panel.layout.addWidget(self.finding_list, 1)
        self.detail_panel = Panel("问题详情", "证据可追溯")
        self.detail_scroll = QScrollArea()
        self.detail_scroll.setWidgetResizable(True)
        self.detail_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.detail_scroll.setObjectName("detailScroll")
        self.detail_panel.layout.addWidget(self.detail_scroll, 1)
        splitter.addWidget(self.file_panel)
        splitter.addWidget(self.finding_panel)
        splitter.addWidget(self.detail_panel)
        splitter.setStretchFactor(0, 22)
        splitter.setStretchFactor(1, 29)
        splitter.setStretchFactor(2, 49)
        splitter.setSizes([220, 290, 500])
        layout.addWidget(splitter, 1)

        footer = QHBoxLayout()
        self.status_label = QLabel("就绪")
        self.status_label.setObjectName("statusLabel")
        self.clear_button = QPushButton("清空材料")
        self.clear_button.setObjectName("quietButton")
        self.clear_button.clicked.connect(self._clear_materials)
        self.export_button = QPushButton("导出审查报告")
        self.export_button.setObjectName("quietButton")
        self.export_button.setEnabled(False)
        self.export_button.clicked.connect(self._export_report)
        footer.addWidget(self.status_label, 1)
        footer.addWidget(self.clear_button)
        footer.addWidget(self.export_button)
        layout.addLayout(footer)
        return workspace

    def _set_scenario(self, scenario: str) -> None:
        self.scenario = scenario
        info = SCENARIOS[scenario]
        self.nav_buttons[scenario].setChecked(True)
        self.title_label.setText(info["title"])
        self.subtitle_label.setText(info["subtitle"])
        self.result = None
        self.selected_finding = None
        self.resolved_ids.clear()
        self.export_button.setEnabled(False)
        self._render_findings()
        self._render_detail()
        self._update_metrics()
        self.status_label.setText(info["hint"])

    def _choose_files(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "选择需要审查的材料",
            "",
            "支持的材料 (*.pdf *.docx *.xlsx *.txt *.md *.csv *.json);;所有文件 (*.*)",
        )
        if not files:
            return
        self._add_paths([Path(item) for item in files], auto_review=True)

    def _add_paths(self, incoming: list[Path], auto_review: bool = False) -> None:
        known = {str(path).lower() for path in self.paths}
        rejected: list[str] = []
        added = 0
        for path in incoming:
            if not path.is_file() or path.suffix.lower() not in SUPPORTED_SUFFIXES:
                rejected.append(path.name)
            elif str(path).lower() not in known:
                self.paths.append(path)
                known.add(str(path).lower())
                added += 1
        self.result = None
        self.resolved_ids.clear()
        self._render_files()
        self._render_findings()
        self._render_detail()
        self._update_metrics()
        self.status_label.setText(f"已添加 {len(self.paths)} 个文件，正在准备自动审查" if added and auto_review else f"已添加 {len(self.paths)} 个文件")
        if rejected:
            QMessageBox.warning(self, "部分文件未添加", "暂不支持：\n" + "\n".join(rejected))
        if added and auto_review and self.thread is None:
            QTimer.singleShot(120, self._start_review)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if self.thread is None and event.mimeData().hasUrls() and any(Path(url.toLocalFile()).suffix.lower() in SUPPORTED_SUFFIXES for url in event.mimeData().urls()):
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        paths = [Path(url.toLocalFile()) for url in event.mimeData().urls() if url.isLocalFile()]
        self._add_paths(paths, auto_review=True)
        event.acceptProposedAction()

    def _load_model_config(self) -> ModelConfig:
        schema_version = int(self.settings.value("model/schema_version", 0))
        provider = str(self.settings.value("model/provider", "embedded"))
        if provider not in MODEL_PROVIDERS:
            provider = "embedded"
        enabled = self.settings.value("model/enabled", True, type=bool)
        base_url = str(self.settings.value("model/base_url", ""))
        model_name = str(self.settings.value("model/name", "Qwen2.5-0.5B-Instruct Q4_K_M"))
        if schema_version < 2 and not (enabled and provider != "embedded" and base_url and model_name):
            provider = "embedded"
            enabled = True
            base_url = ""
            model_name = "Qwen2.5-0.5B-Instruct Q4_K_M"
            self.settings.setValue("model/schema_version", 2)
        return ModelConfig(
            enabled=enabled,
            provider=provider,
            base_url=base_url,
            model=model_name,
            api_key=str(self.settings.value("model/api_key", "")),
        )

    def _open_model_settings(self) -> None:
        dialog = ModelSettingsDialog(self.model_config, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        config = dialog.config()
        if config.enabled and config.provider != "embedded" and (not config.base_url or not config.model):
            QMessageBox.warning(self, "模型配置不完整", "启用模型增强时，请填写接口地址和模型名称。")
            return
        self.model_config = config
        self.settings.setValue("model/enabled", config.enabled)
        self.settings.setValue("model/provider", config.provider)
        self.settings.setValue("model/base_url", config.base_url)
        self.settings.setValue("model/name", config.model)
        self.settings.setValue("model/api_key", config.api_key)
        self.settings.setValue("model/schema_version", 2)
        self._update_model_button()
        if config.enabled and config.provider == "embedded":
            self.status_label.setText("已启用内置模型，下次审查将在本机完成推理")
        elif config.enabled:
            self.status_label.setText("已启用外部模型接口，下次审查会自动调用")
        else:
            self.status_label.setText("AI 已关闭，将使用内置规则审查")

    def _update_model_button(self) -> None:
        if self.model_config.enabled:
            label = "内置模型" if self.model_config.provider == "embedded" else MODEL_PROVIDERS.get(self.model_config.provider, ("自定义模型", "", ""))[0]
            self.model_button.setText(f"AI · {label}")
            self.model_button.setToolTip(self.model_config.model)
            self.model_button.setProperty("enabled", True)
        else:
            self.model_button.setText("模型接口 · 可选")
            self.model_button.setProperty("enabled", False)
        self.model_button.style().unpolish(self.model_button)
        self.model_button.style().polish(self.model_button)

    def _remove_file(self, path: Path) -> None:
        self.paths = [item for item in self.paths if item != path]
        self.result = None
        self.selected_finding = None
        self.resolved_ids.clear()
        self.export_button.setEnabled(False)
        self._render_files()
        self._render_findings()
        self._render_detail()
        self._update_metrics()

    def _clear_materials(self) -> None:
        if self.thread is not None:
            return
        self.paths.clear()
        self.result = None
        self.selected_finding = None
        self.resolved_ids.clear()
        self.export_button.setEnabled(False)
        self._render_files()
        self._render_findings()
        self._render_detail()
        self._update_metrics()
        self.status_label.setText(SCENARIOS[self.scenario]["hint"])

    def _render_files(self) -> None:
        self.file_list.clear()
        self.file_panel.meta_label.setText(f"{len(self.paths)} 个文件")
        if not self.paths:
            self._add_placeholder(self.file_list, "拖入材料即可自动审查\n\n或点击右上角“添加材料”")
            return
        for path in self.paths:
            item = QListWidgetItem()
            item.setSizeHint(QSize(210, 64))
            row = FileRow(path)
            row.remove_requested.connect(self._remove_file)
            self.file_list.addItem(item)
            self.file_list.setItemWidget(item, row)

    def _render_findings(self) -> None:
        self.finding_list.clear()
        if not self.result:
            self.finding_panel.meta_label.setText("等待审查")
            self._add_placeholder(self.finding_list, "运行审查后，问题会按风险等级排列在这里。")
            return
        self.finding_panel.meta_label.setText(f"{len(self.result.findings)} 项")
        for finding in self.result.findings:
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, finding.finding_id)
            item.setSizeHint(QSize(280, 78))
            row = FindingRow(finding, finding.finding_id in self.resolved_ids)
            self.finding_list.addItem(item)
            self.finding_list.setItemWidget(item, row)
            if self.selected_finding and finding.finding_id == self.selected_finding.finding_id:
                self.finding_list.setCurrentItem(item)

    def _on_current_finding_changed(self, item: QListWidgetItem | None, previous: QListWidgetItem | None) -> None:
        del previous
        if not self.result or item is None:
            return
        finding_id = item.data(Qt.ItemDataRole.UserRole)
        self.selected_finding = next((item for item in self.result.findings if item.finding_id == finding_id), None)
        self._render_detail()

    def _render_detail(self) -> None:
        content = QWidget()
        content.setObjectName("detailContent")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(22, 12, 22, 22)
        layout.setSpacing(13)
        finding = self.selected_finding
        if not finding:
            layout.addStretch()
            empty = QLabel("选择一条审查问题\n查看结论、证据和整改建议")
            empty.setObjectName("emptyState")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(empty)
            layout.addStretch()
            self.detail_scroll.setWidget(content)
            return

        severity_label, severity_color = SEVERITY_META[finding.severity]
        badge = QLabel(severity_label)
        badge.setObjectName("detailBadge")
        badge.setStyleSheet(f"color: {severity_color};")
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setFixedSize(72, 27)
        title = QLabel(finding.title)
        title.setObjectName("detailTitle")
        title.setWordWrap(True)
        detail = QLabel(finding.detail)
        detail.setObjectName("detailBody")
        detail.setWordWrap(True)
        layout.addWidget(badge, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(title)
        layout.addWidget(detail)

        evidence = finding.evidence[0] if finding.evidence else None
        evidence_card = QFrame()
        evidence_card.setObjectName("evidenceCard")
        evidence_layout = QVBoxLayout(evidence_card)
        evidence_layout.setContentsMargins(17, 15, 17, 15)
        evidence_layout.setSpacing(9)
        evidence_label = QLabel("原文证据")
        evidence_label.setObjectName("evidenceLabel")
        excerpt = QLabel(f'“{evidence.excerpt if evidence else "暂无原文证据"}”')
        excerpt.setObjectName("evidenceText")
        excerpt.setWordWrap(True)
        source = QLabel(f"{evidence.file if evidence else '审查规则'}  ·  第 {evidence.page if evidence else 1} 页")
        source.setObjectName("evidenceSource")
        evidence_layout.addWidget(evidence_label)
        evidence_layout.addWidget(excerpt)
        evidence_layout.addWidget(source)
        layout.addWidget(evidence_card)

        suggestion_label = QLabel("整改建议")
        suggestion_label.setObjectName("detailSectionLabel")
        suggestion = QLabel(finding.suggestion)
        suggestion.setObjectName("detailBodyStrong")
        suggestion.setWordWrap(True)
        layout.addWidget(suggestion_label)
        layout.addWidget(suggestion)
        layout.addSpacing(4)
        resolved = finding.finding_id in self.resolved_ids
        action = QPushButton("恢复为待处理" if resolved else "标记为已解决")
        action.setObjectName("secondaryButton" if resolved else "primaryButton")
        action.setMinimumHeight(40)
        action.clicked.connect(self._toggle_resolved)
        layout.addWidget(action)
        layout.addStretch()
        self.detail_scroll.setWidget(content)

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
            QMessageBox.information(self, "添加材料", "请先添加需要审查的文件。")
            return
        self.review_button.setEnabled(False)
        self.review_button.setText("正在审查…")
        self.add_button.setEnabled(False)
        self.clear_button.setEnabled(False)
        self.progress_line.setProperty("running", True)
        self.progress_line.style().unpolish(self.progress_line)
        self.progress_line.style().polish(self.progress_line)
        self.status_label.setText("正在准备解析材料")

        self.thread = QThread(self)
        self.worker = ReviewWorker(self.scenario, list(self.paths), self.model_config)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self._on_review_progress)
        self.worker.completed.connect(self._finish_review)
        self.worker.failed.connect(self._fail_review)
        self.worker.completed.connect(self.thread.quit)
        self.worker.failed.connect(self.thread.quit)
        self.thread.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(self._cleanup_thread)
        self.thread.start()

    @Slot(int, int, str)
    def _on_review_progress(self, current: int, total: int, message: str) -> None:
        self.status_label.setText(f"{message}  ·  {current}/{total}")

    @Slot(object)
    def _finish_review(self, result: ReviewResult) -> None:
        self.result = result
        self.resolved_ids.clear()
        self.selected_finding = result.findings[0] if result.findings else None
        self._reset_review_controls()
        self.export_button.setEnabled(True)
        characters = sum(item.characters for item in result.files)
        self.status_label.setText(f"审查完成  ·  {len(result.files)} 个文件  ·  {characters:,} 个字符  ·  {result.model_status}")
        self._render_findings()
        self._render_detail()
        self._update_metrics()

    @Slot(str)
    def _fail_review(self, detail: str) -> None:
        self._reset_review_controls()
        self.status_label.setText("审查失败，请检查文件后重试")
        QMessageBox.critical(self, "审查失败", detail)

    def _reset_review_controls(self) -> None:
        self.review_button.setEnabled(True)
        self.review_button.setText("重新审查" if self.result else "开始审查")
        self.add_button.setEnabled(True)
        self.clear_button.setEnabled(True)
        self.progress_line.setProperty("running", False)
        self.progress_line.style().unpolish(self.progress_line)
        self.progress_line.style().polish(self.progress_line)

    @Slot()
    def _cleanup_thread(self) -> None:
        self.worker = None
        self.thread = None

    def _update_metrics(self) -> None:
        findings = self.result.findings if self.result else []
        open_findings = [item for item in findings if item.finding_id not in self.resolved_ids]
        high_risk = [item for item in open_findings if item.severity in {"blocking", "high"}]
        completion = round((len(self.resolved_ids) / len(findings)) * 100) if findings else 0
        values = [str(len(self.paths)), str(len(open_findings)), str(len(high_risk)), f"{completion}%"]
        for card, value in zip(self.metric_cards, values):
            card.value.setText(value)
        self.metric_cards[2].value.setProperty("risk", bool(high_risk))
        self.metric_cards[2].value.style().unpolish(self.metric_cards[2].value)
        self.metric_cards[2].value.style().polish(self.metric_cards[2].value)

    def _export_report(self) -> None:
        if not self.result:
            return
        target, _ = QFileDialog.getSaveFileName(
            self,
            "导出审查报告",
            f"{SCENARIOS[self.scenario]['title']}-审查报告.txt",
            "文本报告 (*.txt)",
        )
        if not target:
            return
        lines = [
            "明鉴材料审查报告",
            f"审查场景：{SCENARIOS[self.scenario]['title']}",
            f"材料数量：{len(self.result.files)}",
            f"问题数量：{len(self.result.findings)}",
            f"审查方式：{self.result.model_status}",
            "",
        ]
        for index, finding in enumerate(self.result.findings, start=1):
            evidence = finding.evidence[0] if finding.evidence else None
            lines.extend([
                f"{index}. [{SEVERITY_META[finding.severity][0]}] {finding.title}",
                f"编号：{finding.finding_id}",
                f"来源：{'大模型' if finding.source == 'model' else '内置规则'}",
                f"说明：{finding.detail}",
                f"证据：{evidence.excerpt if evidence else '暂无'}",
                f"证据位置：{evidence.file if evidence else '审查规则'} 第 {evidence.page if evidence else 1} 页",
                f"建议：{finding.suggestion}",
                f"状态：{'已解决' if finding.finding_id in self.resolved_ids else '待处理'}",
                "",
            ])
        Path(target).write_text("\n".join(lines), encoding="utf-8")
        self.status_label.setText(f"报告已导出到 {target}")

    @staticmethod
    def _add_placeholder(widget: QListWidget, text: str) -> None:
        item = QListWidgetItem(text)
        item.setFlags(Qt.ItemFlag.NoItemFlags)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        item.setSizeHint(QSize(240, 150))
        widget.addItem(item)


def format_file_size(path: Path) -> str:
    size = path.stat().st_size
    return f"{size / (1024 * 1024):.1f} MB" if size >= 1024 * 1024 else f"{max(1, round(size / 1024))} KB"


APP_STYLE = f"""
* {{
    font-family: "Microsoft YaHei UI", "Segoe UI";
    color: {COLORS['text']};
    outline: none;
}}
QWidget#root, QMainWindow {{ background: {COLORS['app']}; }}
QFrame#sidebar {{ background: {COLORS['sidebar']}; border-right: 1px solid #1D2630; }}
QLabel#brandMark {{ background: transparent; border: 0; }}
QLabel#brandName {{ font-size: 20px; font-weight: 700; }}
QLabel#brandEnglish {{ color: #71808F; font-family: "Cascadia Mono"; font-size: 9px; }}
QLabel#sectionLabel {{ color: #677483; font-size: 11px; font-weight: 600; margin: 2px 7px 6px 7px; }}
QPushButton#navButton {{ background: transparent; color: #B6C0C9; border: 0; border-radius: 8px; padding: 0 14px; text-align: left; font-size: 13px; font-weight: 600; }}
QPushButton#navButton:hover {{ background: #151D26; color: #FFFFFF; }}
QPushButton#navButton:checked {{ background: {COLORS['accent_dark']}; color: {COLORS['accent']}; }}
QPushButton#navButton:disabled {{ color: #4E5A66; }}
QFrame#privacyCard {{ background: #0D2C23; border: 1px solid #154437; border-radius: 9px; }}
QLabel#privacyTitle {{ color: {COLORS['accent']}; font-size: 12px; font-weight: 700; }}
QLabel#privacyBody {{ color: #A6BDB5; font-size: 10px; line-height: 1.5; }}
QLabel#version {{ color: #53606C; font-family: "Cascadia Mono"; font-size: 9px; margin: 8px 5px 0 5px; }}
QLabel#pageTitle {{ font-size: 28px; font-weight: 700; }}
QLabel#pageSubtitle {{ color: {COLORS['muted']}; font-size: 12px; }}
QPushButton#primaryButton {{ background: {COLORS['accent']}; color: #062018; border: 0; border-radius: 8px; padding: 0 18px; font-size: 12px; font-weight: 700; }}
QPushButton#primaryButton:hover {{ background: {COLORS['accent_hover']}; }}
QPushButton#primaryButton:disabled {{ background: #2F6655; color: #90AA9F; }}
QPushButton#secondaryButton, QPushButton#quietButton {{ background: {COLORS['panel_alt']}; border: 1px solid {COLORS['border']}; border-radius: 8px; padding: 0 17px; font-size: 11px; font-weight: 600; }}
QPushButton#secondaryButton:hover, QPushButton#quietButton:hover {{ background: #202A34; border-color: #3A4856; }}
QPushButton#modelButton {{ background: #101820; color: #8D99A6; border: 1px solid #25313C; border-radius: 8px; padding: 0 14px; font-size: 10px; font-weight: 600; }}
QPushButton#modelButton:hover {{ background: #18232D; color: #DDE5EA; border-color: #3B4A57; }}
QPushButton#modelButton[enabled="true"] {{ background: #0D2C23; color: {COLORS['accent']}; border-color: #1B5B48; }}
QPushButton#quietButton {{ min-height: 30px; color: #A8B2BC; }}
QPushButton#quietButton:disabled {{ color: #4C5863; background: transparent; }}
QFrame#metricCard, QFrame#panel {{ background: {COLORS['panel']}; border: 1px solid {COLORS['border']}; border-radius: 9px; }}
QLabel#metricCaption {{ color: {COLORS['muted']}; font-size: 10px; }}
QLabel#metricValue {{ font-family: "Cascadia Mono"; font-size: 22px; font-weight: 700; }}
QLabel#metricValue[risk="true"] {{ color: {COLORS['danger']}; }}
QFrame#progressLine {{ background: {COLORS['border']}; }}
QFrame#progressLine[running="true"] {{ background: {COLORS['accent']}; }}
QLabel#panelTitle {{ font-size: 13px; font-weight: 700; }}
QLabel#panelMeta {{ color: {COLORS['muted']}; font-size: 10px; }}
QSplitter#workspaceSplitter::handle {{ background: transparent; width: 10px; }}
QListWidget, QScrollArea, QWidget#detailContent {{ background: transparent; border: 0; }}
QListWidget::item {{ color: #697785; border: 0; padding: 0; }}
QListWidget::item:selected {{ background: {COLORS['accent_dark']}; border-radius: 8px; }}
QWidget#listCard, QWidget#findingCard {{ background: {COLORS['panel_alt']}; border-radius: 8px; }}
QLabel#fileType {{ background: #202B35; color: {COLORS['accent']}; border-radius: 6px; font-family: "Cascadia Mono"; font-size: 9px; font-weight: 700; }}
QLabel#fileName {{ font-size: 11px; font-weight: 700; }}
QLabel#fileSize, QLabel#findingMeta {{ color: {COLORS['muted']}; font-family: "Cascadia Mono"; font-size: 8px; }}
QPushButton#iconButton {{ background: transparent; border: 0; border-radius: 5px; color: #8995A0; font-size: 16px; }}
QPushButton#iconButton:hover {{ background: #392329; color: {COLORS['danger']}; }}
QLabel[role] {{ background: #242C34; border-radius: 5px; font-size: 9px; font-weight: 700; }}
QLabel[role="resolved"] {{ background: #17362D; color: {COLORS['accent']}; }}
QLabel#findingTitle {{ font-size: 11px; font-weight: 700; }}
QLabel#findingTitleResolved {{ color: #77837F; font-size: 11px; font-weight: 600; }}
QLabel#emptyState {{ color: #64717E; font-size: 12px; }}
QLabel#detailBadge {{ background: #252D35; border-radius: 5px; font-size: 10px; font-weight: 700; }}
QLabel#detailTitle {{ font-size: 21px; font-weight: 700; }}
QLabel#detailBody {{ color: #B6C0C9; font-size: 12px; line-height: 1.55; }}
QLabel#detailBodyStrong {{ font-size: 12px; line-height: 1.55; }}
QLabel#detailSectionLabel {{ color: {COLORS['muted']}; font-size: 10px; font-weight: 700; margin-top: 4px; }}
QFrame#evidenceCard {{ background: #0D1319; border: 1px solid {COLORS['border']}; border-radius: 8px; }}
QLabel#evidenceLabel {{ color: {COLORS['accent']}; font-size: 10px; font-weight: 700; }}
QLabel#evidenceText {{ color: #D9E0E5; font-size: 12px; line-height: 1.55; }}
QLabel#evidenceSource {{ color: {COLORS['muted']}; font-family: "Cascadia Mono"; font-size: 9px; }}
QLabel#statusLabel {{ color: {COLORS['muted']}; font-size: 10px; }}
QScrollBar:vertical {{ background: transparent; width: 8px; margin: 4px 1px; }}
QScrollBar::handle:vertical {{ background: #33404D; min-height: 36px; border-radius: 4px; }}
QScrollBar::handle:vertical:hover {{ background: #465563; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
QDialog {{ background: {COLORS['app']}; }}
QLabel#dialogTitle {{ font-size: 21px; font-weight: 700; }}
QLabel#dialogDescription, QLabel#settingsNote {{ color: {COLORS['muted']}; font-size: 11px; line-height: 1.5; }}
QLabel#testStatus {{ color: {COLORS['muted']}; font-size: 10px; }}
QLabel#testStatus[ok="true"] {{ color: {COLORS['accent']}; }}
QLineEdit, QComboBox {{ min-height: 34px; background: {COLORS['panel_alt']}; border: 1px solid {COLORS['border']}; border-radius: 7px; padding: 0 10px; selection-background-color: {COLORS['accent_dark']}; }}
QLineEdit:focus, QComboBox:focus {{ border-color: {COLORS['accent']}; }}
QComboBox QAbstractItemView {{ background: {COLORS['panel_alt']}; border: 1px solid {COLORS['border']}; selection-background-color: {COLORS['accent_dark']}; }}
QCheckBox {{ spacing: 8px; }}
QDialogButtonBox QPushButton {{ min-width: 80px; min-height: 34px; background: {COLORS['panel_alt']}; border: 1px solid {COLORS['border']}; border-radius: 7px; }}
QDialogButtonBox QPushButton:hover {{ border-color: {COLORS['accent']}; }}
"""


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("明鉴")
    app.setApplicationVersion("0.7.0")
    app.setWindowIcon(QIcon(str(resource_path("assets/mingjian-v2.ico"))))
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(COLORS["app"]))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(COLORS["text"]))
    app.setPalette(palette)
    window = MingJianWindow()
    window.show()
    startup_paths = [Path(argument) for argument in sys.argv[1:] if Path(argument).is_file()]
    if startup_paths:
        QTimer.singleShot(120, lambda: window._add_paths(startup_paths, auto_review=True))
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
