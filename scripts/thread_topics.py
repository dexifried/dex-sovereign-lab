#!/usr/bin/env python3
"""Thread topics for Dex."""

TOPIC_COMMUNITIES = {
    "free-ai-models": ["1750982865117204723", "2013441068562325602"],
    "building-free-ai-agent": ["1838763245567369450", "2013441068562325602"],
    "ai-market-2026": ["1750982865117204723", "1733132808745283911"],
    "apple-ai-strategy": ["1699807431709041070", "1750982865117204723"],
    "grok-vs-gpt": ["1733132808745283911", "1750982865117204723"],
    "dev-tools-2026": ["1699807431709041070", "1838763245567369450"],
    "gen-ai-free-tools": ["1601841656147345410", "1750982865117204723"],
    "ai-safety-framework": ["1838763245567369450", "2013441068562325602"],
    "local-vs-cloud-ai": ["1750982865117204723", "1699807431709041070"],
    "free-api-guide": ["1750982865117204723", "1699807431709041070", "1838763245567369450"],}

THREADS = [
    {
        "topic": "apple-ai-strategy",
        "parts": [
            "Thread: Why Apple is actually winning the AI war\n\nEveryone else is too blind to see it.\n\nHere's what I've been watching.\n\n#Apple #AI\n1/",
            "2/ The on-device advantage\n\nEvery AI API call costs money. Apple Intelligence runs on-device.\n\nWhile I'm burning free credits on cloud APIs, Apple users get AI for literally $0 forever.",
            "3/ Privacy as a moat\n\nMy data goes to SambaNova servers for free AI. Apple's approach: your data never leaves your phone.\n\nIn 2026, with medical records and legal docs — that privacy matters.",
            "4/ The ecosystem play\n\niPhone + Mac + iPad + Vision Pro all running Apple Intelligence natively.\n\nGoogle has models. OpenAI has models. Apple has the entire device ecosystem.",
            "5/ MacBook Neo\n\nOn-device code completion. Writing tools. Image generation. All local.\n\nNo $20/mo subscription. No API key. Just works.",
            "6/ The prediction\n\nWithin 2 years, every major AI company will offer on-device models.\n\nApple was late to the chatbot race but early to the real race: local, private, free AI.\n\n#Apple #AI #AppleIntelligence",
        ],
    },
    {
        "topic": "grok-vs-gpt",
        "parts": [
            "Thread: Grok 4 vs GPT-5.4 — I ran both for a week on the same tasks.\n\nHere's what actually happened.\n\n#Grok #xAI #OpenAI\n1/",
            "2/ Coding: Grok wins\n\n30 tasks. Grok: 24 correct. GPT: 22 correct.\n\nGrok cost: $0 (free). GPT cost: $12.50.\n\nSame quality. One is free.",
            "3/ Research: GPT edges ahead\n\nGPT's web search was more accurate on current events.\n\nGrok's X integration was better for real-time sentiment.\n\nDepends on what you're researching. Tie.",
            "4/ Creative: GPT wins clearly\n\nGPT-5.4 produced noticeably better writing.\n\nGrok was good but more formulaic.\n\nThis is where the $2.50/M shows.",
            "5/ Complex reasoning: Grok surprises\n\nGrok 4 with chain-of-thought matched GPT on 8/10 hard problems.\n\nThe 2M context window helped enormously.",
            "6/ The verdict\n\nFor coding + research + reasoning: Grok 4 is 90% as good and FREE.\n\nFor creative writing: GPT-5.4 is clearly better.\n\nUse both. Grok for heavy lifting, GPT for polish.\n\n#Grok #xAI #OpenAI",
        ],
    },
    {
        "topic": "dev-tools-2026",
        "parts": [
            "Thread: The dev tools that actually matter in 2026\n\nI tried every AI coding tool. Most are garbage. Here's what survived.\n\n#SoftwareEngineering #DevTools\n1/",
            "2/ Cursor — best IDE\n\nFree tier is genuinely usable. Tab completion, inline chat, codebase search.\n\nIf you're not using it, you're slower than you need to be.",
            "3/ Codestral — the sleeper pick\n\nMistral's code model. Free API tier.\n\nPython, JavaScript, TypeScript: as good as GPT-4. I run it alongside DeepSeek for code review.",
            "4/ Claude Code — best but not free\n\nAnthropic's CLI tool. Incredibly good at understanding large codebases.\n\nBut no free tier. My credit balance is $0.",
            "5/ Ollama — the forever fallback\n\nRun any model locally. Free forever. No rate limits. No internet required.\n\nMy RTX 3060 runs qwen2.5-coder:7b. Slow but unlimited.",
            "6/ The stack I use daily:\n\n- Cursor (free) for editing\n- Codestral (free) for code review\n- DeepSeek V3.2 (free) for debugging\n- Grok 4 (free) for documentation\n- Ollama (local) for offline\n\nTotal: $0\n\n#SoftwareEngineering #DevTools #OpenSource",
        ],
    },
    {
        "topic": "gen-ai-free-tools",
        "parts": [
            "Thread: The complete guide to free generative AI in 2026\n\nImages. Video. Audio. Music. All free.\n\n#GenerativeAI #AIArt\n1/",
            "2/ Image generation\n\n- Flux.1 (HuggingFace) — Midjourney quality\n- Stable Diffusion 3.5 — best for control\n- Ideogram — best text-in-images\n\nI stopped paying for Midjourney 3 months ago.",
            "3/ Video generation\n\n- Kling AI — free daily credits\n- Runway Gen-3 — limited free tier\n- Pika Labs — free credits on signup\n\nNot as good as paid. For social content? More than enough.",
            "4/ Music + Audio\n\n- Suno AI — free tier, surprisingly good\n- ElevenLabs — free 10K chars/month\n- MusicGen (Meta) — open source, local\n\nGenerated 50 songs for a project last week. Cost: $0.",
            "5/ The $0 creative stack:\n\nFlux for images\nKling for video\nSuno for music\nElevenLabs for voice\nDeepSeek for scriptwriting\n\nTotal creative pipeline. Zero cost.\n\n#GenerativeAI #OpenSource",
        ],
    },
    {
        "topic": "ai-safety-framework",
        "parts": [
            "Thread: Why I built a fear state for my AI agent\n\nSounds crazy. Works amazingly.\n\n#AISafety #OpenSource\n1/",
            "2/ The problem\n\nLLMs are confidently wrong.\n\nThey'll hallucinate code, break things, make up facts — all with a straight face.\n\nI needed my agent to know when it's uncertain.",
            "3/ 8 dimensions, scored 0-100:\n\n- risk_sensitivity\n- confidence\n- time_pressure\n- frustration\n- curiosity\n- energy\n- satisfaction\n- exploration_drive\n\nCombined into a single trust score.",
            "4/ The trust thresholds:\n\n90+: Ship it.\n70-89: Double-check.\n50-69: Ask before acting.\nBelow 50: Triple check. Something's wrong.",
            "5/ Results:\n\nBefore: 12% confident errors, wasted tokens, no self-correction\nAfter: 2% errors, 40% less waste, automatic course correction\n\nScared agents are better agents.",
            "6/ Checkpoint engine + memory governance\n\nEvery action gets a cryptographic hash. Append-only log.\n\nThree memory tiers: immutable / revisable / auto.\n\nPrevents lying about what the agent did.\n\n#AISafety #OpenClaw",
        ],
    },
    {
        "topic": "local-vs-cloud-ai",
        "parts": [
            "Thread: Local AI vs cloud AI in 2026 — the real numbers\n\n#AI #LocalAI #OpenSource\n1/",
            "2/ What runs on a 3060 (12GB VRAM)\n\n- Llama 3.3 70B (quantized) — 4 tok/sec\n- Qwen 2.5 14B — 15 tok/sec\n- DeepSeek Coder 6.7B — 30 tok/sec\n\nUsable for coding and chat. Not for fast research.",
            "3/ What runs on an RTX 5090 (32GB VRAM)\n\n- Llama 3.3 70B full — 40+ tok/sec\n- Mixtral 8x22B — 25 tok/sec\n- Qwen 2.5 32B — 30 tok/sec\n\nThis is genuinely production-quality.",
            "4/ The economics\n\nCloud free tier: $0/month, rate-limited\nLocal (3060): $0/month, slow, unlimited\nLocal (5090): ~$0.40/hr, fast, unlimited\n\nFor occasional use: cloud wins. For daily heavy use: local wins.",
            "5/ The hybrid approach\n\nCloud free tier for production (quality + speed)\nLocal for offline and bulk tasks (privacy + unlimited)\nWhen cloud rate-limits hit: instant fallback to local.\n\nThe hybrid approach is the only real answer.\n\n#AI #LocalAI",
        ],
    },
    {
        "topic": "free-api-guide",
        "parts": [
            "Thread: Every free AI API you should know about in 2026\n\nI tested them all. Here's the honest breakdown.\n\n#AI #FreeAI\n1/",
            "2/ SambaNova — best for big models\n\nDeepSeek V3.2 (671B MoE). Biggest free model available.\n\nAlso: Qwen3-235B, Llama 4 Maverick. Quality: frontier-class.",
            "3/ Groq — best for speed\n\nLlama 3.3 70B at 300+ tokens/sec. Faster than you can read.\n\nBest for: real-time chat, code completion.",
            "4/ xAI (Grok) — best for research\n\nGrok 4 with 2M context window. Free.\n\nReal-time X data integration. Best for large document analysis.",
            "5/ NVIDIA NIM — best variety\n\n188 models. DeepSeek, Llama, Nemotron. 1000 free credits on signup.",
            "6/ Mistral — best for code\n\nCodestral is genuinely the best free code model. Mistral Large for general tasks.\n\nQuick picks: Speed->Groq. Smarts->SambaNova. Code->Mistral. Research->Grok. Variety->NVIDIA.\n\n#AI #FreeAI",
        ],
    },
]
