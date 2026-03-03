"""The Window for the GUI."""

import tkinter
import tkinter.messagebox
from datetime import datetime
import time

from utils import resource_path
#from utils import DataMedium, resource_path


BACKGROUND_COLOR = "gray"


class Window:
    """The GUI Window."""

    piece_num: int = 0
    num_completed_trials: int = 0
    is_in_trial: bool = False

    def __init__(self,expState):
        """Initialize the window."""
        self.create_window()
        self.expState = expState
        self.time_limit_job = None
        self.time_limit_triggered = False
        self.create_header_frame()
        self.create_input_frame()
        self.create_button_frame()
        self.create_progress_frame()
        self.create_status_frame()  # Add Bluetooth Status Frame

    def create_window(self):
        """Create and initialize the close frame."""
        self.window = tkinter.Tk()
        self.window.title("Trial Tracking")
        self.window.geometry("600x900")
        self.window.configure(background=BACKGROUND_COLOR)
        self.window.iconphoto(
            False, tkinter.PhotoImage(file=resource_path("src/TheTab_KGrgb_72ppi.png"))
        )

        self.window.protocol("WM_DELETE_WINDOW", self.close)

    def create_header_frame(self):
        """Create and initialize the header."""
        self.header_frame = tkinter.Frame(
            self.window, pady=10, background=BACKGROUND_COLOR
        )

        self.title_label = tkinter.Label(
            self.header_frame,
            text="Trial Tracking",
            font=("Times New Roman", 40),
            background=BACKGROUND_COLOR,
        )
        self.title_label.pack()

        self.header_frame.pack()

    def create_input_frame(self):
        """Create the frame for trial input."""
        self.input_frame = tkinter.Frame(self.window, background=BACKGROUND_COLOR)

        # File name
        self.file_label = tkinter.Label(
            self.input_frame,
            text="Filename:",
            font=("Arial Bold", 12),
            background=BACKGROUND_COLOR,
        )
        self.file_input = tkinter.StringVar(value=f"{self.expState.participantId}.csv")
        self.file_entry = tkinter.Entry(
            self.input_frame,
            textvariable=self.file_input,
            font=("Arial", 12),
            state="disabled",
        )
        self.file_label.pack()
        self.file_entry.pack(pady=(0, 10))

        # Trial Order
        self.trial_order_label = tkinter.Label(
            self.input_frame,
            text="Trial Label Order:",
            font=("Arial Bold", 12),
            background=BACKGROUND_COLOR,
        )
        self.trial_order_input = tkinter.StringVar(
            value="".join(self.expState.trial_label_order)
        )
        self.trial_order_entry = tkinter.Entry(
            self.input_frame,
            textvariable=self.trial_order_input,
            font=("Arial", 12),
            state="disabled",
        )
        self.trial_order_label.pack()
        self.trial_order_entry.pack(pady=(0, 10))

        # Copy id button
        def copy_id():
            self.window.clipboard_clear()
            self.window.clipboard_append(self.expState.participantId)

        self.copyid_button = tkinter.Button(
            self.input_frame,
            text="Copy ID to Clipboard",
            font=("Arial Bold", 10),
            background="light gray",
            activebackground="dark gray",
            width=20,
            height=3,
            command=copy_id,
        )
        self.copyid_button.pack(pady=(20, 10))

        self.input_frame.pack()

    def create_button_frame(self):
        """Create the frame for trial change."""
        self.button_frame = tkinter.Frame(self.window, background=BACKGROUND_COLOR)
        self.button_main_frame = tkinter.Frame(
            self.button_frame, background=BACKGROUND_COLOR
        )

        # Trial Button
        self.start_button = tkinter.Button(
            self.button_main_frame,
            text="Start Trial",
            font=("Arial Bold", 10),
            background="green",
            activebackground="dark green",
            foreground="black",
            width=20,
            height=10,
            command=self.start_trial,
        )
        self.start_button.pack(side=tkinter.LEFT, padx=(0, 10))

        self.stop_button = tkinter.Button(
            self.button_main_frame,
            text="Stop Trial",
            font=("Arial Bold", 10),
            background="light gray",
            activebackground="dark red",
            foreground="black",
            width=20,
            height=10,
            state="disabled",
            command=self.stop_trial,
        )
        self.stop_button.pack(side=tkinter.RIGHT, padx=(10, 10))

        self.button_main_frame.pack(side=tkinter.LEFT)

        self.reset_button = tkinter.Button(
            self.button_frame,
            text="Reset Trial",
            font=("Arial Bold", 7),
            background="yellow",
            activebackground="gold",
            foreground="black",
            width=10,
            height=15,
            command=self.reset_trial,
        )
        self.reset_button.pack(side=tkinter.RIGHT, padx=(10, 0))

        self.button_frame.pack(pady=(40, 0))

    def create_progress_frame(self):
        """Create the frame for progress display."""
        self.progress_frame = tkinter.Frame(self.window, background=BACKGROUND_COLOR)

        # Trial Label
        self.current_trial_label = tkinter.Label(
            self.progress_frame,
            text=f"Current Trial Label: {self.expState.trial_label_order[0]}",
            font=("Arial Bold", 24), # changed from 12 to 24 for readability
            background=BACKGROUND_COLOR,
        )
        self.current_trial_label.pack(pady=(10, 0))

        # Piece Label
        self.current_piece_label = tkinter.Label(
            self.progress_frame,
            text="Placed Pieces: 0",
            font=("Arial Bold", 12),
            background=BACKGROUND_COLOR,
        )
        self.current_piece_label.pack(pady=(10, 0))

        self.progress_frame.pack(pady=(0, 10))

    def create_status_frame(self):
        """Create the frame for Bluetooth connection status."""
        self.status_frame = tkinter.Frame(self.window, background=BACKGROUND_COLOR)

        # Bluetooth Status Label
        self.bluetooth_status_label = tkinter.Label(
            self.status_frame,
            text="Bluetooth Status: Checking...",
            font=("Arial Bold", 20),
            background=BACKGROUND_COLOR,
            foreground="blue",
        )
        self.bluetooth_status_label.pack(pady=(10, 0))

        self.status_frame.pack(pady=(10, 10))

    def update_bluetooth_status(self, is_connected):
        """Update the Bluetooth status label."""
        if is_connected is None:
            self.bluetooth_status_label.config(
                text="Bluetooth Status: Not Required",
                foreground="gray",
            )
        elif is_connected:
            self.bluetooth_status_label.config(
                text="Bluetooth Status: Connected to T01",
                foreground="green",
            )
        else:
            self.bluetooth_status_label.config(
                text="Bluetooth Status: Not Connected to T01",
                foreground="red",
            )




    def start_trial(self, event=None):
        """Start a trial."""

        if Window.num_completed_trials == 0:
            #start_camera() #start pipeline in main
            # self.expState.pipeline.start(self.expState.config)

            self.expState.start_camera()
            self.expState.startEpochTime = datetime.now().timestamp()
            self.expState.startDateTime = datetime.now().strftime("%Y-%m-%d %H:%M:%S") 
            self.expState.save_snapshot(0)
            with open(self.expState.participants_file,'a') as fout:
                fout.write('%s,%s,%f,%s\n'%(self.expState.participantId,self.expState.tag,self.expState.startEpochTime,self.expState.startDateTime))

            self.start_time_limit_timer()

        # Change the button
        self.start_button.config(state="disabled", background="light gray")
        self.stop_button.config(state="normal", background="red")
        self.current_piece_label.config(text="Placed Pieces: 0")
        Window.is_in_trial = True

    def stop_trial(self):
        """Stop a trial."""
        # Save snapshot
        self.expState.save_snapshot(self.expState.trial_label_order[Window.num_completed_trials])

        # Change trial
        Window.num_completed_trials += 1
        if Window.num_completed_trials != self.expState.num_trials:
             self.current_trial_label.config(
                    text=f"Current Trial Label: {self.expState.trial_label_order[Window.num_completed_trials]}" # 1 added to display current trial
                )
        if Window.num_completed_trials < self.expState.num_trials:
            Window.piece_num = 0

            # Change the button
            self.start_button.config(state="normal", background="green")
            self.stop_button.config(state="disabled", background="light gray")

        # Move on to errors
        else:
            self.start_button.config(state="disabled", background="light gray")
            self.stop_button.config(state="disabled", background="light gray")

            self.expState.is_trials_complete = True
            self.close()

        Window.is_in_trial = False

    def mark_date(self, evnt_time):
        """Mark the date in a trial."""
        # Return if there is not a trial ongoing
        if Window.is_in_trial is False:
            return

        #self.expState.trial_times[Window.num_completed_trials].append(datetime.now())
        self.expState.trial_times[Window.num_completed_trials].append(evnt_time)
        self.current_trial_label.config(
            text=f"Current Trial Label: {self.expState.trial_label_order[Window.num_completed_trials]}"
        )

        if Window.piece_num == 0:
            text = "Placed Pieces: Initialized"
        else:
            text = f"Placed Pieces: {Window.piece_num}"

        self.current_piece_label.config(text=text)

        Window.piece_num += 1

    def reset_trial(self, event=None):
        """Reset the date in a trial."""
        # Return if there is not a trial ongoing
        if Window.is_in_trial is False:
            return

        self.expState.trial_times[Window.num_completed_trials] = []
        self.current_piece_label.config(text="Placed Pieces: 0")

        Window.piece_num = 0

    def start(self):
        """Start the window main loop."""
        self.window.mainloop()

    def close(self):
        """Handle closing the window."""
        # Check closing type
        if self.expState.is_trials_complete is False:
            res = tkinter.messagebox.askokcancel(
                "Exit Program", "Save current data and exit?"
            )
            if not res:
                return
            self.expState.is_trials_complete = True

        # Wait for main to finish writing to the file
        while self.expState.is_finished_main is False:
            time.sleep(0.05)

        if self.time_limit_job:
            self.window.after_cancel(self.time_limit_job)
            self.time_limit_job = None
        
        stop_camera = getattr(self.expState, "stop_camera", None)
        if callable(stop_camera):
            stop_camera()

        self.window.quit()

    def start_time_limit_timer(self):
        """Begin countdown for the experiment time limit, if configured."""
        if getattr(self.expState, "time_limit_seconds", 0) <= 0:
            return
        if self.expState.time_limit_deadline:
            return
        self.expState.time_limit_deadline = datetime.now().timestamp() + self.expState.time_limit_seconds
        self.time_limit_job = self.window.after(500, self.check_time_limit)

    def check_time_limit(self):
        """Poll the time limit and trigger expiration when reached."""
        self.time_limit_job = None
        if self.expState.is_trials_complete or self.expState.time_limit_deadline is None:
            return

        if datetime.now().timestamp() >= self.expState.time_limit_deadline:
            self.handle_time_limit_expired()
            return

        self.time_limit_job = self.window.after(500, self.check_time_limit)

    def handle_time_limit_expired(self):
        """Gracefully stop the experiment when the time limit is reached."""
        if self.time_limit_triggered:
            return

        self.time_limit_triggered = True
        print("Time limit reached; stopping experiment.")

        if Window.is_in_trial:
            self.stop_trial()

        self.start_button.config(state="disabled", background="light gray")
        self.stop_button.config(state="disabled", background="light gray")
        self.reset_button.config(state="disabled", background="light gray")
        self.expState.is_trials_complete = True
        self.window.after(0, self.close)
