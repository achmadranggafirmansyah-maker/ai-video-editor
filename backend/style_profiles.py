STYLE_PROFILES = {
    "reference_fast_storytelling": {
        "name": "Reference — Fast Storytelling",
        "description": "Fast social-video pacing inspired by the uploaded reference: tight cuts, emphasis, punch-ins and strong captions.",
        "default_zoom": 1.08,
        "caption_style": "bold_social",
        "dead_air_threshold": 0.45,
        "rules": [
            "Prioritize a strong opening hook.",
            "Remove long pauses and low-information sections.",
            "Use subtle punch-in emphasis on important moments.",
            "Keep visual changes purposeful rather than constant.",
            "Use readable high-contrast captions.",
        ],
    },
    "clean_creator": {
        "name": "Clean Creator",
        "description": "Clean, restrained creator editing with gentle cuts and minimal emphasis.",
        "default_zoom": 1.03,
        "caption_style": "clean",
        "dead_air_threshold": 0.65,
        "rules": [
            "Keep natural pacing.",
            "Remove obvious dead air.",
            "Use restrained zooms.",
            "Use clean captions.",
        ],
    },
}
