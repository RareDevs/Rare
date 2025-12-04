import platform as pf
from typing import Type, TypeVar

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import QCheckBox, QFormLayout, QGroupBox, QVBoxLayout

from rare.models.settings import RareAppSettings, app_settings
from rare.shared import RareCore

from .wine import WineSettings

if pf.system() in {"Linux", "FreeBSD"}:
    from .proton import ProtonSettings


class RunnerSettingsBase(QGroupBox):
    # str: option key
    environ_changed: Signal = Signal(str)
    # # bool: state, str: path
    # compat_tool_enabled: Signal = Signal(bool, str)

    def __init__(
        self,
        settings: RareAppSettings,
        rcore: RareCore,
        wine_widget: Type["WineSettings"],
        proton_widget: Type["ProtonSettings"] = None,
        parent=None,
    ):
        super().__init__(parent=parent)
        self.settings = settings
        self.app_name: str = "default"

        self.setTitle(self.tr("Compatibility"))

        # self.compat_label = QLabel(self.tr("Runner"))
        # self.compat_combo = QComboBox(self)
        # self.compat_stack = QStackedWidget(self)

        self.main_layout = QVBoxLayout(self)

        self.wine = wine_widget(settings, rcore, self)
        self.wine.environ_changed.connect(self.environ_changed)
        self.main_layout.addWidget(self.wine)
        # self.compat_layout = QFormLayout(self.compat)
        # self.compat_layout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.compat_label)
        # self.compat_layout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.compat_combo)
        # self.compat_layout.setWidget(1, QFormLayout.ItemRole.SpanningRole, self.compat_stack)
        # self.compat_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.FieldsStayAtSizeHint)

        self.ctool = False
        if proton_widget is not None:
            self.ctool = proton_widget(rcore, self)
            self.ctool.environ_changed.connect(self.environ_changed)
            self.ctool.compat_tool_enabled.connect(self.wine.compat_tool_enabled)
            self.ctool.compat_path_changed.connect(self.wine.compat_path_changed)
            self.main_layout.addWidget(self.ctool)
            # self.ctool.compat_tool_enabled.connect(self.compat_tool_enabled)

        font = self.font()
        font.setItalic(True)
        self.shader_cache_check = QCheckBox(self.tr("Use game-specific shader cache directory"), self)
        self.shader_cache_check.setFont(font)
        self.shader_cache_check.setChecked(self.settings.get_value(app_settings.local_shader_cache))
        self.shader_cache_check.checkStateChanged.connect(self._shader_cache_check_changed)

        # wine_index = self.compat_stack.addWidget(self.wine)
        # self.compat_combo.addItem("Wine", wine_index)
        # proton_index = self.compat_stack.addWidget(self.proton_tool)
        # self.compat_combo.addItem("Proton", proton_index)

        self.form_layout = QFormLayout()
        self.form_layout.addRow(self.tr("Shader cache"), self.shader_cache_check)
        self.form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self.form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.form_layout.setFormAlignment(Qt.AlignmentFlag.AlignLeading | Qt.AlignmentFlag.AlignVCenter)
        self.main_layout.addLayout(self.form_layout)

    @Slot(Qt.CheckState)
    def _shader_cache_check_changed(self, state: Qt.CheckState):
        self.settings.set_value(app_settings.local_shader_cache, state != Qt.CheckState.Unchecked)


RunnerSettingsType = TypeVar("RunnerSettingsType", bound=RunnerSettingsBase)
