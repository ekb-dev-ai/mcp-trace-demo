#!/usr/bin/env bash
# Print latest trace ops for a Jaeger service (video B-roll helper).
SERVICE="${1:-crew-incident-agent}"
curl -sf "http://localhost:16686/api/traces?service=${SERVICE}&limit=1" | python3 -c "
import json, sys
d = json.load(sys.stdin)
if not d.get('data'):
    print(f'No traces for service={sys.argv[1]}')
    sys.exit(0)
t = d['data'][0]
procs = {pid: p.get('serviceName', '?') for pid, p in t.get('processes', {}).items()}
print('traceID:', t['traceID'])
print('services:', sorted(set(procs.values())))
for s in sorted(t['spans'], key=lambda x: x['startTime']):
    print(f\"  {procs.get(s['processID'], '?')}: {s['operationName']}\")
" "$SERVICE"
