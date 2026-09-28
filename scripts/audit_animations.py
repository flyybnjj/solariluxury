import os
import re
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_DIR = os.path.join(BASE_DIR, "mi_proyecto")

keyframes_regex = re.compile(r'@keyframes\s+([a-zA-Z0-9_-]+)\s*\{([^}]+(?:\}[^}]+)*)\}', re.MULTILINE)
transition_regex = re.compile(r'transition:\s*([^;]+);', re.IGNORECASE)
animation_property_regex = re.compile(r'animation(?:-name)?:\s*([^;]+);', re.IGNORECASE)
touch_hover_regex = re.compile(r'([^{]+):hover\s*\{', re.MULTILINE)
mouse_js_regex = re.compile(r'addEventListener\(\s*[\'"](mousemove|mouseover|mouseenter|mouseleave|scroll|touchmove)[\'"]', re.IGNORECASE)

def scan_files():
    report = {
        "keyframes": {},
        "transitions_samples": [],
        "hover_rules": [],
        "js_mouse_listeners": []
    }
    
    for root, dirs, files in os.walk(PROJECT_DIR):
        for f in files:
            if f.endswith(('.html', '.css', '.js')):
                filepath = os.path.join(root, f)
                rel_path = os.path.relpath(filepath, BASE_DIR)
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as fp:
                        content = fp.read()
                        
                        # Keyframes
                        for match in keyframes_regex.finditer(content):
                            name = match.group(1)
                            report["keyframes"][name] = rel_path
                            
                        # Hover rules
                        for match in touch_hover_regex.finditer(content):
                            selector = match.group(1).strip()
                            if len(selector) < 80:
                                report["hover_rules"].append({"file": rel_path, "selector": selector})
                                
                        # JS mouse/scroll
                        for match in mouse_js_regex.finditer(content):
                            event = match.group(1)
                            report["js_mouse_listeners"].append({"file": rel_path, "event": event})
                except Exception as e:
                    pass

    output_path = os.path.join(BASE_DIR, "capturas_mobile_audit", "animations_audit.json")
    with open(output_path, 'w', encoding='utf-8') as out:
        json.dump(report, out, indent=2, ensure_ascii=False)
    print(f"Animations audit saved to: {output_path}")
    print(f"Found {len(report['keyframes'])} keyframes animations.")
    print(f"Found {len(report['hover_rules'])} hover CSS rules.")
    print(f"Found {len(report['js_mouse_listeners'])} mouse/scroll JS listeners.")

if __name__ == "__main__":
    scan_files()
