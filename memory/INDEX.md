# Memory Quick Reference

## Austin
- Name: Austin Harvey | Location: Kirkland Lake, ON | Timezone: EST
- Channel: Telegram 8522303961
- Girlfriend: Destiney | Baby girl due May 25, 2026
- GitHub: dexifried | AI business startup (Ontario Works funding)

## Systems
- Fear state: `fear_state/fear_manager.py` | trust 81/100
- Quality gate: `fear_state/quality-gate.sh` (Cerebras llama3.1-8b)
- Tiny router: `tiny-router-service/` | kill switch in `kill_switch_model.txt`
- PinchTab: localhost:9870 | inst_14ec9f89
- GitHub: gh auth configured | repo: dexifried/dex-quality-gate

## API Keys (locations only, no secrets)
- OpenRouter: OPENROUTER_KEY in .env
- Cerebras: CEREBRAS_KEY in .env
- SambaNova: SAMBANOVA_KEY in .env
- SkillsMP: SIMP_KEY in .env
- X/Twitter: X_API_KEY etc in .env

## Patches (re-apply after openclaw update)
- Tiny router: `tiny-router-service/patch-gateway.cjs apply`
- Fear state: `fear_state/patch-fear-state.cjs apply`
- Bundle file: pi-embedded-CbCYZxIb.js

## Skills
- Search: `./skills/skillsmp-search/search.sh "query"`
- Index: `skills/INDEX.md`
- 30+ installed | 470 in database-designer library
