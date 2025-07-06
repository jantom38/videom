import json
import os

class TemplateManager:
    def __init__(self, template_file="template.json"):
        self.template_file = template_file

    def save_template(self, pre_clips, post_clips):
        """Save the pre and post clips as a default template to a JSON file."""
        template_data = {
            "pre_clips": pre_clips,
            "post_clips": post_clips
        }
        try:
            with open(self.template_file, 'w') as f:
                json.dump(template_data, f, indent=4)
            return True, "Template saved successfully!"
        except Exception as e:
            return False, f"Error saving template: {str(e)}"

    def load_template(self):
        """Load the default template from a JSON file."""
        try:
            if os.path.exists(self.template_file):
                with open(self.template_file, 'r') as f:
                    template_data = json.load(f)
                    # Validate that template_data contains pre_clips and post_clips
                    if not isinstance(template_data, dict):
                        return False, "Invalid template format: expected a dictionary."
                    pre_clips = template_data.get("pre_clips", [])
                    post_clips = template_data.get("post_clips", [])
                    if not (isinstance(pre_clips, list) and isinstance(post_clips, list)):
                        return False, "Invalid template format: pre_clips and post_clips must be lists."
                    return True, {"pre_clips": pre_clips, "post_clips": post_clips}
            return False, "No template found."
        except Exception as e:
            return False, f"Error loading template: {str(e)}"