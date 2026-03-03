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

def resource_path(relative_path: str):
    """Get absolute path to resource."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)
