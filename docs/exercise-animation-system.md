# GymAI exercise visual system

Exercise visuals are editorial media records stored in `exercise_media`; the React detail page does not invent or approximate exercise motion. It selects reviewed local media, preferring `ready`/`approved` primary records before considering media format. Records marked `failed`, `deprecated`, or `rejected` are hidden. The retired `GymAI Visual Pipeline` provider is also explicitly excluded in the player as a migration safeguard.

ExerciseDB-style GIFs render on a square white illustration stage inside the existing responsive GymAI player. A GIF uses its `media_url` when motion is allowed. When `prefers-reduced-motion: reduce` is active, the player uses the generated first-frame `poster_url` instead. GIFs intentionally have no play or speed controls because an `<img>` cannot control GIF playback accurately. Reviewed videos keep play, replay, and speed controls.

When no reviewed media is installed, the player shows a clear unavailable state and keeps written instructions accessible. There is no procedural character fallback and no hard-coded bundled animation URL.

See [ExerciseDB local media import](exercisedb-media-import.md) for the asset ingestion workflow.
