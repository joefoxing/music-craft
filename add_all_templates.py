import json

# Load existing templates_complete.json
with open('app/static/templates/templates_complete.json', 'r') as f:
    data = json.load(f)
existing = data['templates']
existing_ids = {t['id'] for t in existing}
print(f"Loaded {len(existing)} existing templates with IDs: {sorted(existing_ids)}")

# Helper to load templates from a Python file (simplified)
def load_templates_from_py(filepath, variable_name):
    import ast
    with open(filepath, 'r') as f:
        content = f.read()
    # Parse the Python file to find the variable assignment
    tree = ast.parse(content)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == variable_name:
                    # Evaluate the value safely
                    try:
                        # Use eval with a limited environment
                        env = {}
                        exec(compile(ast.Expression(node.value), '<string>', 'eval'), {}, env)
                        return env['__result__'] if '__result__' in env else node.value
                    except:
                        # Fallback: try to extract via string parsing (crude)
                        import re
                        match = re.search(rf'{variable_name}\s*=\s*(\[.*?\])', content, re.DOTALL)
                        if match:
                            import json
                            # The list may not be valid JSON due to Python syntax
                            # We'll use ast.literal_eval
                            import ast
                            try:
                                return ast.literal_eval(match.group(1))
                            except:
                                pass
    return []

# Load templates from generate_templates.py (existing_templates variable)
# Since the file is valid Python, we can import it as a module
import sys
sys.path.insert(0, '.')
try:
    from generate_templates import existing_templates as gen_templates
    print(f"Loaded {len(gen_templates)} templates from generate_templates.py")
except Exception as e:
    print(f"Error importing generate_templates: {e}")
    # Fallback: define manually
    gen_templates = []

# Load templates from create_new_templates.py (new_templates variable)
try:
    from create_new_templates import new_templates as new_templates
    print(f"Loaded {len(new_templates)} templates from create_new_templates.py")
except Exception as e:
    print(f"Error importing create_new_templates: {e}")
    new_templates = []

# Combine all templates from both sources
all_templates = gen_templates + new_templates
print(f"Total templates from sources: {len(all_templates)}")

# Filter out templates that already exist
missing = []
for t in all_templates:
    if t['id'] not in existing_ids:
        missing.append(t)

print(f"Found {len(missing)} missing templates: {[t['id'] for t in missing]}")

# Ensure categories match dropdown options (we'll just trust they do)
# Append missing templates
existing.extend(missing)

# Update the data
data['templates'] = existing

# Write back
with open('app/static/templates/templates_complete.json', 'w') as f:
    json.dump(data, f, indent=2)

print(f"Updated templates_complete.json with {len(missing)} new templates. Total templates: {len(existing)}")