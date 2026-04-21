"""
Elite AI Workout Coach - Android App (Kivy)
Fixed: CSV loading from app folder, responsive UI, Android TTS
"""

import os
import threading
import time

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
from kivy.metrics import dp, sp

try:
    from android import mActivity
    ANDROID = True
except ImportError:
    ANDROID = False

# try:
#     import pandas as pd
#     HAS_PANDAS = True
# except ImportError:
#     HAS_PANDAS = False

HAS_PANDAS = False    

# --------------------------
# CONFIG
# --------------------------
START_DELAY = 10
REST_EXERCISE = 20
REST_SET = 40
REST_TYPE = 100

BG_COLOR       = get_color_from_hex("#0E0E12")
ACCENT_COLOR   = get_color_from_hex("#00FFC6")
CARD_COLOR     = get_color_from_hex("#1E1E24")
TEXT_COLOR     = get_color_from_hex("#FFFFFF")
MUTED_COLOR    = get_color_from_hex("#AAAAAA")
DARK_TEXT      = get_color_from_hex("#0E0E12")
DANGER_COLOR   = get_color_from_hex("#FF4444")


# --------------------------
# TTS ENGINE
# --------------------------
class TTSEngine:
    def __init__(self):
        self.tts = None
        self._ready = False
        self.TextToSpeech = None

        if ANDROID:
            try:
                from jnius import autoclass, PythonJavaClass, java_method

                TextToSpeech = autoclass('android.speech.tts.TextToSpeech')
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                context = PythonActivity.mActivity
                self.TextToSpeech = TextToSpeech

                class TTSListener(PythonJavaClass):
                    __javainterfaces__ = ['android/speech/tts/TextToSpeech$OnInitListener']
                    def __init__(self_, callback):
                        super().__init__()
                        self_.callback = callback

                    @java_method('(I)V')
                    def onInit(self_, status):
                        self_.callback(status)

                def on_init(status):
                    if status == 0:
                        self._ready = True
                        try:
                            Locale = autoclass('java.util.Locale')
                            self.tts.setLanguage(Locale.US)
                        except Exception as e:
                            print(f"[TTS locale error] {e}")

                self._listener = TTSListener(on_init)
                self.tts = TextToSpeech(context, self._listener)

            except Exception as e:
                print(f"[TTS init error] {e}")

    def speak(self, text):
        try:
            if self.tts and self._ready:
                self.tts.speak(text, self.TextToSpeech.QUEUE_ADD, None, None)
            else:
                print(f"[TTS] {text}")
        except Exception as e:
            print(f"[TTS speak error] {e}")

    def stop(self):
        try:
            if self.tts:
                self.tts.stop()
        except Exception:
            pass


# --------------------------
# CSV LOADING
# --------------------------
SAMPLE_CSV = """workout_id,type,exercise,sets,reps,time
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

def find_csv():
    candidates = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "workouts.csv"),
        os.path.join(os.getcwd(), "workouts.csv"),
    ]
    if ANDROID:
        try:
            from android.storage import app_storage_path
            candidates.insert(0, os.path.join(app_storage_path(), "workouts.csv"))
        except Exception:
            pass
    for path in candidates:
        if os.path.exists(path):
            print(f"[CSV] Found at {path}")
            return path
    print("[CSV] Not found, using sample data")
    return None

def load_workouts():
    path = find_csv()
    if HAS_PANDAS:
        import io
        if path:
            try:
                return pd.read_csv(path)
            except Exception as e:
                print(f"[CSV read error] {e}")
        return pd.read_csv(io.StringIO(SAMPLE_CSV))
    else:
        import csv, io
        src = open(path) if path else io.StringIO(SAMPLE_CSV)
        rows = list(csv.DictReader(src))
        if path:
            src.close()
        return rows

def get_workout_ids(df):
    if HAS_PANDAS:
        return sorted(df["workout_id"].unique().tolist())
    return sorted(set(int(r["workout_id"]) for r in df))

def filter_by_workout(df, workout_id):
    if HAS_PANDAS:
        return df[df["workout_id"] == workout_id]
    return [r for r in df if int(r["workout_id"]) == workout_id]

def get_types(df):
    if HAS_PANDAS:
        return df["type"].unique().tolist()
    seen = []
    for r in df:
        if r["type"] not in seen:
            seen.append(r["type"])
    return seen

def filter_by_type(df, t):
    if HAS_PANDAS:
        return df[df["type"] == t]
    return [r for r in df if r["type"] == t]

def get_sets(df):
    if HAS_PANDAS:
        return int(df["sets"].iloc[0])
    return int(df[0]["sets"])

def get_exercises(df):
    if HAS_PANDAS:
        return df["exercise"].unique().tolist()
    seen = []
    for r in df:
        if r["exercise"] not in seen:
            seen.append(r["exercise"])
    return seen

def iter_rows(df):
    if HAS_PANDAS:
        return list(df.iterrows())
    return list(enumerate(df))

def get_val(row, key):
    if HAS_PANDAS:
        val = row[key]
        return None if pd.isna(val) else val
    val = row.get(key, "")
    return None if val == "" else val

def get_next_exercise(df, current_idx):
    rows = iter_rows(df)
    for i, (idx, row) in enumerate(rows):
        if idx == current_idx and i + 1 < len(rows):
            return "Up Next: " + str(get_val(rows[i + 1][1], "exercise"))
    return ""


# --------------------------
# WIDGETS
# --------------------------
class StyledButton(Button):
    def __init__(self, bg=None, text_color=None, **kwargs):
        super().__init__(**kwargs)
        self.bg = bg or ACCENT_COLOR
        self.text_color = text_color or DARK_TEXT
        self.background_normal = ""
        self.background_color = [0, 0, 0, 0]
        self.color = self.text_color
        self.bold = True
        self.font_size = sp(13)
        self.size_hint_y = None
        self.height = dp(44)
        self.bind(pos=self._redraw, size=self._redraw)

    def _redraw(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.bg)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(12)])


class ExerciseCard(BoxLayout):
    def __init__(self, text, active=False, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.size_hint_y = None
        self.height = dp(46)
        self.padding = [dp(12), dp(6)]

        bg = ACCENT_COLOR if active else CARD_COLOR
        lbl_color = DARK_TEXT if active else MUTED_COLOR

        with self.canvas.before:
            Color(*bg)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(12)])
        self.bind(pos=self._r, size=self._r)

        lbl = Label(
            text=text,
            color=lbl_color,
            bold=active,
            font_size=sp(13),
            halign="left",
            valign="middle"
        )
        lbl.bind(size=lbl.setter('text_size'))
        self.add_widget(lbl)

    def _r(self, *a):
        self.rect.pos = self.pos
        self.rect.size = self.size


class SectionHeader(Label):
    def __init__(self, text, **kwargs):
        super().__init__(**kwargs)
        self.text = text
        self.color = ACCENT_COLOR
        self.bold = True
        self.font_size = sp(14)
        self.size_hint_y = None
        self.height = dp(36)
        self.halign = "left"
        self.valign = "middle"
        self.bind(size=self.setter('text_size'))


# --------------------------
# MAIN LAYOUT
# --------------------------
class WorkoutCoachLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = [dp(12), dp(16), dp(12), dp(12)]
        self.spacing = dp(8)

        with self.canvas.before:
            Color(*BG_COLOR)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._bg, size=self._bg)

        self.workout_thread = None
        self.bell = None

        # Safe CSV load
        try:
            self.df = load_workouts()
            self.workout_ids = get_workout_ids(self.df)
        except Exception as e:
            print(f"[STARTUP CSV ERROR] {e}")
            import io, csv
            self.df = list(csv.DictReader(io.StringIO(SAMPLE_CSV)))
            self.workout_ids = get_workout_ids(self.df)

        # Safe TTS init
        try:
            self.tts = TTSEngine()
        except Exception as e:
            print(f"[STARTUP TTS ERROR] {e}")
            self.tts = None

        # Safe bell load
        try:
            from kivy.core.audio import SoundLoader
            bell_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bell.mp3")
            self.bell = SoundLoader.load(bell_path)
        except Exception as e:
            print(f"[STARTUP BELL ERROR] {e}")

        self._build_ui()

    def _bg(self, *a):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def _build_ui(self):
        # Title
        title = Label(
            text="⚡ Workout Coach",
            color=TEXT_COLOR,
            bold=True,
            font_size=sp(22),
            size_hint_y=None,
            height=dp(40),
            halign="center",
            valign="middle"
        )
        title.bind(size=title.setter('text_size'))
        self.add_widget(title)

        # Workout picker
        picker_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(42), spacing=dp(8))
        picker_label = Label(text="Workout:", color=MUTED_COLOR, font_size=sp(13), size_hint_x=0.35, halign="left", valign="middle")
        picker_label.bind(size=picker_label.setter('text_size'))
        self.spinner = Spinner(
            text=str(self.workout_ids[0]) if self.workout_ids else "1",
            values=[str(w) for w in self.workout_ids],
            size_hint_x=0.65,
            background_normal="",
            background_color=CARD_COLOR,
            color=TEXT_COLOR,
            font_size=sp(13)
        )
        picker_row.add_widget(picker_label)
        picker_row.add_widget(self.spinner)
        self.add_widget(picker_row)

        # Exercise label
        self.exercise_label = Label(
            text="Select a Workout",
            color=TEXT_COLOR,
            bold=True,
            font_size=sp(17),
            size_hint_y=None,
            height=dp(36),
            halign="center",
            valign="middle"
        )
        self.exercise_label.bind(size=self.exercise_label.setter('text_size'))
        self.add_widget(self.exercise_label)

        # Timer + upcoming
        timer_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(72))
        self.timer_label = Label(
            text="--", color=ACCENT_COLOR, bold=True, font_size=sp(60),
            size_hint_x=0.4, halign="center", valign="middle"
        )
        self.timer_label.bind(size=self.timer_label.setter('text_size'))
        self.upcoming_label = Label(
            text="", color=MUTED_COLOR, font_size=sp(12),
            size_hint_x=0.6, halign="left", valign="middle"
        )
        self.upcoming_label.bind(size=lambda inst, val: setattr(inst, 'text_size', (val[0], None)))
        timer_row.add_widget(self.timer_label)
        timer_row.add_widget(self.upcoming_label)
        self.add_widget(timer_row)

        # Progress bar
        pb_box = BoxLayout(size_hint_y=None, height=dp(14))
        self.progress = ProgressBar(max=100, value=0)
        pb_box.add_widget(self.progress)
        self.add_widget(pb_box)

        # Timeline scroll
        scroll = ScrollView(size_hint_y=1)
        self.timeline_layout = BoxLayout(
            orientation="vertical", size_hint_y=None,
            spacing=dp(5), padding=[0, dp(4)]
        )
        self.timeline_layout.bind(minimum_height=self.timeline_layout.setter("height"))
        scroll.add_widget(self.timeline_layout)
        self.add_widget(scroll)

        # Buttons
        btn_grid = GridLayout(cols=3, size_hint_y=None, height=dp(100), spacing=dp(6))
        self.start_btn = StyledButton(text="▶ Start", bg=ACCENT_COLOR, text_color=DARK_TEXT)
        self.start_btn.bind(on_press=self.start_workout)
        self.pause_btn = StyledButton(text="⏸ Pause", bg=CARD_COLOR, text_color=TEXT_COLOR)
        self.pause_btn.bind(on_press=self.pause_workout)
        self.resume_btn = StyledButton(text="▶▶ Resume", bg=CARD_COLOR, text_color=TEXT_COLOR)
        self.resume_btn.bind(on_press=self.resume_workout)
        self.skip_btn = StyledButton(text="⏭ Skip", bg=CARD_COLOR, text_color=TEXT_COLOR)
        self.skip_btn.bind(on_press=self.skip_phase)
        self.stop_btn = StyledButton(text="⏹ Stop", bg=DANGER_COLOR, text_color=TEXT_COLOR)
        self.stop_btn.bind(on_press=self.stop_workout)
        btn_grid.add_widget(self.start_btn)
        btn_grid.add_widget(self.pause_btn)
        btn_grid.add_widget(self.resume_btn)
        btn_grid.add_widget(self.skip_btn)
        btn_grid.add_widget(self.stop_btn)
        btn_grid.add_widget(Widget())
        self.add_widget(btn_grid)

    def render_timeline(self, current_exercise=None):
        self.timeline_layout.clear_widgets()
        workout_id = int(self.spinner.text)
        workout_df = filter_by_workout(self.df, workout_id)
        for t in get_types(workout_df):
            self.timeline_layout.add_widget(SectionHeader(text=t.upper()))
            for ex in get_exercises(filter_by_type(workout_df, t)):
                self.timeline_layout.add_widget(ExerciseCard(text=ex, active=(ex == current_exercise)))

    def start_workout(self, *a):
        if self.workout_thread and self.workout_thread.is_alive():
            return
        workout_id = int(self.spinner.text)
        self.render_timeline()
        self.workout_thread = WorkoutRunner(
            df=self.df, workout_id=workout_id, tts=self.tts, bell=self.bell,
            on_update=self._on_update, on_highlight=self._on_highlight,
            on_finish=self._on_finish, on_speak=self._on_speak,
        )
        self.workout_thread.start()

    def pause_workout(self, *a):
        if self.workout_thread: self.workout_thread.paused = True

    def resume_workout(self, *a):
        if self.workout_thread: self.workout_thread.paused = False

    def skip_phase(self, *a):
        if self.workout_thread: self.workout_thread.skip_phase = True

    def stop_workout(self, *a):
        if self.workout_thread:
            self.workout_thread.running = False
            self.workout_thread.paused = False
            self.workout_thread.skip_phase = True
        if self.tts:
            self.tts.stop()
        Clock.schedule_once(lambda dt: self._reset_ui(), 0.3)

    def _reset_ui(self):
        self.exercise_label.text = "Select a Workout"
        self.timer_label.text = "--"
        self.upcoming_label.text = ""
        self.progress.value = 0

    def _on_update(self, exercise, upcoming, sec, total):
        def u(dt):
            self.exercise_label.text = exercise
            self.upcoming_label.text = upcoming
            self.timer_label.text = str(sec)
            self.progress.value = int((1 - sec / total) * 100)
        Clock.schedule_once(u, 0)

    def _on_highlight(self, ex):
        Clock.schedule_once(lambda dt: self.render_timeline(ex), 0)

    def _on_finish(self):
        def u(dt):
            self.exercise_label.text = "Workout Complete 💪"
            self.timer_label.text = "✓"
        Clock.schedule_once(u, 0)

    def _on_speak(self, text):
        if self.tts:
            Clock.schedule_once(lambda dt: self.tts.speak(text), 0)


# --------------------------
# WORKOUT RUNNER
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
        self.announce(f"Starting workout {self.workout_id}")
        self.phase("Get Ready", START_DELAY)
        types = get_types(self.df)

        for t in types:
            if not self.running: return
            type_data = filter_by_type(self.df, t)
            sets = get_sets(type_data)
            self.announce(f"Starting {t} section")

            for s in range(sets):
                if not self.running: return
                rows = iter_rows(type_data)
                for idx, (df_idx, row) in enumerate(rows):
                    if not self.running: return
                    exercise = get_val(row, "exercise")
                    reps = get_val(row, "reps")
                    t_val = get_val(row, "time")
                    duration = self._get_duration(reps, t_val)
                    reps_or_seconds = (
                        f"{int(float(reps))} reps" if reps is not None
                        else f"{int(float(t_val))} seconds"
                    )
                    self.announce(f"Round {s + 1}. {exercise}. {reps_or_seconds}.")
                    next_ex = get_next_exercise(type_data, df_idx)
                    self.on_highlight(exercise)
                    self.phase(exercise, duration, next_ex)
                    self.announce("Rest")
                    self.phase("Rest", REST_EXERCISE)

                if s < sets - 1:
                    self.announce("Rest between sets")
                    self.phase("Rest between sets", REST_SET)

            if t != types[-1]:
                self.announce("Rest before next section")
                self.phase("Rest before next section", REST_TYPE)

        self.announce("Workout complete. Great job!")
        self.on_finish()

    def announce(self, text):
        self.on_speak(text)
        time.sleep(max(1.2, len(text) * 0.06))

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
        if self.bell:
            try:
                Clock.schedule_once(lambda dt: self.bell.play(), 0)
            except Exception:
                pass

    def _get_duration(self, reps, t_val):
        if t_val is not None: return int(float(t_val))
        elif reps is not None: return int(float(reps)) * 3
        return 30


# --------------------------
# APP
# --------------------------
class WorkoutCoachApp(App):
    def build(self):
        Window.clearcolor = BG_COLOR
        return WorkoutCoachLayout()

    def get_application_name(self):
        return "Workout Coach"


if __name__ == "__main__":
    WorkoutCoachApp().run()
