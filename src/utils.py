"""Utility refactored from main."""

import os
import sys
from datetime import datetime


class ExperimentState:
    """A class to transfer data between the main program and window."""

    def __init__(self, tag, participants_file,num_trials,participantId):
        # Instance attributes
        self.tag = tag
        self.participants_file = participants_file 
        self.num_trials = num_trials
        self.participantId = participantId
        self.trial_label_order = ['%i'%(idx+1) for idx in range(self.num_trials) ]
        self.trial_times = [list() for _ in range(self.num_trials)]

        self.num_misplaced: int = 0
        self.num_unplaced: int = 0
        self.num_placed_clusters: int = 0

        self.is_trials_complete: bool = False
        self.is_finished_main: bool = False
        self.t01_present: bool = False
        self.time_limit_seconds = 0
        self.time_limit_deadline = None
        self.data_root = None
        self.data_path = None
        self.bug_log_path = None
        self.log_wait_alerted = False

def resource_path(relative_path: str):
    """Get absolute path to resource."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def log_bug(exp_state, message: str):
    """Append a bug entry to the experiment's log file."""
    log_path = getattr(exp_state, "bug_log_path", None)
    if not log_path:
        return
    timestamp = datetime.now().isoformat()
    try:
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, "a") as log_file:
            log_file.write(f"[{timestamp}] {message}\n")
    except Exception as exc:
        print(f"Failed to write bug log: {exc}")
