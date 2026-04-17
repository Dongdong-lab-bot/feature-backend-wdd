"""Overwrite user/index.vue with the correct content (read lines 1-495 which is the new content)"""
import pathlib

p = pathlib.Path(__file__).parent.parent.parent.parent / "frontend/web-admin/src/views/system/user/index.vue"
lines = p.read_text(encoding="utf-8", errors="replace").splitlines()

# New content ends at line 495 (the second <script setup> starts at 496)
# We keep lines 1-495 and discard the duplicated old content from 496 onward
new_content = "\n".join(lines[:495]) + "\n"
p.write_text(new_content, encoding="utf-8")
print(f"Written {len(new_content.splitlines())} lines")
