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
SAMPLE_CSV = """workout_id,type,exercise,reps,time,sets
1,Warmup,T-Spine,,30,2
1,Warmup,LTW,,30,2
1,Warmup,High Plank,,30,2
1,Warmup,Knee Pull,,30,2
1,Main Workout,Squats,12,,4
1,Main Workout,Pushups,12,,4
1,Main Workout,Plank,,40,4
1,Main Workout,Side to side floor touch,,40,4
1,Finisher,Russian Twists,,30,3
1,Finisher,Jumping Jacks,,30,3
1,Finisher,Hollow Hold,,30,3
2,Warmup,Open book,,40,2
2,Warmup,LTW,,40,2
2,Warmup,Prone angels,,40,2
2,Warmup,Weighted Deadbugs,,40,2
2,Main Workout,Pushups,12,,4
2,Main Workout,Jumping Ts,,40,4
2,Main Workout,Rows,12,,4
2,Main Workout,Superman Up and Down,12,,4
2,Finisher,Side plank - R,,30,3
2,Finisher,Shoulder press,,30,3
2,Finisher,Side plank - L,,30,3
3,Warmup,Hip openers,,40,2
3,Warmup,WSG,,40,2
3,Warmup,Squat to hip up,,40,2
3,Warmup,Glute bridges,,40,2
3,Main Workout,Squats Reach,15,,4
3,Main Workout,Burpees,12,,4
3,Main Workout,Deadlifts,15,,4
3,Main Workout,Split Stance Lunges,24,,4
3,Finisher,Calf Raises,,150,3
3,Finisher,High Plank Jack,,40,3
3,Finisher,Beast Hold,,40,3
4,Warmup,Open book,,30,2
4,Warmup,Knee to chest,,30,2
4,Warmup,Prone Angels,,30,2
4,Warmup,Glute bridges,,30,2
4,Main Workout,Jump Squats,15,,4
4,Main Workout,Pushups,15,,4
4,Main Workout,Skater Jumps,24,,4
4,Main Workout,Deadbugs,18,,4
4,Finisher,Mountain Climbers,,40,3
4,Finisher,Russian Twists,,40,3
4,Finisher,Plank,,40,3
5,Warmup,Knee to chest,,30,2
5,Warmup,Kneeling T spine,,30,2
5,Warmup,Prone Angels,,30,2
5,Warmup,Hip openers,,30,2
5,Activation,YTW,,30,2
5,Activation,Hip Bridges,,30,2
5,Activation,High Plank Hold,,30,2
5,Main Workout,Thrusters,,40,4
5,Main Workout,Single leg hip bridge,,40,4
5,Main Workout,Broad Jumps to Burpees,,40,4
5,Main Workout,Single leg hip bridge,,40,4
5,Finisher,Situps,,30,3
5,Finisher,Hollow Hold,,30,3
6,Warmup,Knee to chest,,30,2
6,Warmup,Bird dog,,30,2
6,Warmup,World's greatest stretch,,30,2
6,Warmup,Frogger stretch,,30,2
6,Activation,Squats,,30,2
6,Activation,Glute bridges,,30,2
6,Main Workout,Lunges,,40,4
6,Main Workout,Beast Hold,,40,4
6,Main Workout,Sumo Squats,,40,4
6,Main Workout,High plank jacks,,40,4
6,Finisher,Squat Jumps,,20,4
6,Finisher,Squat Hold,,20,4
7,Warmup,Cat and camel,,30,2
7,Warmup,Open book,,30,2
7,Warmup,Prone angels,,30,2
7,Warmup,Side lying arm rotation,,30,2
7,Activation,Inchworms,,30,2
7,Activation,YTW,,30,2
7,Activation,High plank hold,,30,2
7,Main Workout,Low plank to high plank,,40,5
7,Main Workout,Superman Up and Down,,40,5
7,Main Workout,Shoulder press,,40,5
7,Main Workout,Sit ups with punches,,40,5
7,Finisher,Side Plank hold,,30,2
7,Finisher,High knees,,30,2
8,Warmup,Cat and Camel,,40,1
8,Warmup,Thread to needle,,40,1
8,Warmup,Scapula Pushup,,40,1
8,Warmup,Chest opener to overhead stretch,,40,1
8,Warmup,Downward Dog to pushup,,40,1
8,Warmup,Chest Press,,40,1
8,Main Workout,Chest Press,,40,3
8,Main Workout,Dumbbell Squeeze,,40,3
8,Main Workout,Skull Crusher,,40,3
8,Main Workout,Overhead Extension,,40,3
8,Main Workout,Pushups,,40,3
8,Finisher,Leg raise hold to crunches,,30,2
8,Finisher,Plank,,30,2
9,Warmup,"Mountain, Beast hold, Shoulder Tap",,40,2
9,Warmup,World's greatest stretch,,40,2
9,Warmup,Reverse Lunge with Knee drive,,40,2
9,Main Workout 1,Clean,,30,3
9,Main Workout 1,Jump Squats,,30,3
9,Main Workout 1,Leg raises,,30,3
9,Main Workout 2,Renegade Rows,,30,3
9,Main Workout 2,Biceps curl,,30,3
9,Main Workout 2,Suitcase Lunges,,30,3
9,Finisher,Burpees,,60,2
9,Finisher,Plank,,60,3
10,Warmup,YTW,,30,2
10,Warmup,High plank to beast,,30,2
10,Warmup,Renegade Rows to Toe touch,,30,2
10,Warmup,cobra to Mountain,,30,2
10,Main Workout,Rows,,30,4
10,Main Workout,Superman up and down,,30,4
10,Main Workout,Zercher's curls,,30,4
10,Main Workout 2,Rows,,30,4
10,Main Workout 2,Hammer curls,,30,4
10,Main Workout 2,Double mountain climbers,,30,4
10,Finisher,Power Jacks,,30,2
10,Finisher,Front steps,,30,2
11,Warmup,Knee to chest ,,30,2
11,Warmup,Supine Twist,,30,2
11,Warmup,Hip bridge,,30,2
11,Warmup,Deadbugs,,30,2
11,Warmup,Bird dog,,30,2
11,Warmup,Side Planks,,30,2
11,Warmup,Plank,,30,2
11,Activation,Burpee to High knees,,60,1
11,Main Workout 1,High knees,,30,2
11,Main Workout 1,Crab toe touch,,30,2
11,Main Workout 1,2-Plank Jack to 4-Mountain Climbers,,30,2
11,Main Workout 2,Burpee Tuck Jump,,30,2
11,Main Workout 2,Reverse Plank in and out,,30,2
11,Main Workout 2,Jump Squat,,30,2
11,Main Workout 3,Plank to pike,,30,2
11,Main Workout 3,Thrusters,,30,2
11,Main Workout 3,Lateral Jump Burpee,,30,2
11,Finisher,The 100,100,,2
12,Warmup,Spot Jog,,30,1
12,Warmup,Butt Kicks,,30,1
12,Warmup,Arm stretch,,30,1
12,Activation,Deltoid Circles,,40,1
12,Activation,Cat and camel,,40,1
12,Activation,Thread to needle,,40,1
12,Activation,Scapula Pushups,,40,1
12,Activation,World's greatest Stretch,,40,1
12,Activation,Hip openers,,40,1
12,Activation,Squat Hold with T-spine rotation,,40,1
12,Main Workout 1,Chest Press,,60,2
12,Main Workout 1,Rows,,60,2
12,Main Workout 1,Pushups,,60,2
12,Main Workout 2,Biceps Curls,,60,2
12,Main Workout 2,Lateral Raise,,60,2
12,Main Workout 2,Shoulder Taps,,60,2
12,Finisher,Squats,,40,2
12,Finisher,Quadrockers,,30,2
12,Finisher,Glute Bridges,,30,2
13,Warmup,Spot Jog,,30,2
13,Warmup,Y raises,,30,2
13,Warmup,Shoulder Rotation,,30,2
13,Warmup,Beast Hold Shoulder Taps,,30,2
13,Main Workout,Pike Pushups,,30,4
13,Main Workout,Shoulder Press,,30,4
13,Main Workout,Front Raises,,30,4
13,Main Workout 2,Dumbbell High pull,,30,4
13,Main Workout 2,Curls,,30,4
13,Main Workout 2,Halos,,30,4
13,Finisher,Burpees,,60,3
14,Warmup,Spot Jog,,30,2
14,Warmup,Cat and Camel,,,2
14,Warmup,Supine Twist,,,2
14,Warmup,Deltoid Circles,,,2
14,Main Workout,Squat,12,,5
14,Main Workout,Frog Jumps,12,,5
14,Main Workout,Pushups,12,,5
14,Main Workout,V-hold Toe touches,12,,5
14,Finisher,Plank,,40,5
14,Finisher,Sprawls with Taps,,20,2
14,Finisher,Sprawls with Knee to Elbow,,20,2
15,Warmup,Jumping Ts,,30,2
15,Warmup,Child to Cobra,,30,2
15,Warmup,Forearm Stretch,,40,2
15,Warmup,T spine rotation,,40,2
15,Main Workout,Pushup with Rows,12,,6
15,Main Workout,Sprawls,12,,6
15,Main Workout,Superman up & down,12,,6
15,Main Workout,Leg Tuckins and Russian Twist,24,,6
15,Finisher,Star Plank Hold,,20,8
16,Warmup,Around the World,,30,2
16,Warmup,Forearm Stretch,,30,2
16,Warmup,Down dog to cobra,,30,2
16,Main workout,Row,12,,4
16,Main workout,Shrugs,18,,4
16,Main workout,Crush grip row hold,,24,4
16,Finisher,Curls,,20,4
16,Finisher,Skater Jumps,,20,4
16,Finisher,Hammer curls,,20,4
17,Warmup,Spot Jog,,30,1
17,Warmup,Swimmer's stretch,,30,1
17,Warmup,Cobra to child pose,,30,1
17,Warmup,Bridge Reach,,30,1
17,Warmup,Side Bend Lunges,,30,1
17,Warmup,Dynamic Hamstring Stretch,,40,1
17,Warmup,Bear Crawls,,30,1
17,Warmup,Spider Lunges,,30,1
17,Main Workout,Squat,,40,3
17,Main Workout,RDL,,40,3
17,Main Workout,Split Squats,,60,3
17,Main Workout,Glute Bridge hold,,40,3
17,Finisher,V-sit toe touches,,40,3
17,Finisher,Side Bridge Leg Raises,,40,3
18,Warmup,Walkout With Arms,,30,2
18,Warmup,Child pose to Pushups,,30,2
18,Warmup,Hip openers,,30,2
18,Warmup,Lateral Lunge with Arm Reach,,30,2
18,Main Workout,Dumbbell Forward Reverse Lunge R,,30,5
18,Main Workout,Dumbbell Forward Reverse Lunge L,,30,5
18,Main Workout,Floor Press,,30,5
18,Main Workout,Mountain Climbers,,30,5
18,Main Workout,Hang power Cleans,,30,5
18,Main Workout,Jump Squats,,30,5
19,Warmup,Inchwork,,30,2
19,Warmup,YTW,,30,2
19,Workout 1,Beast hold shoulder taps,,30,3
19,Workout 1,Cuban press,,30,3
19,Workout 2,Filly Press,,60,4
19,Workout 2,Clean,,30,4
19,Workout 3,Front Raises,,30,3
19,Workout 3,Lateral Raises,,60,3
19,Workout 4,Jump Squats,,20,4
19,Workout 4,High Plank Jacks,,20,4
19,Finisher,Jumping Jacks,,20,4
19,Finisher,Burpees,,20,4
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
