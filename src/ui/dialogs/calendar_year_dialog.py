# src/ui/dialogs/calendar_year_dialog.py
import os
import re
import calendar
from datetime import datetime

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QBrush
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSpinBox, QGridLayout, QFrame, QTableWidget, QTableWidgetItem
)


class CalendarYearDialog(QDialog):
    """
    Annual calendar view (12 months) showing all days with numbers.
    - Days with results are colored (best % or count).
    - Click a colored day -> emits dateSelected("YYYY-MM-DD")
    """
    dateSelected = pyqtSignal(str)  # "YYYY-MM-DD"

    def __init__(self, results, year=None, parent=None):
        super().__init__(parent)
        self.results = results or []
        self.year = year if year is not None else datetime.now().year

        # Mode:
        # False => best % (similarity)
        # True  => count occurrences
        self._mode_count = False

        # Aggregates
        self.day_best = {}   # key -> best similarity %
        self.day_count = {}  # key -> count

        self.month_tables = {}  # month -> QTableWidget

        self._init_ui()
        self._rebuild_aggregates()
        self.render_year(self.year)

    # ---------------- UI ----------------
    def _init_ui(self):
        self.setWindowTitle(f"Calendar Heatmap — {self.year}")
        self.setMinimumSize(1300, 700)

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 12, 14, 12)
        root.setSpacing(10)

        # Top bar
        top = QHBoxLayout()
        title = QLabel("Annual Calendar")
        title.setStyleSheet("font-size: 16px; font-weight: 700; color: #2C3E50;")
        top.addWidget(title)

        top.addSpacing(20)

        year_label = QLabel("Year:")
        year_label.setStyleSheet("font-weight: 600;")
        top.addWidget(year_label)

        self.year_spin = QSpinBox()
        self.year_spin.setRange(2000, 2100)
        self.year_spin.setValue(self.year)
        self.year_spin.valueChanged.connect(self._on_year_changed)
        self.year_spin.setFixedWidth(90)
        top.addWidget(self.year_spin)

        top.addStretch()

        self.mode_btn = QPushButton("Mode: best %")
        self.mode_btn.setFixedWidth(140)
        self.mode_btn.clicked.connect(self._toggle_mode)
        self.mode_btn.setStyleSheet("""
            QPushButton {
                background: white;
                border: 1px solid #CFCFCF;
                border-radius: 6px;
                padding: 8px 10px;
                font-weight: 600;
            }
            QPushButton:hover { border-color: #3498DB; }
        """)
        top.addWidget(self.mode_btn)

        root.addLayout(top)

        hint = QLabel("Click a colored day to open Clock view (24h) for that date.")
        hint.setStyleSheet("color: #7F8C8D;")
        root.addWidget(hint)

        # 12 months grid (3 rows x 4 cols)
        self.month_grid = QGridLayout()
        self.month_grid.setSpacing(12)

        for m in range(1, 13):
            frame = QFrame()
            frame.setStyleSheet("""
                QFrame { background: white; border: 1px solid #E0E0E0; border-radius: 8px; }
            """)
            f_layout = QVBoxLayout(frame)
            f_layout.setContentsMargins(10, 8, 10, 10)
            f_layout.setSpacing(6)

            month_title = QLabel(calendar.month_name[m])
            month_title.setStyleSheet("font-weight: 800; color: #2C3E50;")
            f_layout.addWidget(month_title)

            table = QTableWidget()
            table.setColumnCount(7)
            table.setRowCount(6)
            table.setHorizontalHeaderLabels(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])
            table.verticalHeader().setVisible(False)
            table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
            table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            table.setShowGrid(True)

            table.setStyleSheet("""
                QTableWidget { border: none; gridline-color: #ECECEC; }
                QHeaderView::section {
                    background: #FAFBFC;
                    border: none;
                    font-size: 9px;
                    font-weight: 800;
                    color: #34495E;
                    padding: 3px;
                }
                QTableWidget::item { padding: 0px; }
            """)

            # Make cells visible
            for c in range(7):
                table.setColumnWidth(c, 34)
            for r in range(6):
                table.setRowHeight(r, 26)

            # Click handler (month captured correctly)
            table.cellClicked.connect(lambda rr, cc, mm=m: self._on_month_cell_clicked(mm, rr, cc))

            f_layout.addWidget(table)

            self.month_tables[m] = table
            row = (m - 1) // 4
            col = (m - 1) % 4
            self.month_grid.addWidget(frame, row, col)

        root.addLayout(self.month_grid)

        self.status = QLabel("")
        self.status.setStyleSheet("color: #2980B9; font-weight: 600;")
        root.addWidget(self.status)

    # ---------------- Aggregation ----------------
    def _rebuild_aggregates(self):
        """
        Build:
          - day_best: best similarity% per day
          - day_count: count of results per day
        """
        self.day_best = {}
        self.day_count = {}

        for r in self.results:
            dt = self._parse_datetime_from_result(r)
            if dt is None:
                continue

            key = dt.strftime("%Y-%m-%d")
            score = float(r.get("similarity", 0.0)) * 100.0

            # count
            self.day_count[key] = self.day_count.get(key, 0) + 1

            # best
            prev = self.day_best.get(key)
            if prev is None or score > prev:
                self.day_best[key] = score

    def _parse_datetime_from_result(self, result):
        meta = result.get("metadata", {}) or {}

        # direct datetime
        dt = meta.get("datetime")
        if isinstance(dt, datetime):
            return dt

        # try from filename / path / s3 uri
        s = meta.get("file") or meta.get("filename") or ""
        s = str(s)
        base = os.path.basename(s.replace("\\", "/"))

        # match DEVICE_YYYYMMDD_HHMMSS.(flac|wav|mp3)
        m = re.search(r"(\w+)_(\d{8})_(\d{6})\.(flac|wav|mp3)", base, re.IGNORECASE)
        if not m:
            return None

        date_str = m.group(2)
        time_str = m.group(3)
        try:
            return datetime.strptime(date_str + time_str, "%Y%m%d%H%M%S")
        except Exception:
            return None
    def _hours_for_day(self, day_key: str):
        """Retourne la liste triée des heures (0..23) où on a des résultats pour ce jour."""
        hours = set()
        for r in self.results:
            dt = self._parse_datetime_from_result(r)
            if dt is None:
                continue
            if dt.strftime("%Y-%m-%d") == day_key:
                hours.add(dt.hour)
        return sorted(hours)

    # ---------------- Rendering ----------------
    def render_year(self, year: int):
        self.year = year
        self.setWindowTitle(f"Calendar Heatmap — {self.year}")

        cal = calendar.Calendar(firstweekday=0)  # Monday

        for month in range(1, 13):
            table = self.month_tables[month]
            table.clearContents()

            weeks = cal.monthdayscalendar(year, month)
            while len(weeks) < 6:
                weeks.append([0] * 7)

            for r, week in enumerate(weeks[:6]):
                for c, day in enumerate(week):
                    item = QTableWidgetItem("")

                    if day == 0:
                        item.setFlags(Qt.ItemFlag.NoItemFlags)
                        item.setBackground(QBrush(QColor(255, 255, 255, 0)))
                        table.setItem(r, c, item)
                        continue

                    key = f"{year:04d}-{month:02d}-{day:02d}"
                    item.setData(Qt.ItemDataRole.UserRole, key)

                    # show day number
                    item.setText(str(day))
                    item.setForeground(QBrush(QColor(44, 62, 80)))

                    if self._mode_count:
                        cnt = self.day_count.get(key, 0)
                        if cnt > 0:
                            intensity = int(50 + min(cnt, 20) / 20.0 * 200)
                            item.setBackground(QBrush(QColor(46, 204, 113, intensity)))
                            item.setToolTip(f"""
                            <div style="
                                background-color:#2C3E50;
                                color:#ECF0F1;
                                padding:6px 8px;
                                border-radius:6px;
                                font-size:11px;
                            ">
                            <b>{key}</b><br>
                            Count: {cnt}
                            </div>
                            """)

                        else:
                            item.setBackground(QBrush(QColor(240, 240, 240, 140)))
                            item.setToolTip(key)
                    else:
                        best = self.day_best.get(key)
                        if best is not None:
                            item.setBackground(self._score_to_brush(best))

                            hours = self._hours_for_day(key)
                            if len(hours) == 0:
                                hours_txt = "Hours: —"
                            elif len(hours) <= 6:
                                hours_txt = "Hours: " + ", ".join([f"{h:02d}:00" for h in hours])
                            else:
                                hours_txt = "Hours: " + ", ".join([f"{h:02d}:00" for h in hours[:6]]) + " …"

                            # Tooltip: date + heures + %
                            item.setToolTip(f"""
                            <div style="
                                background-color:#2C3E50;
                                color:#ECF0F1;
                                padding:6px 8px;
                                border-radius:6px;
                                font-size:11px;
                            ">
                            <b>{key}</b><br>
                            {hours_txt}<br>
                            Best: {best:.1f}%
                            </div>
                            """)

                        else:
                            item.setBackground(QBrush(QColor(240, 240, 240, 140)))
                            item.setToolTip(f"{key}\nNo results")


                    table.setItem(r, c, item)

        self.status.setText("")

    def _score_to_brush(self, score_pct: float) -> QBrush:
        s = max(0.0, min(100.0, float(score_pct)))
        # stronger blue when higher score
        intensity = int(40 + (s / 100.0) * 200)  # 40..240
        return QBrush(QColor(52, 152, 219, intensity))

    # ---------------- Events ----------------
    def _on_year_changed(self, year: int):
        self.render_year(year)

    def _toggle_mode(self):
        self._mode_count = not self._mode_count
        self.mode_btn.setText("Mode: count" if self._mode_count else "Mode: best %")
        self.render_year(self.year)

    def _on_month_cell_clicked(self, month: int, row: int, col: int):
        table = self.month_tables.get(month)
        if not table:
            return

        item = table.item(row, col)
        if not item:
            return

        key = item.data(Qt.ItemDataRole.UserRole)
        if not key:
            return

        # Only open clock if there are results
        if self._mode_count:
            if self.day_count.get(key, 0) == 0:
                self.status.setText(f"{key} — no results")
                return
        else:
            if key not in self.day_best:
                self.status.setText(f"{key} — no results")
                return

        self.status.setText(f"Selected: {key}")
        self.dateSelected.emit(key)
