#!/bin/sh -l
#

echo "🚗 ===== OK we are in ====="
echo "⚙️ ===== args = $@ "
echo "🌳 ===== env follows"
env
echo "🌳 ===== end env "
echo "📁 ===== directory / follows"
ls -F /
echo "📁 ===== directory / ends"
echo "📂 ===== workspace follows"
ls -F /github/workspace
echo "📂 ===== workspace ends"
echo "🛑 the end"
exit 0
