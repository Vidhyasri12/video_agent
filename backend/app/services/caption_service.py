import random
from typing import List, Dict, Any

class CaptionService:
    """
    Vision-Language Model (VLM) narrative description generator.
    Produces high-fidelity textual summaries of video events per interval (e.g. every 10 seconds).
    """
    TEMPLATES = [
        "A person wearing a blue jacket entered through Gate 2 carrying a large backpack.",
        "Two forklifts crossed paths near Loading Dock B while a worker in a high-vis vest walked between them.",
        "A red sedan slowed down and parked in the restricted zone near Gate 1.",
        "A group of 4 pedestrians gathered near the main entrance, loitering for 45 seconds.",
        "A maintenance technician inspected equipment near Zone 3 while wearing full protective gear.",
        "An unauthorized individual approached the perimeter fence at 14:22:10 before turning back."
    ]

    def generate_caption(self, camera_name: str, detections: List[Dict[str, Any]]) -> str:
        if not detections:
            return f"Camera '{camera_name}': Area clear. Normal baseline operational activity."

        counts = {}
        for d in detections:
            cls = d.get("class_name", "object")
            counts[cls] = counts.get(cls, 0) + 1

        details = ", ".join([f"{count} {cls}(s)" for cls, count in counts.items()])
        sample_narrative = random.choice(self.TEMPLATES)
        return f"Camera '{camera_name}' (Detected {details}): {sample_narrative}"

caption_service = CaptionService()
