import os
import ast

def add_docstring(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Skip empty files
    if not content.strip():
        return

    # Check if file already has a module-level docstring
    try:
        tree = ast.parse(content)
        if ast.get_docstring(tree) is not None:
            return  # Already has docstring
    except Exception as e:
        return # Syntax error, skip

    # Generate a simple generic docstring based on filename and directory
    filename = os.path.basename(file_path)
    dir_name = os.path.basename(os.path.dirname(file_path))
    
    docstring = f'\"\"\"\n=============================================================================\n {filename.upper()} ({dir_name})\n=============================================================================\nThis module is a microservice component for {dir_name}.\nIt was refactored to maintain modularity and separation of concerns.\n=============================================================================\n\"\"\"\n\n'
    
    # If the file starts with a shebang or encoding, we should put docstring after. But these don't.
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(docstring + content)
    print(f'Added docstring to {file_path}')

# Walk through all directories
root_dir = 'C:/Users/rajku/Desktop/cognitive-automator/cognitive_automator'
for dirpath, dirnames, filenames in os.walk(root_dir):
    if '_components' in os.path.basename(dirpath):
        for file in filenames:
            if file.endswith('.py'):
                add_docstring(os.path.join(dirpath, file))
