#!/bin/bash
# Check for new PR review comments every 10 minutes
GITHUB_TOKEN=$(grep "^GITHUB_TOKEN=" /root/.openclaw/workspace/.env | cut -d= -f2)
STATE_FILE="/root/.openclaw/workspace/memory/pr-last-check.txt"

curl -s "https://api.github.com/repos/dexifried/dex-sovereign-lab/pulls/1/comments?per_page=15&sort=created&direction=desc" \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" | python3 -c "
import json,sys,re
comments = json.load(sys.stdin)
if not comments:
    print('NO_NEW')
    sys.exit(0)

latest = comments[0]['commit_id'][:8]
new_on_latest = [c for c in comments if c['commit_id'].startswith(latest)]

if new_on_latest:
    print(f'REVIEW BOT: {len(new_on_latest)} issues on commit {latest}')
    for c in new_on_latest[:10]:
        body = re.sub(r'<[^>]+>', '', c.get('body','')).strip()
        title = body.split(chr(10))[0].replace('**','').strip()
        badge = 'P1' if 'P1' in c.get('body','') else 'P2' if 'P2' in c.get('body','') else '?'
        print(f'  [{badge}] {c[\"path\"]}:{c.get(\"line\",\"\")}')
        print(f'    {title}')
else:
    print('NO_NEW')
" > /tmp/pr_review.txt 2>&1

RESULT=$(cat /tmp/pr_review.txt)
if [ "$RESULT" != "NO_NEW" ]; then
    echo "$RESULT"
fi
