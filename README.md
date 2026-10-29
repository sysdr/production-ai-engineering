> 📬 **This code accompanies [Hands-On AI Agent Mastery](https://aiamastery.substack.com?utm_source=github&utm_medium=readme&utm_campaign=production-ai-engineering), a newsletter on building AI agents that survive production.**
> The written lessons explain the architecture, the design decisions and the production checklist behind each folder. Lessons 1–5 are free.

# Production AI Engineering

Working code for the **Production AI Engineering** course: AI agents built with the security, cost control, observability and isolation that real users require.

## Lessons

| # | Lesson (full walkthrough) | Code |
| --- | --- | --- |
| 1 | [The 4-Layer Secure Agent Architecture](https://aiamastery.substack.com/p/lesson-1-the-4-layer-secure-agent?utm_source=github&utm_medium=readme&utm_campaign=production-ai-engineering) | [`lesson1/aiam-day01`](lesson1/aiam-day01) |
| 2 | [Tool Execution and Validation](https://aiamastery.substack.com/p/lesson-2-tool-execution-and-validation?utm_source=github&utm_medium=readme&utm_campaign=production-ai-engineering) | [`lesson2/aiam-day02`](lesson2/aiam-day02) |
| 3 | [Memory Systems](https://aiamastery.substack.com/p/lesson-3-memory-systems?utm_source=github&utm_medium=readme&utm_campaign=production-ai-engineering) | [`lesson3/aiam-day03`](lesson3/aiam-day03) |
| 4 | [Rate Limiting and Cost Control](https://aiamastery.substack.com/p/lesson-4-rate-limiting-and-cost-control?utm_source=github&utm_medium=readme&utm_campaign=production-ai-engineering) | [`lesson4/aiam-day04`](lesson4/aiam-day04) |
| 5 | [Security Hardening](https://aiamastery.substack.com/p/lesson-5-security-hardening?utm_source=github&utm_medium=readme&utm_campaign=production-ai-engineering) | [`lesson5/aiam-day05`](lesson5/aiam-day05) |
| 6 | [Observability Stack](https://aiamastery.substack.com/p/lesson-6-observability-stack?utm_source=github&utm_medium=readme&utm_campaign=production-ai-engineering) | [`lesson6/aiam-day06`](lesson6/aiam-day06) |
| 7 | [Sandboxed Code Execution](https://aiamastery.substack.com/p/lesson-7-sandboxed-code-execution?utm_source=github&utm_medium=readme&utm_campaign=production-ai-engineering) | [`lesson7/aiam-day07`](lesson7/aiam-day07) |

## Running a lesson

Each lesson folder is self-contained, with a Dockerfile, `docker-compose.yml` and helper scripts:

```bash
cd lesson1/aiam-day01
./start.sh       # start the service
./demo.sh        # run the demo
./run_tests.sh   # run the tests
./stop.sh        # stop it
```

## Get the next lesson

New lessons publish in the newsletter first. Subscribe free at **[aiamastery.substack.com](https://aiamastery.substack.com?utm_source=github&utm_medium=readme&utm_campaign=production-ai-engineering)**.
