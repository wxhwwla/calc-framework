import os, re

ROOT = 'endfield_damage_calculator'

# Files to update: gui_design.search_ui.* -> gui_design.controls.search.*
files_to_fix = [
    'gui_design/shell/qt_app.py',
    'gui_design/shell/qt_control_dock.py',
    'gui_design/controls/search/qt_actions.py',
    'gui_design/controls/enhancement/qt_dialogs.py',
    'tests/calculation/search/plan/single_skill/test_search_settings.py',
    'tests/calculation/search/plan/test_search_controls.py',
]

for rel in files_to_fix:
    fpath = os.path.join(ROOT, rel)
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    new_content = content.replace(
        'from gui_design.search_ui',
        'from gui_design.controls.search'
    )
    
    if new_content != content:
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f'Updated: {rel}')
    else:
        print(f'No change: {rel}')

print('Done!')
