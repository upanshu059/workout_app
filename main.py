"""
IRON COACH - Android Workout App
Design: Neon Green — dark cards, electric green accents, estimated time
"""

import os
import threading
import time
import csv
import io

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition
from kivy.uix.progressbar import ProgressBar
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle, Rectangle, Line, Ellipse
from kivy.utils import get_color_from_hex
from kivy.metrics import dp, sp
from kivy.core.text import LabelBase

try:
    from android import mActivity
    ANDROID = True
except ImportError:
    ANDROID = False

# --------------------------
# REGISTER EMOJI FONT
# --------------------------
FONT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "NotoEmoji.ttf")
if os.path.exists(FONT_PATH):
    try:
        LabelBase.register(name="NotoEmoji", fn_regular=FONT_PATH)
        HAS_EMOJI_FONT = True
    except Exception:
        HAS_EMOJI_FONT = False
else:
    HAS_EMOJI_FONT = False

# --------------------------
# THEME — Neon Green
# --------------------------
BG          = get_color_from_hex("#080808")
BG2         = get_color_from_hex("#0D0D0D")
CARD        = get_color_from_hex("#111111")
CARD2       = get_color_from_hex("#161616")
CARD3       = get_color_from_hex("#1A1A1A")
GREEN       = get_color_from_hex("#00FF88")
GREEN_DIM   = get_color_from_hex("#00CC6A")
GREEN_BG    = get_color_from_hex("#001A0D")
GREEN_CARD  = get_color_from_hex("#00120A")
WHITE       = get_color_from_hex("#FFFFFF")
GREY        = get_color_from_hex("#666666")
GREY2       = get_color_from_hex("#333333")
GREY3       = get_color_from_hex("#222222")
RED         = get_color_from_hex("#FF3D3D")
AMBER       = get_color_from_hex("#FFB800")
BLACK       = get_color_from_hex("#000000")

# --------------------------
# CONFIG
# --------------------------
START_DELAY   = 10
REST_EXERCISE = 20
REST_SET      = 40
REST_TYPE     = 100

# --------------------------
# SAMPLE CSV
# --------------------------
SAMPLE_CSV = """workout_id,type,exercise,reps,time,sets,workout_name
1,Warmup,T-Spine,,30,2,Full body - Core
1,Warmup,LTW,,30,2,Full body - Core
1,Warmup,High Plank,,30,2,Full body - Core
1,Warmup,Knee Pull,,30,2,Full body - Core
1,Main Workout,Squats,12,,4,Full body - Core
1,Main Workout,Pushups,12,,4,Full body - Core
1,Main Workout,Plank,,40,4,Full body - Core
1,Main Workout,Side to side floor touch,,40,4,Full body - Core
1,Finisher,Russian Twists,,30,3,Full body - Core
1,Finisher,Jumping Jacks,,30,3,Full body - Core
1,Finisher,Hollow Hold,,30,3,Full body - Core
2,Warmup,Open book,,40,2,Chest - Back - Shoulders
2,Warmup,LTW,,40,2,Chest - Back - Shoulders
2,Warmup,Prone angels,,40,2,Chest - Back - Shoulders
2,Warmup,Weighted Deadbugs,,40,2,Chest - Back - Shoulders
2,Main Workout,Pushups,12,,4,Chest - Back - Shoulders
2,Main Workout,Jumping Ts,,40,4,Chest - Back - Shoulders
2,Main Workout,Rows,12,,4,Chest - Back - Shoulders
2,Main Workout,Superman Up and Down,12,,4,Chest - Back - Shoulders
2,Finisher,Side plank - R,,30,3,Chest - Back - Shoulders
2,Finisher,Shoulder press,,30,3,Chest - Back - Shoulders
2,Finisher,Side plank - L,,30,3,Chest - Back - Shoulders
3,Warmup,Hip openers,,40,2,Legs
3,Warmup,WSG,,40,2,Legs
3,Warmup,Squat to hip up,,40,2,Legs
3,Warmup,Glute bridges,,40,2,Legs
3,Main Workout,Squats Reach,15,,4,Legs
3,Main Workout,Burpees,12,,4,Legs
3,Main Workout,Deadlifts,15,,4,Legs
3,Main Workout,Split Stance Lunges,24,,4,Legs
3,Finisher,Calf Raises,,150,3,Legs
3,Finisher,High Plank Jack,,40,3,Legs
3,Finisher,Beast Hold,,40,3,Legs
4,Warmup,Open book,,30,2,Legs with pushups
4,Warmup,Knee to chest,,30,2,Legs with pushups
4,Warmup,Prone Angels,,30,2,Legs with pushups
4,Warmup,Glute bridges,,30,2,Legs with pushups
4,Main Workout,Jump Squats,15,,4,Legs with pushups
4,Main Workout,Pushups,15,,4,Legs with pushups
4,Main Workout,Skater Jumps,24,,4,Legs with pushups
4,Main Workout,Deadbugs,18,,4,Legs with pushups
4,Finisher,Mountain Climbers,,40,3,Legs with pushups
4,Finisher,Russian Twists,,40,3,Legs with pushups
4,Finisher,Plank,,40,3,Legs with pushups
5,Warmup,Knee to chest,,30,2,Legs and Core
5,Warmup,Kneeling T spine,,30,2,Legs and Core
5,Warmup,Prone Angels,,30,2,Legs and Core
5,Warmup,Hip openers,,30,2,Legs and Core
5,Activation,YTW,,30,2,Legs and Core
5,Activation,Hip Bridges,,30,2,Legs and Core
5,Activation,High Plank Hold,,30,2,Legs and Core
5,Main Workout,Thrusters,,40,4,Legs and Core
5,Main Workout,Single leg hip bridge,,40,4,Legs and Core
5,Main Workout,Broad Jumps to Burpees,,40,4,Legs and Core
5,Main Workout,Single leg hip bridge,,40,4,Legs and Core
5,Finisher,Situps,,30,3,Legs and Core
5,Finisher,Hollow Hold,,30,3,Legs and Core
6,Warmup,Knee to chest,,30,2,Explosive Legs
6,Warmup,Bird dog,,30,2,Explosive Legs
6,Warmup,World's greatest stretch,,30,2,Explosive Legs
6,Warmup,Frogger stretch,,30,2,Explosive Legs
6,Activation,Squats,,30,2,Explosive Legs
6,Activation,Glute bridges,,30,2,Explosive Legs
6,Main Workout,Lunges,,40,4,Explosive Legs
6,Main Workout,Beast Hold,,40,4,Explosive Legs
6,Main Workout,Sumo Squats,,40,4,Explosive Legs
6,Main Workout,High plank jacks,,40,4,Explosive Legs
6,Finisher,Squat Jumps,,20,4,Explosive Legs
6,Finisher,Squat Hold,,20,4,Explosive Legs
7,Warmup,Cat and camel,,30,2,Core
7,Warmup,Open book,,30,2,Core
7,Warmup,Prone angels,,30,2,Core
7,Warmup,Side lying arm rotation,,30,2,Core
7,Activation,Inchworms,,30,2,Core
7,Activation,YTW,,30,2,Core
7,Activation,High plank hold,,30,2,Core
7,Main Workout,Low plank to high plank,,40,5,Core
7,Main Workout,Superman Up and Down,,40,5,Core
7,Main Workout,Shoulder press,,40,5,Core
7,Main Workout,Sit ups with punches,,40,5,Core
7,Finisher,Side Plank hold,,30,2,Core
7,Finisher,High knees,,30,2,Core
8,Warmup,Cat and Camel,,40,1,Chest
8,Warmup,Thread to needle,,40,1,Chest
8,Warmup,Scapula Pushup,,40,1,Chest
8,Warmup,Chest opener to overhead stretch,,40,1,Chest
8,Warmup,Downward Dog to pushup,,40,1,Chest
8,Warmup,Chest Press,,40,1,Chest
8,Main Workout,Chest Press,,40,3,Chest
8,Main Workout,Dumbbell Squeeze,,40,3,Chest
8,Main Workout,Skull Crusher,,40,3,Chest
8,Main Workout,Overhead Extension,,40,3,Chest
8,Main Workout,Pushups,,40,3,Chest
8,Finisher,Leg raise hold to crunches,,30,2,Chest
8,Finisher,Plank,,30,2,Chest
9,Warmup,"Mountain, Beast hold, Shoulder Tap",,40,2,Clean and Curls
9,Warmup,World's greatest stretch,,40,2,Clean and Curls
9,Warmup,Reverse Lunge with Knee drive,,40,2,Clean and Curls
9,Main Workout 1,Clean,,30,3,Clean and Curls
9,Main Workout 1,Jump Squats,,30,3,Clean and Curls
9,Main Workout 1,Leg raises,,30,3,Clean and Curls
9,Main Workout 2,Renegade Rows,,30,3,Clean and Curls
9,Main Workout 2,Biceps curl,,30,3,Clean and Curls
9,Main Workout 2,Suitcase Lunges,,30,3,Clean and Curls
9,Finisher,Burpees,,60,2,Clean and Curls
9,Finisher,Plank,,60,3,Clean and Curls
10,Warmup,YTW,,30,2,Arms like Hell
10,Warmup,High plank to beast,,30,2,Arms like Hell
10,Warmup,Renegade Rows to Toe touch,,30,2,Arms like Hell
10,Warmup,cobra to Mountain,,30,2,Arms like Hell
10,Main Workout,Rows,,30,4,Arms like Hell
10,Main Workout,Superman up and down,,30,4,Arms like Hell
10,Main Workout,Zercher's curls,,30,4,Arms like Hell
10,Main Workout 2,Rows,,30,4,Arms like Hell
10,Main Workout 2,Hammer curls,,30,4,Arms like Hell
10,Main Workout 2,Double mountain climbers,,30,4,Arms like Hell
10,Finisher,Power Jacks,,30,2,Arms like Hell
10,Finisher,Front steps,,30,2,Arms like Hell
11,Warmup,Knee to chest ,,30,2,Get Fast
11,Warmup,Supine Twist,,30,2,Get Fast
11,Warmup,Hip bridge,,30,2,Get Fast
11,Warmup,Deadbugs,,30,2,Get Fast
11,Warmup,Bird dog,,30,2,Get Fast
11,Warmup,Side Planks,,30,2,Get Fast
11,Warmup,Plank,,30,2,Get Fast
11,Activation,Burpee to High knees,,60,1,Get Fast
11,Main Workout 1,High knees,,30,2,Get Fast
11,Main Workout 1,Crab toe touch,,30,2,Get Fast
11,Main Workout 1,2-Plank Jack to 4-Mountain Climbers,,30,2,Get Fast
11,Main Workout 2,Burpee Tuck Jump,,30,2,Get Fast
11,Main Workout 2,Reverse Plank in and out,,30,2,Get Fast
11,Main Workout 2,Jump Squat,,30,2,Get Fast
11,Main Workout 3,Plank to pike,,30,2,Get Fast
11,Main Workout 3,Thrusters,,30,2,Get Fast
11,Main Workout 3,Lateral Jump Burpee,,30,2,Get Fast
11,Finisher,The 100,100,,2,Get Fast
12,Warmup,Spot Jog,,30,1,Upper Body
12,Warmup,Butt Kicks,,30,1,Upper Body
12,Warmup,Arm stretch,,30,1,Upper Body
12,Activation,Deltoid Circles,,40,1,Upper Body
12,Activation,Cat and camel,,40,1,Upper Body
12,Activation,Thread to needle,,40,1,Upper Body
12,Activation,Scapula Pushups,,40,1,Upper Body
12,Activation,World's greatest Stretch,,40,1,Upper Body
12,Activation,Hip openers,,40,1,Upper Body
12,Activation,Squat Hold with T-spine rotation,,40,1,Upper Body
12,Main Workout 1,Chest Press,,60,2,Upper Body
12,Main Workout 1,Rows,,60,2,Upper Body
12,Main Workout 1,Pushups,,60,2,Upper Body
12,Main Workout 2,Biceps Curls,,60,2,Upper Body
12,Main Workout 2,Lateral Raise,,60,2,Upper Body
12,Main Workout 2,Shoulder Taps,,60,2,Upper Body
12,Finisher,Squats,,40,2,Upper Body
12,Finisher,Quadrockers,,30,2,Upper Body
12,Finisher,Glute Bridges,,30,2,Upper Body
13,Warmup,Spot Jog,,30,2,Shoulders
13,Warmup,Y raises,,30,2,Shoulders
13,Warmup,Shoulder Rotation,,30,2,Shoulders
13,Warmup,Beast Hold Shoulder Taps,,30,2,Shoulders
13,Main Workout,Pike Pushups,,30,4,Shoulders
13,Main Workout,Shoulder Press,,30,4,Shoulders
13,Main Workout,Front Raises,,30,4,Shoulders
13,Main Workout 2,Dumbbell High pull,,30,4,Shoulders
13,Main Workout 2,Curls,,30,4,Shoulders
13,Main Workout 2,Halos,,30,4,Shoulders
13,Finisher,Burpees,,60,3,Shoulders
14,Warmup,Spot Jog,,30,2,Legs - Core
14,Warmup,Cat and Camel,,30,2,Legs - Core
14,Warmup,Supine Twist,,30,2,Legs - Core
14,Warmup,Deltoid Circles,,30,2,Legs - Core
14,Main Workout,Squat,12,,5,Legs - Core
14,Main Workout,Frog Jumps,12,,5,Legs - Core
14,Main Workout,Pushups,12,,5,Legs - Core
14,Main Workout,V-hold Toe touches,12,,5,Legs - Core
14,Finisher,Plank,,40,5,Legs - Core
14,Finisher,Sprawls with Taps,,20,2,Legs - Core
14,Finisher,Sprawls with Knee to Elbow,,20,2,Legs - Core
15,Warmup,Jumping Ts,,30,2,Endurance
15,Warmup,Child to Cobra,,30,2,Endurance
15,Warmup,Forearm Stretch,,40,2,Endurance
15,Warmup,T spine rotation,,40,2,Endurance
15,Main Workout,Pushup with Rows,12,,6,Endurance
15,Main Workout,Sprawls,12,,6,Endurance
15,Main Workout,Superman up & down,12,,6,Endurance
15,Main Workout,Leg Tuckins and Russian Twist,24,,6,Endurance
15,Finisher,Star Plank Hold,,20,8,Endurance
16,Warmup,Around the World,,30,2,Back to back
16,Warmup,Forearm Stretch,,30,2,Back to back
16,Warmup,Down dog to cobra,,30,2,Back to back
16,Main workout,Row,12,,4,Back to back
16,Main workout,Shrugs,18,,4,Back to back
16,Main workout,Crush grip row hold,,24,4,Back to back
16,Finisher,Curls,,20,4,Back to back
16,Finisher,Skater Jumps,,20,4,Back to back
16,Finisher,Hammer curls,,20,4,Back to back
17,Warmup,Spot Jog,,30,1,Legs and Legs
17,Warmup,Swimmer's stretch,,30,1,Legs and Legs
17,Warmup,Cobra to child pose,,30,1,Legs and Legs
17,Warmup,Bridge Reach,,30,1,Legs and Legs
17,Warmup,Side Bend Lunges,,30,1,Legs and Legs
17,Warmup,Dynamic Hamstring Stretch,,40,1,Legs and Legs
17,Warmup,Bear Crawls,,30,1,Legs and Legs
17,Warmup,Spider Lunges,,30,1,Legs and Legs
17,Main Workout,Squat,,40,3,Legs and Legs
17,Main Workout,RDL,,40,3,Legs and Legs
17,Main Workout,Split Squats,,60,3,Legs and Legs
17,Main Workout,Glute Bridge hold,,40,3,Legs and Legs
17,Finisher,V-sit toe touches,,40,3,Legs and Legs
17,Finisher,Side Bridge Leg Raises,,40,3,Legs and Legs
18,Warmup,Walkout With Arms,,30,2,Clean and Lunges
18,Warmup,Child pose to Pushups,,30,2,Clean and Lunges
18,Warmup,Hip openers,,30,2,Clean and Lunges
18,Warmup,Lateral Lunge with Arm Reach,,30,2,Clean and Lunges
18,Main Workout,Dumbbell Forward Reverse Lunge R,,30,5,Clean and Lunges
18,Main Workout,Dumbbell Forward Reverse Lunge L,,30,5,Clean and Lunges
18,Main Workout,Floor Press,,30,5,Clean and Lunges
18,Main Workout,Mountain Climbers,,30,5,Clean and Lunges
18,Main Workout,Hang power Cleans,,30,5,Clean and Lunges
18,Main Workout,Jump Squats,,30,5,Clean and Lunges
19,Warmup,Inchwork,,30,2,Shoulders off
19,Warmup,YTW,,30,2,Shoulders off
19,Workout 1,Beast hold shoulder taps,,30,3,Shoulders off
19,Workout 1,Cuban press,,30,3,Shoulders off
19,Workout 2,Filly Press,,60,4,Shoulders off
19,Workout 2,Clean,,30,4,Shoulders off
19,Workout 3,Front Raises,,30,3,Shoulders off
19,Workout 3,Lateral Raises,,60,3,Shoulders off
19,Workout 4,Jump Squats,,20,4,Shoulders off
19,Workout 4,High Plank Jacks,,20,4,Shoulders off
19,Finisher,Jumping Jacks,,20,4,Shoulders off
19,Finisher,Burpees,,20,4,Shoulders off
"""

# --------------------------
# DATA HELPERS
# --------------------------
def find_csv():
    candidates = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "workouts.csv"),
        os.path.join(os.getcwd(), "workouts.csv"),
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None

def load_workouts():
    path = find_csv()
    src = open(path, newline='') if path else io.StringIO(SAMPLE_CSV)
    rows = list(csv.DictReader(src))
    if path:
        src.close()
    return rows

def get_workout_ids(rows):
    seen = []
    for r in rows:
        wid = int(r["workout_id"])
        if wid not in seen:
            seen.append(wid)
    return sorted(seen)   # sorted by ID

def get_workout_name(rows, wid):
    for r in rows:
        if int(r["workout_id"]) == wid:
            return r.get("workout_name", f"Workout {wid}")
    return f"Workout {wid}"

def filter_workout(rows, wid):
    return [r for r in rows if int(r["workout_id"]) == wid]

def get_types(rows):
    seen = []
    for r in rows:
        if r["type"] not in seen:
            seen.append(r["type"])
    return seen

def filter_type(rows, t):
    return [r for r in rows if r["type"] == t]

def get_sets(rows):
    return int(rows[0]["sets"])

def get_exercises(rows):
    seen = []
    for r in rows:
        if r["exercise"] not in seen:
            seen.append(r["exercise"])
    return seen

def get_val(row, key):
    v = row.get(key, "").strip()
    return None if v == "" else v

def get_duration(row):
    t = get_val(row, "time")
    r = get_val(row, "reps")
    if t: return int(float(t))
    if r: return int(float(r)) * 3
    return 30

def estimate_workout_minutes(rows):
    total = START_DELAY
    types = get_types(rows)
    for t in types:
        td = filter_type(rows, t)
        sets_total = get_sets(td)
        exercises = get_exercises(td)
        for ex in exercises:
            ex_row = next(r for r in td if r["exercise"] == ex)
            dur = get_duration(ex_row)
            total += sets_total * (dur + REST_EXERCISE)
        if sets_total > 1:
            total += (sets_total - 1) * REST_SET
    total += (len(types) - 1) * REST_TYPE
    return max(1, total // 60)

def count_exercises(rows):
    return len(get_exercises(rows))

def count_total_sets(rows):
    types = get_types(rows)
    total = 0
    for t in types:
        td = filter_type(rows, t)
        total += get_sets(td) * len(get_exercises(td))
    return total

def get_next_exercise(rows, current_idx):
    if current_idx + 1 < len(rows):
        return rows[current_idx + 1]["exercise"]
    return ""

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
                    def __init__(self_, cb):
                        super().__init__()
                        self_.cb = cb
                    @java_method('(I)V')
                    def onInit(self_, status):
                        self_.cb(status)

                def on_init(status):
                    if status == 0:
                        self._ready = True
                        try:
                            Locale = autoclass('java.util.Locale')
                            self.tts.setLanguage(Locale.US)
                        except Exception as e:
                            print(f"[TTS locale] {e}")

                self._listener = TTSListener(on_init)
                self.tts = TextToSpeech(context, self._listener)
            except Exception as e:
                print(f"[TTS init] {e}")

    def speak(self, text):
        try:
            if self.tts and self._ready:
                self.tts.speak(text, self.TextToSpeech.QUEUE_ADD, None, None)
            else:
                print(f"[TTS] {text}")
        except Exception as e:
            print(f"[TTS speak] {e}")

    def stop(self):
        try:
            if self.tts:
                self.tts.stop()
        except Exception:
            pass

# --------------------------
# CUSTOM WIDGETS
# --------------------------
def make_bg(widget, color):
    with widget.canvas.before:
        c = Color(*color)
        r = Rectangle(pos=widget.pos, size=widget.size)
    widget.bind(
        pos=lambda *a: setattr(r, 'pos', widget.pos),
        size=lambda *a: setattr(r, 'size', widget.size)
    )

def make_rounded_bg(widget, color, radius=12):
    with widget.canvas.before:
        c = Color(*color)
        r = RoundedRectangle(pos=widget.pos, size=widget.size, radius=[dp(radius)])
    widget.bind(
        pos=lambda *a: setattr(r, 'pos', widget.pos),
        size=lambda *a: setattr(r, 'size', widget.size)
    )

class NeonButton(Button):
    def __init__(self, filled=True, **kwargs):
        super().__init__(**kwargs)
        self.filled = filled
        self.background_normal = ""
        self.background_color = [0, 0, 0, 0]
        self.color = BLACK if filled else GREEN
        self.bold = True
        self.font_size = sp(13)
        self.size_hint_y = None
        self.height = dp(48)
        self._rect = None
        self._line = None
        self.bind(pos=self._draw, size=self._draw)

    def _draw(self, *a):
        self.canvas.before.clear()
        with self.canvas.before:
            if self.filled:
                Color(*GREEN)
                RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(8)])
            else:
                Color(*GREEN)
                Line(rounded_rectangle=(self.x, self.y, self.width, self.height, dp(8)), width=1.2)

    def on_press(self):
        from kivy.animation import Animation
        anim = Animation(opacity=0.6, duration=0.04) + Animation(opacity=1.0, duration=0.04)
        anim.start(self)


class SmallButton(Button):
    def __init__(self, bg=None, fg=None, radius=8, **kwargs):
        super().__init__(**kwargs)
        self._bg = bg or CARD2
        self._fg = fg or WHITE
        self._radius = radius
        self.background_normal = ""
        self.background_color = [0, 0, 0, 0]
        self.color = self._fg
        self.bold = True
        self.font_size = sp(16)
        self.size_hint_y = None
        self.height = dp(52)
        self.bind(pos=self._draw, size=self._draw)

    def _draw(self, *a):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self._bg)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(self._radius)])

    def on_press(self):
        from kivy.animation import Animation
        anim = Animation(opacity=0.6, duration=0.04) + Animation(opacity=1.0, duration=0.04)
        anim.start(self)


class TagLabel(BoxLayout):
    def __init__(self, text, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_x = None
        self.width = max(dp(60), dp(len(text) * 7 + 16))
        self.size_hint_y = None
        self.height = dp(22)
        make_rounded_bg(self, GREEN_BG, radius=4)
        lbl = Label(
            text=text,
            color=GREEN,
            bold=True,
            font_size=sp(10),
            halign="center",
            valign="middle"
        )
        lbl.bind(size=lbl.setter('text_size'))
        self.add_widget(lbl)


class StatBlock(BoxLayout):
    def __init__(self, value, label, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.spacing = dp(2)
        val_lbl = Label(
            text=str(value),
            color=GREEN,
            bold=True,
            font_size=sp(20),
            halign="center",
            valign="middle",
            size_hint_y=None,
            height=dp(28)
        )
        val_lbl.bind(size=val_lbl.setter('text_size'))
        lbl = Label(
            text=label.upper(),
            color=GREY,
            font_size=sp(9),
            halign="center",
            valign="middle",
            size_hint_y=None,
            height=dp(16)
        )
        lbl.bind(size=lbl.setter('text_size'))
        self.add_widget(val_lbl)
        self.add_widget(lbl)


class WorkoutCard(BoxLayout):
    def __init__(self, wid, name, ex_count, set_count, est_min, types, on_tap, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.size_hint_y = None
        self.height = dp(170)
        self.padding = [dp(16), dp(14), dp(16), dp(14)]
        self.spacing = dp(10)

        with self.canvas.before:
            Color(*CARD)
            self.bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(14)])
            Color(*GREEN)
            self.border_rect = Line(
                rounded_rectangle=(self.x, self.y, self.width, self.height, dp(14)),
                width=0.8
            )
        self.bind(pos=self._draw, size=self._draw)

        # Top row: name + workout number badge
        top_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(32))
        name_lbl = Label(
            text=name.upper(),
            color=WHITE,
            bold=True,
            font_size=sp(16),
            halign="left",
            valign="middle",
            size_hint_x=1
        )
        name_lbl.bind(size=name_lbl.setter('text_size'))

        badge = BoxLayout(size_hint_x=None, width=dp(28), size_hint_y=None, height=dp(28))
        make_rounded_bg(badge, GREEN_BG, radius=6)
        badge_lbl = Label(
            text=str(wid),
            color=GREEN,
            bold=True,
            font_size=sp(12),
            halign="center",
            valign="middle"
        )
        badge_lbl.bind(size=badge_lbl.setter('text_size'))
        badge.add_widget(badge_lbl)

        top_row.add_widget(name_lbl)
        top_row.add_widget(badge)

        # Stats row
        stats_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(46), spacing=dp(8))
        stats_row.add_widget(StatBlock(ex_count, "exercises"))
        # Divider
        div = Widget(size_hint_x=None, width=dp(1))
        with div.canvas:
            Color(*GREY2)
            Rectangle(pos=div.pos, size=div.size)
        div.bind(pos=lambda *a: None, size=lambda *a: None)
        stats_row.add_widget(div)
        stats_row.add_widget(StatBlock(set_count, "sets"))
        div2 = Widget(size_hint_x=None, width=dp(1))
        with div2.canvas:
            Color(*GREY2)
            Rectangle(pos=div2.pos, size=div2.size)
        div2.bind(pos=lambda *a: None, size=lambda *a: None)
        stats_row.add_widget(div2)
        stats_row.add_widget(StatBlock(f"{est_min}m", "est. time"))

        # Tags row
        tags_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(22), spacing=dp(6))
        for t in types[:4]:
            tags_row.add_widget(TagLabel(text=t))
        tags_row.add_widget(Widget())

        # Start button
        btn = NeonButton(filled=True, text="START  -->")
        btn.height = dp(40)
        btn.bind(on_press=lambda x: on_tap())

        self.add_widget(top_row)
        self.add_widget(stats_row)
        self.add_widget(tags_row)
        self.add_widget(btn)

    def _draw(self, *a):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
        self.border_rect.rounded_rectangle = (self.x, self.y, self.width, self.height, dp(14))


class SetDot(Widget):
    def __init__(self, done=False, active=False, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (dp(8), dp(8))
        self.done = done
        self.active = active
        self.bind(pos=self._draw, size=self._draw)

    def _draw(self, *a):
        self.canvas.clear()
        with self.canvas:
            if self.done:
                Color(*GREEN)
                Ellipse(pos=self.pos, size=self.size)
            elif self.active:
                Color(*GREEN_DIM)
                Ellipse(pos=self.pos, size=self.size)
            else:
                Color(*GREY2)
                Ellipse(pos=self.pos, size=self.size)


class ExerciseRow(BoxLayout):
    def __init__(self, exercise, sets_total, sets_done, active=False, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = dp(48)
        self.padding = [dp(12), dp(6), dp(12), dp(6)]
        self.spacing = dp(8)

        bg = CARD2 if active else CARD
        with self.canvas.before:
            Color(*bg)
            self.bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(10)])
            if active:
                Color(*GREEN)
                self.border = Line(
                    rounded_rectangle=(self.x, self.y, self.width, self.height, dp(10)),
                    width=1.0
                )
            else:
                self.border = None
        self.bind(pos=self._draw, size=self._draw)

        # Active marker
        marker = Widget(size_hint_x=None, width=dp(3))
        with marker.canvas:
            Color(*(GREEN if active else GREY2))
            RoundedRectangle(pos=marker.pos, size=marker.size, radius=[dp(2)])
        marker.bind(
            pos=lambda *a: None,
            size=lambda *a: None
        )
        self.add_widget(marker)

        # Name
        name_lbl = Label(
            text=exercise,
            color=WHITE if active else GREY,
            bold=active,
            font_size=sp(13),
            halign="left",
            valign="middle",
            size_hint_x=1
        )
        name_lbl.bind(size=name_lbl.setter('text_size'))
        self.add_widget(name_lbl)

        # Set dots
        dots = BoxLayout(
            orientation="horizontal",
            spacing=dp(4),
            size_hint_x=None,
            width=dp(sets_total * 12),
            padding=[0, dp(4)]
        )
        for i in range(sets_total):
            done = i < sets_done
            act = (i == sets_done and active)
            dots.add_widget(SetDot(done=done, active=act))
        self.add_widget(dots)

    def _draw(self, *a):
        self.bg.pos = self.pos
        self.bg.size = self.size
        if self.border:
            self.border.rounded_rectangle = (self.x, self.y, self.width, self.height, dp(10))


class SectionHeader(BoxLayout):
    def __init__(self, text, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.height = dp(28)
        self.padding = [dp(4), 0]

        dot = Widget(size_hint_x=None, width=dp(6), size_hint_y=None, height=dp(6))
        with dot.canvas:
            Color(*GREEN)
            Ellipse(pos=dot.pos, size=dot.size)
        dot.bind(pos=lambda *a: None, size=lambda *a: None)

        lbl = Label(
            text=text.upper(),
            color=GREEN,
            bold=True,
            font_size=sp(10),
            halign="left",
            valign="middle"
        )
        lbl.bind(size=lbl.setter('text_size'))
        self.add_widget(dot)
        self.add_widget(lbl)


# --------------------------
# HOME SCREEN
# --------------------------
class HomeScreen(Screen):
    def __init__(self, app_ref, **kwargs):
        super().__init__(**kwargs)
        self.app_ref = app_ref
        self._build()

    def _build(self):
        root = BoxLayout(orientation="vertical")
        make_bg(root, BG)

        # Header
        header = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(90),
            padding=[dp(20), dp(28), dp(20), dp(8)]
        )
        make_bg(header, BG)

        title_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(36))
        title = Label(
            text="Iron Coach",
            color=WHITE,
            bold=True,
            font_size=sp(26),
            halign="left",
            valign="middle"
        )
        title.bind(size=title.setter('text_size'))

        # Neon dot accent
        dot_box = BoxLayout(size_hint_x=None, width=dp(10), padding=[0, dp(12)])
        dot = Widget(size_hint_y=None, height=dp(10))
        with dot.canvas:
            Color(*GREEN)
            Ellipse(pos=dot.pos, size=(dp(8), dp(8)))
        dot.bind(pos=lambda *a: None, size=lambda *a: None)
        dot_box.add_widget(dot)

        title_row.add_widget(title)
        title_row.add_widget(dot_box)

        sub = Label(
            text="SELECT WORKOUT",
            color=GREEN,
            bold=True,
            font_size=sp(10),
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(18)
        )
        sub.bind(size=sub.setter('text_size'))

        header.add_widget(title_row)
        header.add_widget(sub)
        root.add_widget(header)

        # Green divider line
        line = Widget(size_hint_y=None, height=dp(1))
        with line.canvas:
            Color(*GREEN)
            Rectangle(pos=line.pos, size=line.size)
        line.bind(
            pos=lambda *a: None,
            size=lambda *a: None
        )
        root.add_widget(line)

        # Scroll
        scroll = ScrollView(size_hint_y=1)
        self.cards_layout = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(12),
            padding=[dp(14), dp(14)]
        )
        self.cards_layout.bind(minimum_height=self.cards_layout.setter("height"))
        scroll.add_widget(self.cards_layout)
        root.add_widget(scroll)

        self.add_widget(root)
        self.refresh_cards()

    def refresh_cards(self):
        self.cards_layout.clear_widgets()
        df = self.app_ref.df
        for wid in self.app_ref.workout_ids:
            wd = filter_workout(df, wid)
            name = get_workout_name(df, wid)
            ex_count = count_exercises(wd)
            set_count = count_total_sets(wd)
            est_min = estimate_workout_minutes(wd)
            types = get_types(wd)
            card = WorkoutCard(
                wid=wid,
                name=name,
                ex_count=ex_count,
                set_count=set_count,
                est_min=est_min,
                types=types,
                on_tap=lambda w=wid: self.app_ref.start_workout(w),
                size_hint_y=None,
                height=dp(170)
            )
            self.cards_layout.add_widget(card)


# --------------------------
# WORKOUT SCREEN
# --------------------------
class WorkoutScreen(Screen):
    def __init__(self, app_ref, **kwargs):
        super().__init__(**kwargs)
        self.app_ref = app_ref
        self.thread = None
        self._workout_df = []
        self._set_done = {}
        self._build()

    def _build(self):
        root = BoxLayout(orientation="vertical")
        make_bg(root, BG)

        # Top bar
        topbar = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(56),
            padding=[dp(14), dp(10), dp(14), dp(4)],
            spacing=dp(10)
        )
        make_bg(topbar, BG)

        back_btn = SmallButton(
            text="<",
            bg=CARD,
            fg=GREEN,
            radius=8,
            size_hint_x=None,
            width=dp(44),
            height=dp(44),
            font_size=sp(18)
        )
        back_btn.bind(on_press=self._go_home)

        self.workout_title = Label(
            text="WORKOUT",
            color=WHITE,
            bold=True,
            font_size=sp(15),
            halign="center",
            valign="middle"
        )
        self.workout_title.bind(size=self.workout_title.setter('text_size'))

        topbar.add_widget(back_btn)
        topbar.add_widget(self.workout_title)
        topbar.add_widget(Widget(size_hint_x=None, width=dp(44)))
        root.add_widget(topbar)

        # Timer block
        timer_block = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(140),
            padding=[dp(14), dp(4), dp(14), dp(4)]
        )
        make_rounded_bg(timer_block, CARD, radius=14)

        self.phase_label = Label(
            text="GET READY",
            color=GREEN,
            bold=True,
            font_size=sp(11),
            halign="center",
            valign="middle",
            size_hint_y=None,
            height=dp(22)
        )
        self.phase_label.bind(size=self.phase_label.setter('text_size'))

        self.timer_label = Label(
            text="--",
            color=WHITE,
            bold=True,
            font_size=sp(72),
            halign="center",
            valign="middle",
            size_hint_y=None,
            height=dp(90)
        )
        self.timer_label.bind(size=self.timer_label.setter('text_size'))

        info_row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(22),
            padding=[dp(4), 0]
        )
        self.set_counter = Label(
            text="",
            color=GREEN,
            bold=True,
            font_size=sp(12),
            halign="left",
            valign="middle",
            size_hint_x=0.5
        )
        self.set_counter.bind(size=self.set_counter.setter('text_size'))
        self.upcoming_label = Label(
            text="",
            color=GREY,
            font_size=sp(11),
            halign="right",
            valign="middle",
            size_hint_x=0.5
        )
        self.upcoming_label.bind(size=self.upcoming_label.setter('text_size'))
        info_row.add_widget(self.set_counter)
        info_row.add_widget(self.upcoming_label)

        timer_block.add_widget(self.phase_label)
        timer_block.add_widget(self.timer_label)
        timer_block.add_widget(info_row)

        timer_wrapper = BoxLayout(
            size_hint_y=None, height=dp(148),
            padding=[dp(14), dp(4)]
        )
        timer_wrapper.add_widget(timer_block)
        root.add_widget(timer_wrapper)

        # Progress bar
        pb_wrapper = BoxLayout(
            size_hint_y=None, height=dp(10),
            padding=[dp(14), 0]
        )
        self.progress = ProgressBar(max=100, value=0)
        pb_wrapper.add_widget(self.progress)
        root.add_widget(pb_wrapper)

        # Timeline
        scroll = ScrollView(size_hint_y=1, do_scroll_x=False)
        self.timeline = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(5),
            padding=[dp(12), dp(8)]
        )
        self.timeline.bind(minimum_height=self.timeline.setter("height"))
        scroll.add_widget(self.timeline)
        root.add_widget(scroll)

        # Control buttons — 4 in a row
        ctrl_wrapper = BoxLayout(
            size_hint_y=None, height=dp(72),
            padding=[dp(12), dp(8)],
            spacing=dp(8)
        )
        make_bg(ctrl_wrapper, BG)

        self.pause_btn = SmallButton(text="||", bg=CARD2, fg=WHITE, radius=10)
        self.pause_btn.bind(on_press=self._pause)

        self.resume_btn = SmallButton(text=">", bg=GREEN_BG, fg=GREEN, radius=10)
        self.resume_btn.bind(on_press=self._resume)

        self.skip_btn = SmallButton(text=">|", bg=CARD2, fg=GREEN, radius=10)
        self.skip_btn.bind(on_press=self._skip)

        self.stop_btn = SmallButton(text="[]", bg=CARD2, fg=RED, radius=10)
        self.stop_btn.bind(on_press=self._stop)

        ctrl_wrapper.add_widget(self.pause_btn)
        ctrl_wrapper.add_widget(self.resume_btn)
        ctrl_wrapper.add_widget(self.skip_btn)
        ctrl_wrapper.add_widget(self.stop_btn)
        root.add_widget(ctrl_wrapper)

        # Button labels
        label_row = BoxLayout(
            size_hint_y=None, height=dp(16),
            padding=[dp(12), 0],
            spacing=dp(8)
        )
        for txt in ["PAUSE", "RESUME", "SKIP", "STOP"]:
            lbl = Label(
                text=txt,
                color=GREY,
                font_size=sp(9),
                halign="center",
                valign="middle"
            )
            lbl.bind(size=lbl.setter('text_size'))
            label_row.add_widget(lbl)
        root.add_widget(label_row)

        self.add_widget(root)

    def start(self, workout_id, workout_name, df):
        self.workout_title.text = workout_name.upper()
        self._workout_df = filter_workout(df, workout_id)
        self._set_done = {}
        self.phase_label.text = "GET READY"
        self.timer_label.text = "--"
        self.timer_label.color = WHITE
        self.set_counter.text = ""
        self.upcoming_label.text = ""
        self.progress.value = 0
        self.render_timeline()

        if self.thread and self.thread.is_alive():
            self.thread.running = False
            self.thread.skip_now()

        self.thread = WorkoutRunner(
            rows=self._workout_df,
            tts=self.app_ref.tts,
            bell=self.app_ref.bell,
            on_update=self._on_update,
            on_highlight=self._on_highlight,
            on_set_done=self._on_set_done,
            on_finish=self._on_finish,
            on_speak=self._on_speak,
        )
        self.thread.start()

    def render_timeline(self, current_ex=None):
        self.timeline.clear_widgets()
        for t in get_types(self._workout_df):
            self.timeline.add_widget(SectionHeader(text=t))
            td = filter_type(self._workout_df, t)
            sets_total = get_sets(td)
            for ex in get_exercises(td):
                done = self._set_done.get(ex, 0)
                active = (ex == current_ex)
                self.timeline.add_widget(
                    ExerciseRow(ex, sets_total, done, active=active)
                )

    # ---- Instant controls ----
    def _pause(self, *a):
        if self.thread:
            self.thread.paused = True
            self.phase_label.text = "PAUSED"

    def _resume(self, *a):
        if self.thread:
            self.thread.paused = False

    def _skip(self, *a):
        if self.thread:
            self.thread.skip_now()

    def _stop(self, *a):
        if self.thread:
            self.thread.running = False
            self.thread.paused = False
            self.thread.skip_now()
        if self.app_ref.tts:
            self.app_ref.tts.stop()
        Clock.schedule_once(lambda dt: self._go_home(), 0.15)

    def _go_home(self, *a):
        if self.thread:
            self.thread.running = False
            self.thread.paused = False
            self.thread.skip_now()
        self.app_ref.sm.current = "home"

    # ---- Callbacks ----
    def _on_update(self, phase, upcoming, sec, total):
        def u(dt):
            self.phase_label.text = phase.upper()
            self.upcoming_label.text = f"Next: {upcoming}" if upcoming else ""
            self.timer_label.text = str(sec)
            self.timer_label.color = RED if sec <= 3 else WHITE
            self.progress.value = int((1 - sec / total) * 100)
        Clock.schedule_once(u, 0)

    def _on_highlight(self, exercise, cur_set, total_sets):
        def u(dt):
            self.phase_label.text = exercise.upper()
            self.set_counter.text = f"SET {cur_set} / {total_sets}"
            self.render_timeline(exercise)
        Clock.schedule_once(u, 0)

    def _on_set_done(self, exercise):
        self._set_done[exercise] = self._set_done.get(exercise, 0) + 1

    def _on_finish(self):
        def u(dt):
            self.phase_label.text = "COMPLETE"
            self.timer_label.text = "OK"
            self.timer_label.color = GREEN
            self.set_counter.text = "DONE"
            self.upcoming_label.text = ""
        Clock.schedule_once(u, 0)

    def _on_speak(self, text):
        if self.app_ref.tts:
            Clock.schedule_once(lambda dt: self.app_ref.tts.speak(text), 0)


# --------------------------
# WORKOUT RUNNER
# --------------------------
class WorkoutRunner(threading.Thread):
    def __init__(self, rows, tts, bell, on_update, on_highlight, on_set_done, on_finish, on_speak):
        super().__init__(daemon=True)
        self.rows = rows
        self.tts = tts
        self.bell = bell
        self.on_update = on_update
        self.on_highlight = on_highlight
        self.on_set_done = on_set_done
        self.on_finish = on_finish
        self.on_speak = on_speak
        self.running = True
        self.paused = False
        self._skip = False

    def skip_now(self):
        self._skip = True

    def _wait(self, seconds):
        end = time.time() + seconds
        while time.time() < end:
            if not self.running or self._skip:
                return
            while self.paused:
                time.sleep(0.05)
                if not self.running:
                    return
            time.sleep(0.05)

    def run(self):
        self.say("Get ready to train")
        self.phase("GET READY", START_DELAY)
        types = get_types(self.rows)

        for t in types:
            if not self.running: return
            td = filter_type(self.rows, t)
            sets_total = get_sets(td)
            self.say(f"Starting {t}")

            for s in range(1, sets_total + 1):
                if not self.running: return
                for ex_idx, ex_row in enumerate(td):
                    if not self.running: return
                    exercise = get_val(ex_row, "exercise")
                    reps = get_val(ex_row, "reps")
                    t_val = get_val(ex_row, "time")
                    duration = get_duration(ex_row)
                    reps_str = (
                        f"{int(float(reps))} reps" if reps
                        else f"{int(float(t_val))} seconds"
                    )
                    self.say(f"Set {s}. {exercise}. {reps_str}")
                    self.on_highlight(exercise, s, sets_total)
                    next_ex = get_next_exercise(td, ex_idx)
                    self.phase(exercise, duration, next_ex, cur_set=s, total_sets=sets_total)
                    self.on_set_done(exercise)
                    self.say("Rest")
                    self.phase("REST", REST_EXERCISE)

                if s < sets_total:
                    self.say("Rest between sets")
                    self.phase("REST BETWEEN SETS", REST_SET)

            if t != types[-1]:
                self.say("Section complete. Rest.")
                self.phase("REST", REST_TYPE)

        self.say("Workout complete. Excellent work!")
        self.on_finish()

    def say(self, text):
        self.on_speak(text)
        self._wait(max(1.0, len(text) * 0.055))

    def phase(self, label, seconds, upcoming="", cur_set=0, total_sets=0):
        self._skip = False
        for sec in range(seconds, 0, -1):
            if not self.running or self._skip:
                return
            while self.paused:
                time.sleep(0.05)
                if not self.running: return
            self.on_update(label, upcoming, sec, seconds)
            if sec <= 3:
                self.on_speak(str(sec))
            time.sleep(1)
        if self.bell:
            try:
                Clock.schedule_once(lambda dt: self.bell.play(), 0)
            except Exception:
                pass


# --------------------------
# APP
# --------------------------
class IronCoachApp(App):
    def build(self):
        Window.clearcolor = BG
        try:
            return self._build_app()
        except Exception as e:
            import traceback
            err = traceback.format_exc()
            print(f"[FATAL] {err}")
            root = BoxLayout(orientation="vertical", padding=dp(20), spacing=dp(10))
            make_bg(root, BG)
            root.add_widget(Label(
                text="STARTUP ERROR",
                color=GREEN,
                bold=True,
                font_size=sp(18),
                size_hint_y=None,
                height=dp(40)
            ))
            root.add_widget(Label(
                text=str(e),
                color=WHITE,
                font_size=sp(11),
                text_size=(Window.width - dp(40), None),
                halign="left",
                size_hint_y=None,
                height=dp(120)
            ))
            root.add_widget(Label(
                text=err[-600:],
                color=GREY,
                font_size=sp(9),
                text_size=(Window.width - dp(40), None),
                halign="left"
            ))
            return root

    def _build_app(self):
        try:
            self.df = load_workouts()
            self.workout_ids = get_workout_ids(self.df)
        except Exception as e:
            print(f"[Data] {e}")
            self.df = list(csv.DictReader(io.StringIO(SAMPLE_CSV)))
            self.workout_ids = get_workout_ids(self.df)

        try:
            self.tts = TTSEngine()
        except Exception:
            self.tts = None

        self.bell = None
        try:
            from kivy.core.audio import SoundLoader
            p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bell.mp3")
            self.bell = SoundLoader.load(p)
        except Exception:
            pass

        self.sm = ScreenManager(transition=NoTransition())
        self.home_screen = HomeScreen(name="home", app_ref=self)
        self.workout_screen = WorkoutScreen(name="workout", app_ref=self)
        self.sm.add_widget(self.home_screen)
        self.sm.add_widget(self.workout_screen)
        self.sm.current = "home"
        return self.sm

    def start_workout(self, workout_id):
        name = get_workout_name(self.df, workout_id)
        self.sm.current = "workout"
        self.workout_screen.start(workout_id, name, self.df)

    def get_application_name(self):
        return "Iron Coach"


if __name__ == "__main__":
    IronCoachApp().run()
