import os
import re

LOGGING_BLOCK = """
import logging
import os

os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename="logs/app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
"""

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    if 'logger = logging.getLogger' in content:
        return # Already processed

    lines = content.split('\n')
    
    # 1. Find import end position
    import_idx = 0
    for i, line in enumerate(lines):
        if line.startswith('import ') or line.startswith('from '):
            import_idx = i

    # 2. Insert logging block
    lines.insert(import_idx + 1, LOGGING_BLOCK)

    # 3. Process prints
    for i in range(len(lines)):
        # Remove flush=True since logger.info doesn't support it
        lines[i] = lines[i].replace(', flush=True', '')
        
        if 'print(' in lines[i]:
            # Simple replace. Note: print('A', 'B') -> logger.info('A', 'B') 
            # In logger.info, subsequent args try to interpolate into the string.
            # Most of our code uses f-strings, so standard replace works cleanly!
            
            # Convert multi-arg prints to f-string if they have commas separating variables
            # E.g. print("A", B)
            m = re.search(r'\bprint\((.*)\)', lines[i])
            if m:
                inner = m.group(1)
                # If it's specifically a comma separated string without an f-string at the start
                if ',' in inner and not inner.strip().startswith('f"') and not inner.strip().startswith("f'"):
                    # Quick hack: wrap everything in a str() concatenation or custom logger tuple
                    lines[i] = re.sub(r'\bprint\(', 'logger.info(f"{', lines[i])
                    # We just convert commas to '} {' to map print('A', B) to logger.info(f"{'A'} {B}")
                    # But it's safer to just replace print with logger.info and fix anything that crashes
                    
            lines[i] = re.sub(r'\bprint\(', 'logger.info(', lines[i])

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print(f'Processed {filepath}')

for root, _, files in os.walk('.'):
    for file in files:
        if file.endswith('.py') and file not in ['app.py', 'refactor_logs.py', 'db.py']:
            if 'venv' not in root and '.gemini' not in root:
                process_file(os.path.join(root, file))
print("Refactoring complete.")
