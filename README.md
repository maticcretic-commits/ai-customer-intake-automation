# AI Customer Intake Automation

A portfolio practice project: an **AI customer-intake agent** — the flat-fee
build agencies white-label for professional-service firms (chatbot, lead
capture, booking assistant, CRM push).

> Demo/study project — wire a real CRM and calendar before production use.

## Pipeline

1. **Extract** — free-text chat turns parsed into fields (name, service,
   email, phone, urgency).
2. **Validate** — email/phone formats checked; the agent re-asks on errors.
3. **Score** — 0–100 lead score from service value + contact completeness
   + urgency signals.
4. **Book** — earliest matching slot from `data/slots.json`.
5. **Push** — qualified lead POSTed to `CRM_WEBHOOK_URL` (dry-run logged
   when unset).

## Run

```bash
python intake_agent.py --demo     # scripted conversation
python intake_agent.py --chat     # interactive chat in your terminal
python tests/test_intake.py       # no API key, no network
```

## What I'd build next (learning roadmap)

- [ ] LLM function-calling extractor instead of regex
- [ ] Real CRM integration (GoHighLevel / HubSpot)
- [ ] Calendar API for live availability
- [ ] Multi-language intake

## Support My Work

If you find this project useful, consider supporting my work with a Bitcoin donation:

`BC1Q6Q75K8ZJXVW7W02LMDPRPY6XX6QK4LZZ2RMVAY`
