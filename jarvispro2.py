import os
import sys
import sqlite3
import datetime
import webbrowser
import requests
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.utils import platform

# Conditional imports based on platform to prevent mobile crashes
if platform == 'win':
    import pyautogui
    import psutil
    import pyttsx3
    import speech_recognition as sr
    import cv2
    import subprocess
else:
    # Android/iOS placeholders or alternatives can be imported here
    pass

# ==========================================
# CONSTANTS & CONFIGURATION
# ==========================================
WAKE_WORD = "jarvis"
USER_NAME = "shourya"
MODEL_NAME = "phi3"
DB_NAME = "jarvis_memory.db"

# ==========================================
# DATABASE / MEMORY MANAGEMENT
# ==========================================
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS memory (key TEXT PRIMARY KEY, value TEXT)")
    conn.commit()
    conn.close()

def remember(key, value):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO memory VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

def recall(key):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM memory WHERE key=?", (key,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

init_db()

# ==========================================
# CORE CAPABILITIES & AUTOMATION MODULES
# ==========================================
def ask_ai(prompt):
    try:
        # Note: 'localhost' works if Ollama runs on the same device.
        # For mobile, replace 'localhost' with your PC's local IP address (e.g., 192.168.1.X)
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": MODEL_NAME, "prompt": prompt, "stream": False},
            timeout=5
        )
        return response.json().get("response", "No response from model.")
    except Exception:
        return "Could not connect to Ollama brain matrix."

def get_battery_level():
    if platform == 'win':
        battery = psutil.sensors_battery()
        if battery is None:
            return f"Unable to detect a battery source, {USER_NAME}."
        status = "plugged in" if battery.power_plugged else "running on main cell arrays"
        return f"Main power cells are at {battery.percent} percent, {USER_NAME}. System is {status}."
    else:
        return f"Battery monitoring module optimized for desktop environments, {USER_NAME}."

def search_desktop_file(file_name):
    if platform == 'win':
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        search_query = file_name.replace("search file", "").replace("find file", "").strip().lower()
        if not search_query:
            return "Please specify the file name, sir."
            
        matched_files = []
        for item in os.listdir(desktop_path):
            if os.path.isfile(os.path.join(desktop_path, item)) and search_query in item.lower():
                matched_files.append(item)
                    
        if matched_files:
            return f"Found matching items on your Desktop: {', '.join(matched_files)}."
        return f"No files matching '{search_query}' detected on Desktop."
    else:
        return "Desktop file search is strictly available on Desktop platforms."

def take_screenshot():
    if platform == 'win':
        image = pyautogui.screenshot()
        filename = "jarvis_screen.png"
        image.save(filename)
        return f"Frame captured and saved as {filename}."
    return "Screenshot hardware hooks are unavailable on this operating system."

def capture_camera_photo():
    if platform == 'win':
        cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not cam.isOpened():
            return "Failed to establish a connection with camera hardware."
        ret, frame = cam.read()
        if ret:
            filename = "jarvis_capture.jpg"
            cv2.imwrite(filename, frame)
            cam.release()
            return f"Optical footprint captured successfully as {filename}."
        cam.release()
        return "Failed to acquire frame sequence."
    return "Native camera automation requires mobile permission wrappers."

def launch_app(app_name):
    if platform == 'win':
        apps = {
            "notepad": "C:\\Windows\\System32\\notepad.exe",
            "calculator": "calc.exe",
            "paint": "C:\\Windows\\System32\\mspaint.exe"
        }
        if app_name in apps:
            subprocess.Popen(apps[app_name], shell=True)
            return f"Launching {app_name} now."
        return f"Application path for {app_name} not structured."
    return f"App execution protocols are platform locked."

# ==========================================
# KIVY GRAPHICAL INTERFACE
# ==========================================
class JarvisInterface(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=20, spacing=10, **kwargs)
        
        # System status label
        self.status_label = Label(
            text="[SYSTEM LOCKED]\nMainframe standing by...", 
            font_size='20sp', 
            halign='center',
            size_hint_y=0.2
        )
        self.add_widget(self.status_label)
        
        # Scrollable terminal output console
        self.scroll_view = ScrollView(size_hint_y=0.6)
        self.console_output = Label(
            text="Welcome to Jarvis Matrix.\n", 
            font_size='14sp', 
            halign='left', 
            valign='top',
            size_hint_y=None
        )
        self.console_output.bind(texture_size=self.console_output.setter('size'))
        self.scroll_view.add_widget(self.console_output)
        self.add_widget(self.scroll_view)
        
        # Action button
        self.action_btn = Button(
            text="TAP TO SPEAK", 
            size_hint_y=0.2, 
            background_color=(0, 0.7, 0.9, 1)
        )
        self.action_btn.bind(on_release=self.trigger_listening)
        self.add_widget(self.action_btn)
        
        self.is_unlocked = False
        self.engine = None
        
        # Initialize text-to-speech engine if on Windows
        if platform == 'win':
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', 180)

    def log_text(self, text):
        self.console_output.text += f"\n{text}"
        
    def speak(self, text):
        self.log_text(f"Jarvis: {text}")
        if platform == 'win' and self.engine:
            self.engine.say(text)
            self.engine.runAndWait()

    def trigger_listening(self, instance):
        if platform == 'win':
            self.status_label.text = "Listening..."
            # Execute voice capture on the next clock frame to keep UI responsive
            Clock.schedule_once(self.process_voice_input, 0.1)
        else:
            self.log_text("System: Voice framework falls back to touch interactions on mobile interfaces.")
            self.process_command("what is time") # Example simulation fallback

    def process_voice_input(self, dt):
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            recognizer.pause_threshold = 0.8
            recognizer.adjust_for_ambient_noise(source, duration=0.4)
            try:
                audio = recognizer.listen(source, timeout=4, phrase_time_limit=6)
                query = recognizer.recognize_google(audio, language='en-US').lower().strip()
                self.log_text(f"User: {query}")
                self.process_command(query)
            except Exception:
                self.status_label.text = "Standing by..."

    def process_command(self, command):
        if not self.is_unlocked:
            if WAKE_WORD in command:
                self.is_unlocked = True
                self.status_label.text = "[MAIN INTEGRITY UNLOCKED]"
                self.speak(f"Good day {USER_NAME}. Mainframe completely unlocked. Directives?")
            else:
                self.status_label.text = "[SYSTEM LOCKED]\nSay 'Jarvis' to unlock."
            return

        # Core operational handlers
        if "exit" in command or "go offline" in command:
            self.speak("Locking mainframe modules.")
            self.is_unlocked = False
            self.status_label.text = "[SYSTEM LOCKED]"
            
        elif "time" in command:
            current_time = datetime.datetime.now().strftime("%I:%M %p")
            self.speak(f"The current time is {current_time}, {USER_NAME}.")
            
        elif "battery" in command:
            self.speak(get_battery_level())
            
        elif "search file" in command or "find file" in command:
            self.speak(search_desktop_file(command))
            
        elif "screenshot" in command:
            self.speak(take_screenshot())
            
        elif "take a photo" in command or "open camera" in command:
            self.speak(capture_camera_photo())
            
        elif command.startswith("open app "):
            target = command.replace("open app ", "").strip()
            self.speak(launch_app(target))
            
        elif command.startswith("open "):
            website = command.replace("open ", "").strip()
            url = f"https://www.{website}.com"
            self.speak(f"Opening {website}.")
            webbrowser.open(url)
            
        elif command.startswith("remember"):
            text = command.replace("remember", "").strip()
            if " is " in text:
                key, value = text.split(" is ", 1)
                remember(key.strip(), value.strip())
                self.speak(f"Stored. {key.strip()} is now set to {value.strip()}.")
                
        elif command.startswith("what is"):
            key = command.replace("what is", "").strip()
            value = recall(key)
            if value:
                self.speak(f"{key} is {value}")
            else:
                self.speak(ask_ai(command))
        else:
            self.speak(ask_ai(command))

class JarvisApp(App):
    def build(self):
        self.title = "Jarvis Core System"
        return JarvisInterface()

if __name__ == '__main__':
    JarvisApp().run()
