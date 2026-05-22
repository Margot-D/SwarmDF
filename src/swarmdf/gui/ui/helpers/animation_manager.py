class AnimationManager:
    """
    Manage synchronized GUI animations using a shared playback state.

    Multiple animation tracks can be registered to the same state,
    allowing several GIFs/widgets to stay synchronized while sharing
    a single timing loop and playback controls.

    state contains:
    - tracks        : registered animation tracks
    - frame_index   : global animation frame index
    - playing       : playback state
    - job           : scheduled callback reference ID
    - delay         : animation "speed" in ms/frame (i.e. delay between frames in ms)
    - scheduler     : callback scheduling function (e.g. after)
    - cancel        : callback cancellation function (e.g. after_cancel)
    """

    def register_track(self, frames, widget, state):
        """
        Register an animation track linked to a widget (GUI container).
        The track is stored but playback is not started automatically.
        """

        track = {"frames": frames, "widget": widget}
        state["tracks"].append(track)
        
        return track


    def update_tracks(self, state):
        """
        Update all registered animation widgets to the shared frame index.

        Each track (animation) uses the shared frame counter stored in 'state',
        allowing multiple animations to remain synchronized.
        """

        # Get current global frame index
        i = state["frame_index"]

        # Loop over all register animations
        for track in state["tracks"]:

            frames = track["frames"] # images
            widget = track["widget"] # associated widget/container

            # Select which frame (index i) to display
            frame = frames[i % len(frames)]

            # Display frame on widget
            widget.configure(image=frame, text="")
            widget.image = frame


    def play_generic(self, state):
        """
        Advance the shared frame counter and update all registered tracks.
        This acts as the central animation loop for synchronized playback.
        """

        if not state["playing"]:
            return

        state["frame_index"] = (state["frame_index"] + 1)
        self.update_tracks(state)

        # schedule next call to play_generic() after 'delay' ms
        state["job"] = state["scheduler"](state["delay"], lambda: self.play_generic(state))
    

    def toggle_play_pause_generic(self, state):
        """
        Toggle animation playback state and start/stop the timing loop.
        """

        state["playing"] = not state["playing"]

        if state["playing"]:
            self.play_generic(state)
        else: # pause animation
            if state["job"]:
                state["cancel"](state["job"])
                state["job"] = None
        
        return state["playing"]


    def step_frame_generic(self, state, step, toggle_callback=None):
        """
        Manually step animations forward or backward by one frame.
        """

        # if animation is playing, first pause it and update icon using the toggle_callback logic
        if state.get("playing", False) and toggle_callback is not None:
            toggle_callback()

        state["playing"] = False

        if state["job"]:
            state["cancel"](state["job"])
            state["job"] = None

        state["frame_index"] = state["frame_index"] + step

        self.update_tracks(state)