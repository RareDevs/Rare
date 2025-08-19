import platform as pf
from typing import Type, TypeVar

from PySide6.QtCore import Signal, QSettings, Slot, Qt
from PySide6.QtWidgets import QGroupBox, QVBoxLayout, QCheckBox, QFormLayout

from rare.models.options import options
from .wine import WineSettings

if pf.system() in {"Linux", "FreeBSD"}:
    from .proton import ProtonSettings


class RunnerSettingsBase(QGroupBox):
    # str: option key
    environ_changed: Signal = Signal(str)
    # bool: state
    tool_enabled: Signal = Signal(bool)

    def __init__(
        self,
        wine_widget: Type['WineSettings'],
        proton_widget: Type['ProtonSettings'] = None,
        parent=None
    ):
        super().__init__(parent=parent)
        self.setTitle(self.tr("Compatibility"))
        self.settings = QSettings(self)

        self.app_name: str = "default"

        # self.compat_label = QLabel(self.tr("Runner"))
        # self.compat_combo = QComboBox(self)
        # self.compat_stack = QStackedWidget(self)

        self.wine = wine_widget(self)
        self.wine.environ_changed.connect(self.environ_changed)
        # self.compat_layout = QFormLayout(self.compat)
        # self.compat_layout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.compat_label)
        # self.compat_layout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.compat_combo)
        # self.compat_layout.setWidget(1, QFormLayout.ItemRole.SpanningRole, self.compat_stack)
        # self.compat_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.FieldsStayAtSizeHint)

        self.ctool = False
        if proton_widget is not None:
            self.ctool = proton_widget(self)
            self.ctool.environ_changed.connect(self.environ_changed)
            self.ctool.tool_enabled.connect(self.wine.tool_enabled)
            self.ctool.tool_enabled.connect(self.tool_enabled)

        font = self.font()
        font.setItalic(True)
        self.shader_cache_check = QCheckBox(self.tr("Use game-specific shader cache directory"), self)
        self.shader_cache_check.setFont(font)
        self.shader_cache_check.checkStateChanged.connect(self._shader_cache_check_changed)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.addWidget(self.wine)
        # wine_index = self.compat_stack.addWidget(self.wine)
        # self.compat_combo.addItem("Wine", wine_index)
        self.main_layout.addWidget(self.ctool)
        # proton_index = self.compat_stack.addWidget(self.proton_tool)
        # self.compat_combo.addItem("Proton", proton_index)

        self.form_layout = QFormLayout()
        self.form_layout.addRow(self.tr("Shader cache"), self.shader_cache_check)
        self.main_layout.addLayout(self.form_layout)

    @Slot(Qt.CheckState)
    def _shader_cache_check_changed(self, state: Qt.CheckState):
        self.settings.setValue(options.local_shader_cache.key, bool(state.value))

RunnerSettingsType = TypeVar("RunnerSettingsType", bound=RunnerSettingsBase)
