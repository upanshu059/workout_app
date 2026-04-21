"""
Elite AI Workout Coach - Android App (Kivy)
Converted from PyQt6 desktop app
"""

import os
import threading
import time
from functools import partial

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.progressbar import ProgressBar
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.utils import get_color_from_hex
from kivy.metrics import dp
from kivy.core.audio import SoundLoader
from kivy.properties import StringProperty, NumericProperty

# Android TTS (text-to-speech)
try:
    from android.tts import TTS
    ANDROID = True
except ImportError:
    ANDROID = False

# Try pyttsx3 as fallback for non-Android (desktop testing)
try:
    import pyttsx3
    HAS_PYTTSX3 = True
except ImportError:
    HAS_PYTTSX3 = False

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

# --------------------------
# CONFIG
# --------------------------
START_DELAY = 10
REST_EXERCISE = 20
REST_SET = 40
REST_TYPE = 100

BG_COLOR = get_color_from_hex("#0E0E12")
ACCENT_COLOR = get_color_from_hex("#00FFC6")
CARD_COLOR = get_color_from_hex("#1E1E24")
TEXT_COLOR = get_color_from_hex("#FFFFFF")
MUTED_COLOR = get_color_from_hex("#AAAAAA")
DARK_TEXT = get_color_from_hex("#0E0E12")


# --------------------------
# TTS WRAPPER
# --------------------------
class TTSEngine:
    def __init__(self):
        self.engine = None
        if ANDROID:
            self.engine = TTS()
        elif HAS_PYTTSX3:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', 150)

    def speak(self, text):
        if self.engine is None:
            print(f"[TTS] {text}")
            return
        try:
            if ANDROID:
                self.engine.speak(text)
            elif HAS_PYTTSX3:
                self.engine.say(text)
                self.engine.runAndWait()
        except Exception as e:
            print(f"[TTS error] {e}")

    def stop(self):
        try:
            if self.engine and not ANDROID and HAS_PYTTSX3:
                self.engine.stop()
        except Exception:
            pass


# --------------------------
# WORKOUT DATA (CSV fallback)
# --------------------------
SAMPLE_WORKOUT_CSV = """workout_id,type,exercise,sets,reps,time
1,Warm Up,Jumping Jacks,2,,30
1,Warm Up,Arm Circles,2,,20
1,Strength,Push Ups,3,15,
1,Strength,Squats,3,20,
1,Strength,Lunges,3,12,
1,Core,Plank,3,,45
1,Core,Crunches,3,20,
1,Cool Down,Hamstring Stretch,1,,30
1,Cool Down,Quad Stretch,1,,30
2,Warm Up,High Knees,2,,30
2,Warm Up,Hip Circles,2,,20
2,HIIT,Burpees,4,10,
2,HIIT,Mountain Climbers,4,,30
2,HIIT,Jump Squats,4,15,
2,Core,Leg Raises,3,15,
2,Core,Russian Twists,3,20,
"""

def load_workouts():
    """Load from CSV file or fall back to sample data."""
    csv_path = os.path.join(os.path.dirname(__file__), "workouts.csv")

    if HAS_PANDAS:
        try:
            if os.path.exists(csv_path):
                return pd.read_csv(csv_path)
        except Exception:
            pass
        import io
        return pd.read_csv(io.StringIO(SAMPLE_WORKOUT_CSV))
    else:
        # Manual CSV parsing without pandas
        import io, csv
        reader = csv.DictReader(io.StringIO(SAMPLE_WORKOUT_CSV))
        rows = list(reader)
        return rows


def get_workout_ids(df):
    if HAS_PANDAS:
        return sorted(df["workout_id"].unique().tolist())
    else:
        return sorted(set(int(row["workout_id"]) for row in df))


def filter_by_workout(df, workout_id):
    if HAS_PANDAS:
        return df[df["workout_id"] == workout_id]
    else:
        return [r for r in df if int(r["workout_id"]) == workout_id]


def get_types(df):
    if HAS_PANDAS:
        return df["type"].unique().tolist()
    else:
        seen = []
        for r in df:
            if r["type"] not in seen:
                seen.append(r["type"])
        return seen


def filter_by_type(df, t):
    if HAS_PANDAS:
        return df[df["type"] == t]
    else:
        return [r for r in df if r["type"] == t]


def get_sets(df):
    if HAS_PANDAS:
        return int(df["sets"].iloc[0])
    else:
        return int(df[0]["sets"])


def get_exercises(df):
    if HAS_PANDAS:
        return df["exercise"].unique().tolist()
    else:
        seen = []
        for r in df:
            if r["exercise"] not in seen:
                seen.append(r["exercise"])
        return seen


def iter_rows(df):
    if HAS_PANDAS:
        return df.iterrows()
    else:
        return enumerate(df)


def get_val(row, key):
    if HAS_PANDAS:
        import pandas as pd
        val = row[key]
        return None if pd.isna(val) else val
    else:
        val = row.get(key, "")
        return None if val == "" else val


def get_next_exercise(df, current_idx):
    if HAS_PANDAS:
        indexes = list(df.index)
        try:
            pos = indexes.index(current_idx)
            if pos + 1 < len(indexes):
                return "Up Next: " + df.loc[indexes[pos + 1]]["exercise"]
        except Exception:
            pass
        return ""
    else:
        try:
            pos = current_idx
            if pos + 1 < len(df):
                return "Up Next: " + df[pos + 1]["exercise"]
        except Exception:
            pass
        return ""


# --------------------------
# CUSTOM WIDGETS
# --------------------------
class RoundedBox(Widget):
    """A widget with a rounded rectangle background."""
    def __init__(self, bg_color=None, radius=20, **kwargs):
        super().__init__(**kwargs)
        self.bg_color = bg_color or CARD_COLOR
        self.radius = radius
        self.bind(pos=self._redraw, size=self._redraw)

    def _redraw(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.bg_color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[self.radius])


class StyledButton(Button):
    def __init__(self, bg=None, text_color=None, **kwargs):
        super().__init__(**kwargs)
        self.bg = bg or ACCENT_COLOR
        self.text_color = text_color or DARK_TEXT
        self.background_normal = ""
        self.background_color = [0, 0, 0, 0]
        self.color = self.text_color
        self.bold = True
        self.font_size = dp(14)
        self.size_hint_y = None
        self.height = dp(48)
        self.bind(pos=self._redraw, size=self._redraw)

    def _redraw(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.bg)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(14)])


class ExerciseCard(BoxLayout):
    """A single exercise card in the timeline."""
    def __init__(self, text, active=False, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.size_hint_y = None
        self.height = dp(52)
        self.padding = [dp(14), dp(8)]

        bg = ACCENT_COLOR if active else CARD_COLOR
        lbl_color = DARK_TEXT if active else MUTED_COLOR

        with self.canvas.before:
            Color(*bg)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(14)])

        self.bind(pos=self._redraw, size=self._redraw)

        lbl = Label(
            text=text,
            color=lbl_color,
            bold=active,
            font_size=dp(14),
            halign="left",
            valign="middle"
        )
        lbl.bind(size=lbl.setter('text_size'))
        self.add_widget(lbl)

    def _redraw(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size


class SectionHeader(Label):
    def __init__(self, text, **kwargs):
        super().__init__(**kwargs)
        self.text = text
        self.color = ACCENT_COLOR
        self.bold = True
        self.font_size = dp(16)
        self.size_hint_y = None
        self.height = dp(40)
        self.halign = "left"
        self.valign = "middle"
        self.padding = [dp(4), 0]
        self.bind(size=self.setter('text_size'))


# --------------------------
# MAIN LAYOUT
# --------------------------
class WorkoutCoachLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = [dp(16), dp(24), dp(16), dp(16)]
        self.spacing = dp(12)

        with self.canvas.before:
            Color(*BG_COLOR)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

        self.df = load_workouts()
        self.workout_ids = get_workout_ids(self.df)
        self.tts = TTSEngine()
        self.bell = SoundLoader.load(os.path.join(os.path.dirname(__file__), "bell.mp3"))
        self.workout_thread = None
        self._build_ui()

    def _update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def _build_ui(self):
        # Title
        title = Label(
            text="⚡ Workout Coach",
            color=TEXT_COLOR,
            bold=True,
            font_size=dp(26),
            size_hint_y=None,
            height=dp(50),
            halign="center",
            valign="middle"
        )
        title.bind(size=title.setter('text_size'))
        self.add_widget(title)

        # Workout picker row
        picker_row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(48),
            spacing=dp(8)
        )
        picker_label = Label(
            text="Workout:",
            color=MUTED_COLOR,
            font_size=dp(14),
            size_hint_x=0.3,
            halign="left",
            valign="middle"
        )
        picker_label.bind(size=picker_label.setter('text_size'))

        self.spinner = Spinner(
            text=str(self.workout_ids[0]) if self.workout_ids else "1",
            values=[str(w) for w in self.workout_ids],
            size_hint_x=0.7,
            background_normal="",
            background_color=CARD_COLOR,
            color=TEXT_COLOR,
            font_size=dp(14)
        )
        picker_row.add_widget(picker_label)
        picker_row.add_widget(self.spinner)
        self.add_widget(picker_row)

        # Exercise label
        self.exercise_label = Label(
            text="Select a Workout",
            color=TEXT_COLOR,
            bold=True,
            font_size=dp(20),
            size_hint_y=None,
            height=dp(44),
            halign="center",
            valign="middle"
        )
        self.exercise_label.bind(size=self.exercise_label.setter('text_size'))
        self.add_widget(self.exercise_label)

        # Timer
        self.timer_label = Label(
            text="--",
            color=ACCENT_COLOR,
            bold=True,
            font_size=dp(72),
            size_hint_y=None,
            height=dp(100),
            halign="center",
            valign="middle"
        )
        self.timer_label.bind(size=self.timer_label.setter('text_size'))
        self.add_widget(self.timer_label)

        # Upcoming
        self.upcoming_label = Label(
            text="",
            color=MUTED_COLOR,
            font_size=dp(13),
            size_hint_y=None,
            height=dp(28),
            halign="center",
            valign="middle"
        )
        self.upcoming_label.bind(size=self.upcoming_label.setter('text_size'))
        self.add_widget(self.upcoming_label)

        # Progress bar
        pb_container = BoxLayout(size_hint_y=None, height=dp(16))
        self.progress = ProgressBar(max=100, value=0)
        pb_container.add_widget(self.progress)
        self.add_widget(pb_container)

        # Timeline scroll area
        scroll = ScrollView(size_hint_y=1)
        self.timeline_layout = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(6),
            padding=[0, dp(8)]
        )
        self.timeline_layout.bind(
            minimum_height=self.timeline_layout.setter("height")
        )
        scroll.add_widget(self.timeline_layout)
        self.add_widget(scroll)

        # Buttons
        btn_grid = GridLayout(
            cols=3,
            size_hint_y=None,
            height=dp(56),
            spacing=dp(8)
        )

        self.start_btn = StyledButton(text="▶ Start", bg=ACCENT_COLOR, text_color=DARK_TEXT)
        self.start_btn.bind(on_press=self.start_workout)

        self.pause_btn = StyledButton(text="⏸ Pause", bg=CARD_COLOR, text_color=TEXT_COLOR)
        self.pause_btn.bind(on_press=self.pause_workout)

        self.resume_btn = StyledButton(text="▶▶ Resume", bg=CARD_COLOR, text_color=TEXT_COLOR)
        self.resume_btn.bind(on_press=self.resume_workout)

        self.skip_btn = StyledButton(text="⏭ Skip", bg=CARD_COLOR, text_color=TEXT_COLOR)
        self.skip_btn.bind(on_press=self.skip_phase)

        self.stop_btn = StyledButton(text="⏹ Stop", bg=get_color_from_hex("#FF4444"), text_color=TEXT_COLOR)
        self.stop_btn.bind(on_press=self.stop_workout)

        btn_grid.add_widget(self.start_btn)
        btn_grid.add_widget(self.pause_btn)
        btn_grid.add_widget(self.resume_btn)
        btn_grid.add_widget(self.skip_btn)
        btn_grid.add_widget(self.stop_btn)
        btn_grid.add_widget(Widget())  # spacer

        self.add_widget(btn_grid)

    # --------------------------
    # TIMELINE RENDERING
    # --------------------------
    def render_timeline(self, current_exercise=None):
        self.timeline_layout.clear_widgets()
        workout_id = int(self.spinner.text)
        workout_df = filter_by_workout(self.df, workout_id)
        types = get_types(workout_df)

        for t in types:
            self.timeline_layout.add_widget(SectionHeader(text=t.upper()))
            type_data = filter_by_type(workout_df, t)
            exercises = get_exercises(type_data)
            for ex in exercises:
                active = (ex == current_exercise)
                card = ExerciseCard(text=ex, active=active)
                self.timeline_layout.add_widget(card)

    # --------------------------
    # WORKOUT CONTROL
    # --------------------------
    def start_workout(self, *args):
        if self.workout_thread and self.workout_thread.is_alive():
            return
        workout_id = int(self.spinner.text)
        self.render_timeline()
        self.workout_thread = WorkoutRunner(
            df=self.df,
            workout_id=workout_id,
            tts=self.tts,
            bell=self.bell,
            on_update=self._on_update,
            on_highlight=self._on_highlight,
            on_finish=self._on_finish,
            on_speak=self._on_speak,
        )
        self.workout_thread.start()

    def pause_workout(self, *args):
        if self.workout_thread:
            self.workout_thread.paused = True

    def resume_workout(self, *args):
        if self.workout_thread:
            self.workout_thread.paused = False

    def skip_phase(self, *args):
        if self.workout_thread:
            self.workout_thread.skip_phase = True

    def stop_workout(self, *args):
        if self.workout_thread:
            self.workout_thread.running = False
            self.workout_thread.paused = False
            self.workout_thread.skip_phase = True
        self.tts.stop()
        Clock.schedule_once(lambda dt: self._reset_ui(), 0.5)

    def _reset_ui(self):
        self.exercise_label.text = "Select a Workout"
        self.timer_label.text = "--"
        self.upcoming_label.text = ""
        self.progress.value = 0

    # --------------------------
    # CALLBACKS (scheduled on main thread)
    # --------------------------
    def _on_update(self, exercise, upcoming, sec, total):
        def update(dt):
            self.exercise_label.text = exercise
            self.upcoming_label.text = upcoming
            self.timer_label.text = str(sec)
            self.progress.value = int((1 - sec / total) * 100)
        Clock.schedule_once(update, 0)

    def _on_highlight(self, current_exercise):
        def update(dt):
            self.render_timeline(current_exercise)
        Clock.schedule_once(update, 0)

    def _on_finish(self):
        def update(dt):
            self.exercise_label.text = "Workout Complete 💪"
            self.timer_label.text = "✓"
        Clock.schedule_once(update, 0)

    def _on_speak(self, text):
        def speak(dt):
            self.tts.speak(text)
        Clock.schedule_once(speak, 0)


# --------------------------
# WORKOUT RUNNER THREAD
# --------------------------
class WorkoutRunner(threading.Thread):
    def __init__(self, df, workout_id, tts, bell, on_update, on_highlight, on_finish, on_speak):
        super().__init__(daemon=True)
        self.df = filter_by_workout(df, workout_id)
        self.workout_id = workout_id
        self.tts = tts
        self.bell = bell
        self.on_update = on_update
        self.on_highlight = on_highlight
        self.on_finish = on_finish
        self.on_speak = on_speak
        self.running = True
        self.paused = False
        self.skip_phase = False

    def run(self):
        self.speak(f"Starting workout {self.workout_id}")
        self.phase("Get Ready", START_DELAY)

        types = get_types(self.df)

        for t in types:
            if not self.running:
                return
            type_data = filter_by_type(self.df, t)
            sets = get_sets(type_data)

            self.speak(f"Starting {t} section")

            for s in range(sets):
                if not self.running:
                    return
                for idx, row in iter_rows(type_data):
                    if not self.running:
                        return

                    exercise = get_val(row, "exercise")
                    reps = get_val(row, "reps")
                    t_val = get_val(row, "time")
                    duration = self._get_duration(reps, t_val)

                    reps_or_seconds = (
                        f"{int(float(reps))} reps" if reps is not None
                        else f"{int(float(t_val))} seconds"
                    )

                    self.on_speak(f"Round {s+1} of {exercise}. {reps_or_seconds}.")
                    time.sleep(2.5)  # wait for TTS

                    next_ex = get_next_exercise(type_data, idx)
                    self.on_highlight(exercise)
                    self.phase(exercise, duration, next_ex)
                    self.phase("Rest", REST_EXERCISE)

                if s < sets - 1:
                    self.phase("Rest between sets", REST_SET)

            if t != types[-1]:
                self.phase("Rest before next section", REST_TYPE)

        self.speak("Workout complete. Great job!")
        self.on_finish()

    def speak(self, text):
        self.on_speak(text)
        time.sleep(max(1.5, len(text) * 0.065))

    def phase(self, label, seconds, upcoming=""):
        self.skip_phase = False
        for sec in range(seconds, 0, -1):
            while self.paused:
                time.sleep(0.1)
            if not self.running or self.skip_phase:
                return
            self.on_update(label, upcoming, sec, seconds)
            if sec <= 3:
                self.on_speak(str(sec))
                time.sleep(1)
            else:
                time.sleep(1)

        if self.bell:
            try:
                Clock.schedule_once(lambda dt: self.bell.play(), 0)
            except Exception:
                pass

    def _get_duration(self, reps, t_val):
        if t_val is not None:
            return int(float(t_val))
        elif reps is not None:
            return int(float(reps)) * 3
        return 30


# --------------------------
# KIVY APP
# --------------------------
class WorkoutCoachApp(App):
    def build(self):
        Window.clearcolor = BG_COLOR
        return WorkoutCoachLayout()

    def get_application_name(self):
        return "Workout Coach"


if __name__ == "__main__":
    WorkoutCoachApp().run()
