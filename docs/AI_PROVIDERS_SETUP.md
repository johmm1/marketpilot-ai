# MARKETPILOT AI provider setup

The backend supports server-side AI routing. No AI key belongs in the frontend, browser storage, source control, or chat.

## Render environment variables

Set these in the MARKETPILOT backend service environment:

| Variable | Purpose | Suggested value |
|---|---|---|
| `GEMINI_API_KEY` | Gemini text and chart-image analysis | Your Google AI Studio key |
| `GEMINI_MODEL` | Gemini model | `gemini-2.5-flash` |
| `GROQ_API_KEY` | Groq text-analysis fallback | Your Groq console key |
| `GROQ_MODEL` | Groq text model | `llama-3.3-70b-versatile` |
| `OPENAI_API_KEY` | Optional text and image fallback | Your OpenAI API key |
| `OPENAI_MODEL` | OpenAI model | Keep the currently supported model for your account |
| `MARKETPILOT_AI_PRIMARY` | Preferred provider | `gemini`, `groq`, or `openai` |

The backend restarts/redeploys after environment changes. Do not commit actual values.

## Routing behaviour

- Text analysis: preferred provider first, then the other configured providers.
- Screenshot analysis: Gemini and OpenAI only. Groq is not used for images in this implementation.
- Provider failures fall through to the next configured provider. The response identifies the provider and model used.
- `GET /api/ai/providers` reports configured status without exposing secrets and requires an authenticated session.
- Live trading is not enabled by AI responses. The AI cannot submit or approve an order.

## Privacy and limits

Gemini's free tier may use submitted content to improve Google products. Do not share passwords, API keys, account identifiers, or unredacted personal information in chart screenshots. Free tiers are rate-limited and may change. Automatic fallback does not guarantee uninterrupted service or free usage.

## Verification

After adding keys, sign in and call `GET /api/ai/providers`. Confirm each configured provider is reported as ready. Then test a text question and a redacted chart screenshot. Verify the provider label returned with each result. Test with paper/demo functionality only; no live trade should be placed.
