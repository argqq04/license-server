import customtkinter as ctk
import pyautogui
import pydirectinput
import time
import numpy as np
import threading
from pynput import keyboard
import cv2
import mss
import uuid
import platform
import hashlib
import requests
import json
import os
import tkinter.simpledialog as sd

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")
pyautogui.FAILSAFE = True
pydirectinput.PAUSE = 0.05

SERVER_URL = "https://web-production-f9ee0.up.railway.app"
KEY_FILE = os.path.join(os.getenv("APPDATA"), "zahar_license.json")

def get_hwid():
    raw = platform.node() + str(uuid.getnode())
    return hashlib.sha256(raw.encode()).hexdigest()

def check_license():
    hwid = get_hwid()

    if os.path.exists(KEY_FILE):
        with open(KEY_FILE) as f:
            code = json.load(f).get("code")
    else:
        root = ctk.CTk()
        root.withdraw()
        code = sd.askstring("Activare Licență", "Introdu codul de activare:", parent=root)
        root.destroy()
        if not code:
            return False

    try:
        r = requests.post(
            f"{SERVER_URL}/validate",
            json={"code": code.strip().upper(), "hwid": hwid},
            timeout=5
        )
        data = r.json()
    except Exception:
        return False

    if data.get("ok"):
        with open(KEY_FILE, "w") as f:
            json.dump({"code": code.strip().upper()}, f)
        return True

    if os.path.exists(KEY_FILE):
        os.remove(KEY_FILE)

    return False


class MethBotApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("argq bosu zahar pulosu")
        self.geometry("500x850")
        self.resizable(False, False)

        try:
            self.iconbitmap("zahar.ico")
        except Exception:
            pass

        if not check_license():
            import tkinter.messagebox as mb
            mb.showerror("Acces Refuzat", "Licență invalidă sau expirată.")
            self.destroy()
            return

        self.running = False

        self.keyboard_listener = keyboard.Listener(on_press=self.on_key_press)
        self.keyboard_listener.start()

        self.setup_ui()
        self.log("Sistem initializat. Acces Verificat.")

    def setup_ui(self):
        self.header_frame = ctk.CTkFrame(self, fg_color="#1a1a1a", corner_radius=0, height=80)
        self.header_frame.pack(fill="x", side="top")

        ctk.CTkLabel(self.header_frame, text="Sistem a la bos de farmat",
                     font=("Roboto Medium", 24, "bold"), text_color="#ffffff").pack(pady=(20, 5))

        self.status_label = ctk.CTkLabel(self.header_frame, text="STATUS: IN AȘTEPTARE",
                                         font=("Roboto", 12, "bold"), text_color="#aaaaaa")
        self.status_label.pack(pady=(0, 15))

        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(pady=20, padx=20, fill="both")

        self.btn_preparare = self._create_module_frame("PREPARARE", "▶ PORNEȘTE MODUL PREPARARE (CIFRA 1)",
                                                        self.start_preparare, "#2cc985", "#1e8f5e")

        self.btn_frigidere = self._create_module_frame("FRIGIDER", "▶ PORNEȘTE MODUL FRIGIDER (CIFRA 2)",
                                                        self.start_frigidere, "#d68a24", "#a86916")

        self.btn_infoliere = self._create_module_frame("INFOLIAT", "▶ PORNEȘTE MODUL INFOLIERE (CIFRA 3)",
                                                        self.start_infoliere, "#1f6aa5", "#144870")

        self.btn_fosfor = self._create_module_frame("FOSFOR", "▶ PORNEȘTE PROCESARE FOSFOR (CIFRA 4)",
                                                        self.start_fosfor, "#8e44ad", "#732d91")

        self.btn_stop = ctk.CTkButton(
            self, text="😎 STOP (CIFRA 0)", command=self.stop_script,
            fg_color="#3a3a3a", text_color_disabled="#666666", hover_color="#9e2222",
            height=55, font=("Roboto", 16, "bold"), state="disabled",
            border_width=2, border_color="#2b2b2b", corner_radius=10
        )
        self.btn_stop.pack(pady=15, padx=20, fill="x")

        self.log_frame = ctk.CTkFrame(self, fg_color="#121212", corner_radius=10)
        self.log_frame.pack(pady=(0, 20), padx=20, fill="both", expand=True)

        ctk.CTkLabel(self.log_frame, text="Terminal Output:", font=("Consolas", 10, "bold"),
                     text_color="#555555").pack(anchor="w", padx=10, pady=(5, 0))

        self.log_box = ctk.CTkTextbox(self.log_frame, font=("Consolas", 12), text_color="#023F02", fg_color="transparent")
        self.log_box.pack(padx=5, pady=5, fill="both", expand=True)
        self.log_box.configure(state="disabled")

    def _create_module_frame(self, label_text, btn_text, command, color, hover_color):
        frame = ctk.CTkFrame(self.main_container, fg_color="#2b2b2b", corner_radius=10)
        frame.pack(fill="x", pady=5)
        ctk.CTkLabel(frame, text=label_text, font=("Arial", 11, "bold"), text_color="#7f8c8d").pack(pady=(10, 0))
        btn = ctk.CTkButton(frame, text=btn_text, command=command, fg_color=color, hover_color=hover_color,
                            height=40, font=("Roboto", 13, "bold"), corner_radius=8)
        btn.pack(pady=10, padx=15, fill="x")
        return btn

    def log(self, message):
        self.after(0, self._update_log_ui, message)

    def _update_log_ui(self, message):
        self.log_box.configure(state="normal")
        timestamp = time.strftime('[%H:%M:%S]')
        self.log_box.insert("end", f"{timestamp} > {message}\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def toggle_buttons(self, state):
        self.after(0, lambda: self._update_buttons_ui(state))

    def _update_buttons_ui(self, state):
        if state == "running":
            self.btn_infoliere.configure(state="disabled", fg_color="#3a3a3a")
            self.btn_preparare.configure(state="disabled", fg_color="#3a3a3a")
            self.btn_frigidere.configure(state="disabled", fg_color="#3a3a3a")
            self.btn_fosfor.configure(state="disabled", fg_color="#3a3a3a")
            self.btn_stop.configure(state="normal", fg_color="#c92c2c", border_color="#ff4d4d")
        else:
            self.btn_infoliere.configure(state="normal", fg_color="#1f6aa5")
            self.btn_preparare.configure(state="normal", fg_color="#2cc985")
            self.btn_frigidere.configure(state="normal", fg_color="#d68a24")
            self.btn_fosfor.configure(state="normal", fg_color="#8e44ad")
            self.btn_stop.configure(state="disabled", fg_color="#3a3a3a", border_color="#2b2b2b")
            self.status_label.configure(text="STATUS: IN AȘTEPTARE", text_color="#aaaaaa")

    def on_key_press(self, key):
        try:
            if key.char.lower() == '0' and self.running:
                self.log("Ai apasat pe cifra 0! Oprire...")
                self.stop_script()
            elif key.char.lower() == '1' and not self.running:
                self.log("Ai apasat cifra 1! Pornesc modul de preparare.")
                self.start_preparare()
            elif key.char.lower() == '2' and not self.running:
                self.log("Ai apasat cifra 2! Pornesc modul de frigidere.")
                self.start_frigidere()
            elif key.char.lower() == '3' and not self.running:
                self.log("Ai apasat cifra 3! Pornesc modul de infoliere.")
                self.start_infoliere()
            elif key.char.lower() == '4' and not self.running:
                self.log("Ai apasat cifra 4! Pornesc modul pentru fosfor.")
                self.start_fosfor()
        except AttributeError:
            pass

    def stop_script(self):
        self.running = False
        self.after(0, lambda: self.status_label.configure(text="STATUS: SE OPREȘTE...", text_color="#e67e22"))

    def check_active(self):
        if not self.running:
            raise Exception("StopVoluntar")

    def click_sigur(self):
        pydirectinput.mouseDown()
        time.sleep(0.1)
        pydirectinput.mouseUp()

    def click_sigur_pyautogui(self):
        pyautogui.mouseDown(button='left')
        time.sleep(0.1)
        pyautogui.mouseUp(button='left')

    def human_click(self, x, y):
        pyautogui.moveTo(x, y, duration=0.1)
        pyautogui.mouseDown()
        time.sleep(0.1)
        pyautogui.mouseUp()

    def human_drag_drop(self, start_x, start_y, end_x, end_y):
        pyautogui.moveTo(start_x, start_y, duration=0.1)
        time.sleep(0.1)
        pyautogui.mouseDown()
        time.sleep(0.1)
        pyautogui.moveTo(end_x, end_y, duration=0.1)
        time.sleep(0.1)
        pyautogui.mouseUp()

    def reset_camera(self):
        coord_start_alt = (939, 541)
        coord_start_click2 = (844, 505)

        self.check_active()
        pyautogui.moveTo(*coord_start_alt, duration=0.1)
        pydirectinput.keyDown('alt')
        time.sleep(0.3)

        self.click_sigur_pyautogui()
        time.sleep(0.1)

        pyautogui.moveTo(*coord_start_click2, duration=0.1)
        self.click_sigur_pyautogui()
        time.sleep(0.1)

        pydirectinput.keyUp('alt')
        time.sleep(0.5)

    def _start_thread(self, target_func, status_text, status_color):
        if not self.running:
            self.running = True
            self.toggle_buttons("running")
            self.status_label.configure(text=status_text, text_color=status_color)
            threading.Thread(target=target_func, daemon=True).start()

    def start_fosfor(self):
        self._start_thread(self.run_logic_fosfor, "STATUS: FOSFOR ACTIV...", "#8e44ad")

    def run_logic_fosfor(self):
        prima_coordonata = (194, 571)
        doua_coordonata = (1845, 813)
        trei_coordonata = (1652, 988)

        self.log("--- MOD FOSFOR ---")
        self.log("Ai 3 secunde să dai click pe fereastra jocului...")
        time.sleep(3)

        try:
            while self.running:
                self.check_active()
                pydirectinput.keyDown('e')
                time.sleep(0.1)
                pydirectinput.keyUp('e')
                time.sleep(0.2)

                self.check_active()
                pydirectinput.click(prima_coordonata[0], prima_coordonata[1])
                time.sleep(0.5)

                self.check_active()

                for _ in range(4):
                    self.check_active()
                    pydirectinput.click(doua_coordonata[0], doua_coordonata[1])
                    time.sleep(0.1)

                self.check_active()
                pydirectinput.click(trei_coordonata[0], trei_coordonata[1])

                for _ in range(164):
                    self.check_active()
                    time.sleep(0.1)

        except Exception as e:
            self.log("Sistemul s-a oprit." if str(e) == "StopVoluntar" else f"Eroare: {e}")
        finally:
            self.running = False
            self.toggle_buttons("stopped")

    def start_infoliere(self):
        self._start_thread(self.run_logic_infoliere, "STATUS: ÎMPACHETARE ACTIV...", "#1f6aa5")

    def run_logic_infoliere(self):
        plicuri = [(958, 232), (955, 235), (1227, 230), (1224, 226), (1240, 223),
                   (1223, 222), (655, 227), (854, 217), (854, 216)]
        muguri = [(336, 392), (210, 392), (87, 385), (399, 292), (273, 306),
                  (139, 306), (413, 248), (311, 235), (202, 233)]

        coord_start_alt = (1322, 251)
        coord_start_click2 = (844, 505)
        mijloc_x, mijloc_y = (958, 304)

        self.log("--- MOD INFOLIERE ---")
        self.log("Începe în 3 secunde...")
        time.sleep(3)
        self.log("Am inceput infolierea!")

        try:
            while self.running:
                self.check_active()

                pydirectinput.press('alt')
                time.sleep(0.5)

                pyautogui.moveTo(coord_start_alt, duration=0.1)
                pydirectinput.keyDown('alt')
                time.sleep(0.5)
                self.click_sigur()
                time.sleep(0.5)

                pyautogui.moveTo(coord_start_click2, duration=0.1)
                self.click_sigur()
                time.sleep(0.1)
                pydirectinput.keyUp('alt')
                time.sleep(0.5)

                for plic, mugur in zip(plicuri, muguri):
                    self.check_active()
                    self.human_click(*plic)
                    time.sleep(0.11)
                    self.human_drag_drop(mugur[0], mugur[1], mijloc_x, mijloc_y)
                    time.sleep(0.6)

        except Exception as e:
            self.log("Sistemul s-a oprit." if str(e) == "StopVoluntar" else f"Eroare: {e}")
        finally:
            pydirectinput.keyUp('alt')
            self.running = False
            self.toggle_buttons("stopped")

    def rezolva_minigame(self):
        self.log("--- MINIGAME START ---")

        FIRE_X, FIRE_Y = 956, 1007
        SCAN_X_START, SCAN_Y_START = 630, 925
        SCAN_WIDTH, SCAN_HEIGHT = 660, 20

        monitor = {'top': SCAN_Y_START, 'left': SCAN_X_START, 'width': SCAN_WIDTH, 'height': SCAN_HEIGHT}

        LOWER_GREEN = np.array([35, 70, 70])
        UPPER_GREEN = np.array([90, 255, 255])
        WHITE_THRESHOLD = 230

        pyautogui.moveTo(FIRE_X, FIRE_Y)
        time.sleep(0.1)

        is_holding = False
        frames_missing_bar = 0

        try:
            with mss.mss() as sct:
                start_time = time.time()
                while self.running and (time.time() - start_time < 30):
                    img = np.array(sct.grab(monitor))
                    frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

                    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                    green_mask = cv2.inRange(hsv, LOWER_GREEN, UPPER_GREEN)
                    green_points = cv2.findNonZero(green_mask)

                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    _, white_mask = cv2.threshold(gray, WHITE_THRESHOLD, 255, cv2.THRESH_BINARY)
                    white_points = cv2.findNonZero(white_mask)

                    if white_points is not None and green_points is not None:
                        frames_missing_bar = 0

                        current_white_x = np.mean(white_points[:, :, 0])
                        target_green_x = np.mean(green_points[:, :, 0])

                        if current_white_x < target_green_x:
                            if not is_holding:
                                pydirectinput.mouseDown(button='right')
                                is_holding = True
                        else:
                            if is_holding:
                                pydirectinput.mouseUp(button='right')
                                is_holding = False
                    else:
                        frames_missing_bar += 1
                        if frames_missing_bar > 30:
                            break

                    time.sleep(0.01)

        except Exception as e:
            self.log(f"Eroare Minigame: {e}")
        finally:
            pydirectinput.mouseUp(button='right')
            self.log("--- MINIGAME FINALIZAT ---")

    def anti_afk_movement(self):
        self.log("Se executa miscarea Anti-AFK")

        try:
            pydirectinput.keyDown('d')
            time.sleep(0.3)
            pydirectinput.keyUp('d')
            time.sleep(0.1)

            pydirectinput.keyDown('a')
            time.sleep(0.3)
            pydirectinput.keyUp('a')

            time.sleep(1)
            self.log("AFK Resetat cu succes.")
        except Exception as e:
            self.log(f"Eroare la miscarea Anti-AFK: {e}")

    def start_preparare(self):
        self._start_thread(self.run_logic_preparare, "STATUS: PREPARARE ACTIV...", "#2cc985")

    def run_logic_preparare(self):
        ingrediente = [(616, 308, 6.1), (705, 335, 1.5), (624, 402, 6.1), (708, 405, 6.1)]
        locatie_ceaun = (957, 439)
        buton_activare = (956, 281)
        destinatie_ceaun_jos = (1092, 388)
        buton_start_minigame = (955, 172)

        durata_drag = 0.2
        pauza_pre_click = 0.1
        pauza_post_click = 1.4
        pauza_dupa_mutare = 6
        pauza_intre_cicluri = 0.7

        self.log("--- MOD PREPARARE ---")
        self.log("Începe în 3 secunde...")
        time.sleep(3)
        self.log("Am inceput prepararea!")

        contor_cicluri = 0
        total_cicluri_efectuate = 0

        try:
            while self.running:
                if total_cicluri_efectuate >= 100:
                    self.log("S-a atins limita maxima de 100 de cicluri. Oprire automata.")
                    break

                if contor_cicluri >= 25:
                    self.log("Limita 25 cicluri atinsa. Activez sistemul Anti-AFK.")
                    self.anti_afk_movement()
                    contor_cicluri = 0
                    time.sleep(1)

                self.check_active()
                time.sleep(0.2)
                self.reset_camera()
                time.sleep(0.2)

                for x, y, pauza_custom in ingrediente:
                    self.check_active()
                    pyautogui.moveTo(x, y, duration=0.1)
                    time.sleep(0.1)
                    pyautogui.dragTo(*locatie_ceaun, duration=durata_drag, button='left')
                    time.sleep(pauza_custom)

                self.check_active()
                time.sleep(pauza_pre_click)
                pyautogui.moveTo(*buton_activare, duration=0.1)
                self.click_sigur_pyautogui()

                self.check_active()
                time.sleep(pauza_post_click)
                pyautogui.moveTo(*locatie_ceaun, duration=0.1)
                pyautogui.dragTo(*destinatie_ceaun_jos, duration=durata_drag, button='left')

                self.check_active()
                time.sleep(pauza_dupa_mutare)
                pyautogui.moveTo(*destinatie_ceaun_jos, duration=0.1)
                self.click_sigur_pyautogui()

                pyautogui.moveTo(*buton_start_minigame, duration=0.1)
                time.sleep(pauza_intre_cicluri)
                self.click_sigur_pyautogui()

                time.sleep(0.5)
                self.check_active()
                self.rezolva_minigame()

                contor_cicluri += 1
                total_cicluri_efectuate += 1
                self.log(f"Ciclu {contor_cicluri}/25 complet. Resetare camera.")

        except Exception as e:
            self.log("Sistemul s-a oprit." if str(e) == "StopVoluntar" else f"Eroare: {e}")
        finally:
            pydirectinput.keyUp('alt')
            self.running = False
            self.toggle_buttons("stopped")

    def start_frigidere(self):
        self._start_thread(self.run_logic_frigidere, "STATUS: FRIGIDERE ACTIV...", "#d68a24")

    def run_logic_frigidere(self):
        lista_frigidere = [
            (1504, 357), (1638, 361), (1784, 358), (1499, 490),
            (1641, 503), (1785, 498), (1504, 636), (1644, 641),
            (1778, 639), (1504, 786), (1641, 783), (1779, 782)
        ]

        self.log("--- MOD FRIGIDERE ---")
        self.log("Începe în 3 secunde...")
        time.sleep(3)
        self.log("Am inceput sa le bag la frigider!")

        try:
            for i, (fx, fy) in enumerate(lista_frigidere):
                self.check_active()
                raft = i + 1
                self.log(f"Raftul {raft} din 12")

                pyautogui.moveTo(1320, 530, duration=0.1)
                pydirectinput.keyDown('alt')
                time.sleep(0.1)
                pydirectinput.mouseDown(); time.sleep(0.05); pydirectinput.mouseUp()
                time.sleep(0.1)

                pyautogui.moveTo(844, 505, duration=0.1)
                time.sleep(0.1)
                pydirectinput.mouseDown(); time.sleep(0.05); pydirectinput.mouseUp()
                time.sleep(0.1)
                pydirectinput.keyUp('alt')
                time.sleep(0.5)

                self.check_active()
                if not (fx == 0 and fy == 0):
                    self.log(f"Am apasat pe raftul: {raft} ")
                    pyautogui.moveTo(fx, fy, duration=0.1)
                    pydirectinput.mouseDown(); time.sleep(0.05); pydirectinput.mouseUp()

                time.sleep(0.5)
                self.check_active()

                pyautogui.moveTo(1365, 535, duration=0.1)
                time.sleep(0.1)
                pyautogui.mouseDown()
                time.sleep(0.1)
                pyautogui.moveTo(1177, 557, duration=0.1)
                time.sleep(0.1)
                pyautogui.mouseUp()
                time.sleep(5.3)

                self.check_active()
                pyautogui.moveTo(826, 477, duration=0.2)
                pydirectinput.mouseDown(); time.sleep(0.05); pydirectinput.mouseUp()
                time.sleep(0.7)

                self.check_active()
                pyautogui.moveTo(1092, 539, duration=0.2)
                pydirectinput.mouseDown()
                time.sleep(4)
                pydirectinput.mouseUp()

            self.log("Frigider finalizat.")

        except Exception as e:
            self.log("Sistemul s-a oprit." if str(e) == "StopVoluntar" else f"Eroare: {e}")
        finally:
            pydirectinput.keyUp('alt')
            self.running = False
            self.toggle_buttons("stopped")


if __name__ == "__main__":
    app = MethBotApp()
    app.mainloop()
