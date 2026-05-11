class AnimationManager:

    def register_track(self, frames, widget, state):
        """ 
        Register a GIF animation as a passive object.
        It does not start animation; it only stores frames and target label.
        (Swarm orbit and lompe plots) only
        """
        track = {"frames": frames, "widget": widget}
        state['tracks'].append(track)
        
        return track

    def update_tracks(self, state):
        """
        Draw current frame for all registered animations.
        """
        i = state["current_frame"]

        for track in state['tracks']:
            frames = track["frames"]
            widget = track["widget"]

            frame = frames[i % len(frames)]
            widget.configure(image=frame, text="")
            widget.image = frame  # keep reference

    def play_generic(self, state):
        """
        Advance global frame counter and update all animations.
        This is the single timing loop for the whole GUI (both GIFs).
        Timing loop
        """
        if not state["playing"]:
            return

        state["current_frame"] = (state["current_frame"] + 1) #) % len(state["frames"])
        self.update_tracks(state)

        state["job"] = state["scheduler"](state["delay"], lambda: self.play_generic(state))
    
    def toggle_play_pause_generic(self, state, buttons):
        """
        Play/pause animation
        """
        state["playing"] = not state["playing"]

        # icon = self.icons.pause if state["playing"] else self.icons.play
        # for btn in buttons:
        #     btn.configure(image=icon)

        if state["playing"]:
            self.play_generic(state)
        else:
            if state["job"]:
                state["cancel"](state["job"])
                state["job"] = None
        
        return state["playing"]

    def step_frame_generic(self, state, step, toggle_callback=None):
        """
        Manual stepping
        """
        # if currently playing → stop via existing logic (also updates icons)
        if state.get("playing", False) and toggle_callback is not None:
            toggle_callback()

        state["playing"] = False

        if state["job"]:
            state["cancel"](state["job"])
            state["job"] = None

        state["current_frame"] = state["current_frame"] + step

        self.update_tracks(state)