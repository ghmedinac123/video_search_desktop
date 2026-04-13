"""
Tema visual de la aplicación — modo oscuro (NVR) y modo claro.

Paleta centralizada + QSS global. Toda la app usa estos colores.
Soporta toggle dark/light en tiempo real sin reiniciar.

Uso:
    from ui.theme import Theme

    app.setStyleSheet(Theme.get_stylesheet())       # Dark por defecto
    app.setStyleSheet(Theme.get_stylesheet("light")) # Cambiar a claro
    colors = Theme.colors()                          # Dict de colores actuales
"""

from __future__ import annotations


class _ColorPalette:
    """Paleta de colores para un modo específico."""

    def __init__(
        self,
        bg_primary: str,
        bg_secondary: str,
        bg_tertiary: str,
        bg_input: str,
        border: str,
        border_focus: str,
        accent: str,
        accent_hover: str,
        accent_pressed: str,
        success: str,
        warning: str,
        error: str,
        info: str,
        text_primary: str,
        text_secondary: str,
        text_muted: str,
        text_on_accent: str,
        card_bg: str,
        card_border: str,
        scrollbar_bg: str,
        scrollbar_handle: str,
    ) -> None:
        self.bg_primary = bg_primary
        self.bg_secondary = bg_secondary
        self.bg_tertiary = bg_tertiary
        self.bg_input = bg_input
        self.border = border
        self.border_focus = border_focus
        self.accent = accent
        self.accent_hover = accent_hover
        self.accent_pressed = accent_pressed
        self.success = success
        self.warning = warning
        self.error = error
        self.info = info
        self.text_primary = text_primary
        self.text_secondary = text_secondary
        self.text_muted = text_muted
        self.text_on_accent = text_on_accent
        self.card_bg = card_bg
        self.card_border = card_border
        self.scrollbar_bg = scrollbar_bg
        self.scrollbar_handle = scrollbar_handle


# ── Paletas ──

_DARK = _ColorPalette(
    bg_primary="#0a0e17",
    bg_secondary="#0f1420",
    bg_tertiary="#161d2e",
    bg_input="#1a2235",
    border="#243049",
    border_focus="#3b82f6",
    accent="#3b82f6",
    accent_hover="#2563eb",
    accent_pressed="#1d4ed8",
    success="#10b981",
    warning="#f59e0b",
    error="#ef4444",
    info="#06b6d4",
    text_primary="#e4eaf4",
    text_secondary="#7b8ba8",
    text_muted="#4a5568",
    text_on_accent="#ffffff",
    card_bg="#0f1420",
    card_border="#243049",
    scrollbar_bg="#0f1420",
    scrollbar_handle="#243049",
)

_LIGHT = _ColorPalette(
    bg_primary="#f8f9fb",
    bg_secondary="#ffffff",
    bg_tertiary="#f0f2f5",
    bg_input="#ffffff",
    border="#d1d5db",
    border_focus="#3b82f6",
    accent="#3b82f6",
    accent_hover="#2563eb",
    accent_pressed="#1d4ed8",
    success="#059669",
    warning="#d97706",
    error="#dc2626",
    info="#0891b2",
    text_primary="#111827",
    text_secondary="#6b7280",
    text_muted="#9ca3af",
    text_on_accent="#ffffff",
    card_bg="#ffffff",
    card_border="#e5e7eb",
    scrollbar_bg="#f0f2f5",
    scrollbar_handle="#d1d5db",
)


class Theme:
    """Tema centralizado con soporte dark/light."""

    _current_mode: str = "dark"
    _palettes: dict[str, _ColorPalette] = {"dark": _DARK, "light": _LIGHT}

    FONT_FAMILY: str = "Segoe UI, system-ui, sans-serif"
    FONT_SIZE: int = 13
    FONT_SIZE_SMALL: int = 11
    FONT_SIZE_TITLE: int = 15
    FONT_SIZE_HEADER: int = 18
    BORDER_RADIUS: int = 8
    BORDER_RADIUS_SMALL: int = 4
    BORDER_RADIUS_LARGE: int = 12
    SPACING: int = 8
    PADDING: int = 12

    @classmethod
    def current_mode(cls) -> str:
        """Retorna el modo actual: 'dark' o 'light'."""
        return cls._current_mode

    @classmethod
    def toggle_mode(cls) -> str:
        """Alterna entre dark y light. Retorna el nuevo modo."""
        cls._current_mode = "light" if cls._current_mode == "dark" else "dark"
        return cls._current_mode

    @classmethod
    def set_mode(cls, mode: str) -> None:
        """Establece el modo: 'dark' o 'light'."""
        if mode not in cls._palettes:
            raise ValueError(f"Modo inválido: {mode}. Usa 'dark' o 'light'.")
        cls._current_mode = mode

    @classmethod
    def colors(cls) -> _ColorPalette:
        """Retorna la paleta de colores del modo actual."""
        return cls._palettes[cls._current_mode]

    @classmethod
    def get_stylesheet(cls, mode: str | None = None) -> str:
        """
        Genera el QSS completo para toda la aplicación.

        Args:
            mode: 'dark' o 'light'. None = usa modo actual.

        Returns:
            String QSS listo para app.setStyleSheet().
        """
        if mode:
            cls.set_mode(mode)

        c = cls.colors()
        r = cls.BORDER_RADIUS
        f = cls.FONT_FAMILY

        return f"""
        /* ── Base ── */
        QMainWindow, QWidget {{
            background-color: {c.bg_primary};
            color: {c.text_primary};
            font-family: {f};
            font-size: {cls.FONT_SIZE}px;
        }}

        /* ── Labels ── */
        QLabel {{
            color: {c.text_primary};
            background: transparent;
        }}
        QLabel[class="secondary"] {{
            color: {c.text_secondary};
        }}
        QLabel[class="muted"] {{
            color: {c.text_muted};
        }}
        QLabel[class="title"] {{
            font-size: {cls.FONT_SIZE_TITLE}px;
            font-weight: 600;
        }}
        QLabel[class="header"] {{
            font-size: {cls.FONT_SIZE_HEADER}px;
            font-weight: 700;
        }}

        /* ── Botones ── */
        QPushButton {{
            background-color: {c.bg_tertiary};
            color: {c.text_primary};
            border: 1px solid {c.border};
            border-radius: {r}px;
            padding: 8px 20px;
            font-weight: 500;
            min-height: 20px;
        }}
        QPushButton:hover {{
            background-color: {c.border};
            border-color: {c.border_focus};
        }}
        QPushButton:pressed {{
            background-color: {c.accent_pressed};
        }}
        QPushButton[class="primary"] {{
            background-color: {c.accent};
            color: {c.text_on_accent};
            border: none;
        }}
        QPushButton[class="primary"]:hover {{
            background-color: {c.accent_hover};
        }}
        QPushButton[class="danger"] {{
            background-color: {c.error};
            color: {c.text_on_accent};
            border: none;
        }}

        /* ── Inputs ── */
        QLineEdit {{
            background-color: {c.bg_input};
            color: {c.text_primary};
            border: 2px solid {c.border};
            border-radius: {r}px;
            padding: 10px 14px;
            font-size: {cls.FONT_SIZE}px;
            selection-background-color: {c.accent};
        }}
        QLineEdit:focus {{
            border-color: {c.border_focus};
        }}
        QLineEdit::placeholder {{
            color: {c.text_muted};
        }}

        /* ── Sliders ── */
        QSlider::groove:horizontal {{
            height: 6px;
            background: {c.border};
            border-radius: 3px;
        }}
        QSlider::handle:horizontal {{
            width: 18px;
            height: 18px;
            margin: -6px 0;
            background: {c.accent};
            border-radius: 9px;
        }}
        QSlider::handle:horizontal:hover {{
            background: {c.accent_hover};
        }}
        QSlider::sub-page:horizontal {{
            background: {c.accent};
            border-radius: 3px;
        }}

        /* ── Progress Bars ── */
        QProgressBar {{
            background-color: {c.border};
            border: none;
            border-radius: {cls.BORDER_RADIUS_SMALL}px;
            text-align: center;
            color: {c.text_primary};
            min-height: 14px;
            max-height: 14px;
            font-size: {cls.FONT_SIZE_SMALL}px;
        }}
        QProgressBar::chunk {{
            background-color: {c.accent};
            border-radius: {cls.BORDER_RADIUS_SMALL}px;
        }}

        /* ── Radio Buttons ── */
        QRadioButton {{
            color: {c.text_primary};
            spacing: 8px;
        }}
        QRadioButton::indicator {{
            width: 18px;
            height: 18px;
            border-radius: 9px;
            border: 2px solid {c.border};
            background: {c.bg_input};
        }}
        QRadioButton::indicator:checked {{
            background: {c.accent};
            border-color: {c.accent};
        }}
        QRadioButton::indicator:hover {{
            border-color: {c.accent};
        }}

        /* ── ScrollArea ── */
        QScrollArea {{
            background: transparent;
            border: none;
        }}
        QScrollBar:vertical {{
            background: {c.scrollbar_bg};
            width: 8px;
            border-radius: 4px;
        }}
        QScrollBar::handle:vertical {{
            background: {c.scrollbar_handle};
            min-height: 30px;
            border-radius: 4px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {c.text_muted};
        }}
        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        QScrollBar:horizontal {{
            background: {c.scrollbar_bg};
            height: 8px;
            border-radius: 4px;
        }}
        QScrollBar::handle:horizontal {{
            background: {c.scrollbar_handle};
            min-width: 30px;
            border-radius: 4px;
        }}

        /* ── Frames / Cards ── */
        QFrame[class="card"] {{
            background-color: {c.card_bg};
            border: 1px solid {c.card_border};
            border-radius: {cls.BORDER_RADIUS_LARGE}px;
        }}
        QFrame[class="separator"] {{
            background-color: {c.border};
            max-height: 1px;
        }}

        /* ── StatusBar ── */
        QStatusBar {{
            background-color: {c.bg_secondary};
            color: {c.text_secondary};
            border-top: 1px solid {c.border};
            font-size: {cls.FONT_SIZE_SMALL}px;
        }}

        /* ── ToolTip ── */
        QToolTip {{
            background-color: {c.bg_tertiary};
            color: {c.text_primary};
            border: 1px solid {c.border};
            border-radius: {cls.BORDER_RADIUS_SMALL}px;
            padding: 4px 8px;
            font-size: {cls.FONT_SIZE_SMALL}px;
        }}

        /* ── Tab Widget (para futuro) ── */
        QTabWidget::pane {{
            border: 1px solid {c.border};
            background: {c.bg_primary};
        }}
        QTabBar::tab {{
            background: {c.bg_secondary};
            color: {c.text_secondary};
            padding: 8px 16px;
            border: 1px solid {c.border};
        }}
        QTabBar::tab:selected {{
            background: {c.bg_primary};
            color: {c.text_primary};
            border-bottom-color: {c.bg_primary};
        }}
        """
