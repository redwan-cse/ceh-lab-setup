# API budget for a six-hour CEH practice session

The configured model remains `deepseek/deepseek-v4.1-flash-1017` through
OpenRouter's synchronous chat API. No batch model was activated or used for
inference tests. Time and number of flags do not determine the bill directly:
input and output tokens do, including growing conversation/tool context.

## Price snapshot and assumptions

On 12 November 2026, OpenRouter's [public endpoint catalogue](https://openrouter.ai/api/v1/models/deepseek/deepseek-v4.1-flash-1017/endpoints)
lists Morph at **$0.022 per million input tokens and $0.40 per million output
tokens**, matching the displayed low-cost normal-model prices. Other provider
routes cost more. The setup does not pin Morph or impose a price ceiling;
`cost_usd` in the terminal/API usage record is the provider-reported charge.
Cached input can reduce costs. These examples ignore cache discounts and
exclude credit-purchase fees, taxes and separate paid tool services.

At those normal-model rates:

```text
USD = input_tokens / 1,000,000 * 0.022
    + output_tokens / 1,000,000 * 0.40
```

## Example workload for 20 flags

These are planning scenarios, not a prediction that every flag is solvable
within a given number of calls. An API round may contain several tool calls.

| Scenario | API rounds | Average input / output per round | Total input / output | Estimated USD |
| --- | ---: | ---: | ---: | ---: |
| Short contexts | 400 | 10,000 / 1,000 | 4M / 0.4M | $0.25 |
| Moderate practice | 800 | 30,000 / 1,500 | 24M / 1.2M | $1.01 |
| Long contexts/retries | 1,200 | 100,000 / 2,500 | 120M / 3M | $3.84 |

At the displayed cheap route, **$1–5 of usage is a useful planning range**;
$10 credit gives headroom rather than a guarantee. Provider selection can
change that substantially: the middle scenario would cost $4.32 at
$0.15/M input and $0.60/M output. Inspect actual charges during practice.
Use separate task chats when context becomes irrelevant, search concise tool
references instead of loading whole guides, and avoid repeatedly sending raw
large files. Never discard evidence merely to reduce context.

## Why batch is not the exam driver

OpenRouter's [batch API](https://openrouter.ai/blog/announcements/batch-api/)
submits jobs asynchronously and polls for results; it allows a completion
window up to 24 hours. Its published beta median was seven minutes, which is
unsuitable for an interactive command/result/next-command loop. The current
wrapper does not implement batch submission/polling, so this is not a drop-in
model-name change.

The [batch endpoint catalogue](https://openrouter.ai/api/v1/models/deepseek/deepseek-v4.1-flash-1017%3Abatch/endpoints)
currently lists $0.05/M input and $0.15/M output, matching the screenshot.
Compared with $0.022/$0.40, batch is cheaper only when output tokens exceed
about **11.2% of input tokens**. The moderate, input-heavy example above would
cost $1.38 with those batch rates, versus $1.01 normally. Batch is a scheduling
and pricing option, not evidence of a more capable model. It may suit offline
independent document jobs, but the exam setup stays on the normal model.

Prices and availability vary; recheck the actual endpoint and usage dashboard
before funding a session. No additional provider or automatic fallback is added.

## Recorded local usage

The existing Server 2022 terminal log contained 54 normal-model requests with
reported costs: about 3,708 input and 246 output tokens per request on average,
totalling **$0.00814**. This is a short-workload sample, not a completed six-hour
20-flag benchmark, so the planning scenarios above allow much larger contexts.
The new approval/40-round validation uses offline fixtures; it does not submit
batch inference requests.
