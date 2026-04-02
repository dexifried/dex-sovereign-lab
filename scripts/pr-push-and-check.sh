#!/bin/bash
# Push changes, wait 4 minutes for review bot, fetch results
set -e
cd /root/.openclaw/workspace
git add -A
git commit -m "${1:-auto: update scripts}" 2>&1 | tail -2
git push origin fix/reply-bot-and-thread-cleanup 2>&1 | tail -2
echo ""
echo "Pushed. Waiting 4 minutes for review bot..."
sleep 240
echo ""
echo "=== Review Results ==="
GITHUB_TOKEN=$(grep "^GITHUB_TOKEN=" .env | cut -d= -f2)
curl -s "https://api.github.com/repos/dexifried/dex-sovereign-lab/pulls/1/comments?per_page=10&sort=created&direction=desc" \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" | python3 -c "
import json,sys,re
comments = json.load(sys.stdin)
latest = comments[0]['commit_id'][:8] if comments else 'none'
new = [c for c in comments if c['commit_id'].startswith(latest)]
if not new:
    print('No new issues on latest commit')
else:
    for c in new:
        body = re.sub(r'<[^>]+>', '', c.get('body','')).strip()
        title = body.split(chr(10))[0].replace('**','').strip()
        badge = 'P1' if 'P1' in c.get('body','') else 'P2' if 'P2' in c.get('body','') else '?'
        print(f'[{badge}] {c[\"path\"]}:{c.get(\"line\",\"\")}')
        print(f'  {title}')
" 2>&1
