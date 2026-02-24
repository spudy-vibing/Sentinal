"""
SENTINEL V2 — Chat Router
Handles Claude-powered conversational interface.
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from config import get_settings

router = APIRouter()
settings = get_settings()


class ChatMessage(BaseModel):
    """A single chat message."""
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    """Chat request with history."""
    message: str
    history: List[ChatMessage] = []
    portfolio_id: Optional[str] = "portfolio_a"
    include_context: bool = True


class ChatResponse(BaseModel):
    """Chat response."""
    response: str
    context_used: List[str] = []


# System prompt for Sentinel chat
SENTINEL_SYSTEM_PROMPT = """You are Sentinel, an AI assistant for UHNW (Ultra High Net Worth) portfolio management.

You help financial advisors understand portfolio risks, tax implications, and investment recommendations.

Your personality:
- Professional but approachable
- Data-driven and precise
- Proactive about risks and opportunities
- Clear in explanations, avoiding unnecessary jargon

When answering questions:
1. Reference specific data from the portfolio when available
2. Explain tax implications clearly
3. Highlight concentration risks
4. Suggest actionable next steps
5. Be concise but thorough

Current portfolio context will be provided. Use it to give specific, relevant answers."""


@router.post("/message", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    """
    Send a message and get a response from Sentinel.
    """
    try:
        import anthropic

        if not settings.anthropic_api_key:
            # Return mock response if no API key
            return ChatResponse(
                response=get_mock_response(request.message),
                context_used=["portfolio_data", "recent_analysis"]
            )

        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

        # Build context
        context = ""
        context_used = []

        if request.include_context:
            try:
                from src.data import load_portfolio
                portfolio = load_portfolio(request.portfolio_id)
                context = f"""
Current Portfolio: {portfolio.name}
AUM: ${portfolio.aum_usd:,.0f}
Risk Tolerance: {portfolio.client_profile.risk_tolerance.value}
Tax Sensitivity: {portfolio.client_profile.tax_sensitivity:.0%}
Concentration Limit: {portfolio.client_profile.concentration_limit:.0%}

Holdings:
"""
                for h in portfolio.holdings:
                    flag = " ⚠️" if h.portfolio_weight > portfolio.client_profile.concentration_limit else ""
                    context += f"- {h.ticker}: {h.portfolio_weight:.1%} (${h.market_value:,.0f}){flag}\n"

                context_used.append("portfolio_data")
            except Exception:
                pass

        # Build messages
        messages = []
        for msg in request.history[-10:]:  # Last 10 messages for context
            messages.append({
                "role": msg.role,
                "content": msg.content
            })

        # Add current message with context
        user_content = request.message
        if context:
            user_content = f"{context}\n\nUser question: {request.message}"

        messages.append({
            "role": "user",
            "content": user_content
        })

        # Call Claude
        response = client.messages.create(
            model=settings.default_model,
            max_tokens=1024,
            system=SENTINEL_SYSTEM_PROMPT,
            messages=messages
        )

        return ChatResponse(
            response=response.content[0].text,
            context_used=context_used
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def stream_message(request: ChatRequest, req: Request):
    """
    Stream a response from Sentinel (for real-time typing effect).
    """
    try:
        import anthropic

        if not settings.anthropic_api_key:
            # Return mock streaming
            async def mock_generator():
                response = get_mock_response(request.message)
                for word in response.split():
                    yield f"data: {json.dumps({'text': word + ' '})}\n\n"
                yield f"data: {json.dumps({'done': True})}\n\n"

            return StreamingResponse(
                mock_generator(),
                media_type="text/event-stream"
            )

        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

        # Build context
        context = ""
        if request.include_context:
            try:
                from src.data import load_portfolio
                portfolio = load_portfolio(request.portfolio_id)
                context = f"Portfolio: {portfolio.name}, AUM: ${portfolio.aum_usd:,.0f}\n"
            except Exception:
                pass

        messages = [{"role": "user", "content": f"{context}\n{request.message}"}]

        async def generate():
            with client.messages.stream(
                model=settings.default_model,
                max_tokens=1024,
                system=SENTINEL_SYSTEM_PROMPT,
                messages=messages
            ) as stream:
                for text in stream.text_stream:
                    yield f"data: {json.dumps({'text': text})}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/suggestions")
async def get_suggestions(portfolio_id: Optional[str] = "portfolio_a"):
    """Get suggested questions based on current portfolio state."""
    return {
        "suggestions": [
            {
                "text": "Why is NVDA flagged as a concentration risk?",
                "category": "risk"
            },
            {
                "text": "Explain the wash sale conflict",
                "category": "tax"
            },
            {
                "text": "What are my tax-loss harvesting opportunities?",
                "category": "tax"
            },
            {
                "text": "Compare the top two scenarios for me",
                "category": "scenarios"
            },
            {
                "text": "Explain this recommendation to a client",
                "category": "communication"
            },
            {
                "text": "What happens if tech drops another 5%?",
                "category": "risk"
            },
        ]
    }


def get_mock_response(message: str) -> str:
    """Return a mock response when API key is not available."""
    message_lower = message.lower()

    if "nvda" in message_lower and ("flag" in message_lower or "risk" in message_lower):
        return """NVDA is flagged because it currently represents 17% of the portfolio, which exceeds your concentration limit of 15%.

**Key Points:**
- Current weight: 17% ($8.5M)
- Limit: 15%
- Excess: 2% (~$1M)

This concentration creates single-stock risk. If NVDA drops 20%, the portfolio loses 3.4% from that position alone.

**Recommendation:** Consider reducing the position by ~$1M to bring it within limits. However, note the wash sale window from the recent NVDA sale 15 days ago."""

    elif "wash sale" in message_lower:
        return """A wash sale conflict exists because:

1. **Recent Sale:** You sold NVDA shares 15 days ago
2. **Window:** The IRS wash sale rule covers 30 days before AND after a sale
3. **Impact:** If you sell more NVDA now, you can't claim the loss from the Feb 6 sale ($25,000)

**Resolution Options:**
- Wait 16 more days for the window to close
- Use AMD as a correlated substitute (not "substantially identical")
- Accept the wash sale if the concentration risk outweighs the tax benefit"""

    elif "tax" in message_lower and ("harvest" in message_lower or "opportunit" in message_lower):
        return """I found 2 tax-loss harvesting opportunities in your portfolio:

1. **AMD** - $750,000 unrealized loss
   - Could offset gains elsewhere
   - No wash sale concerns
   - Action: Sell and replace with similar tech exposure

2. **BND** - $300,000 unrealized loss
   - Fixed income position
   - Could replace with similar duration bond ETF
   - Action: Harvest and replace with AGG or SCHZ

**Total potential tax benefit:** ~$262,500 (at 25% rate)

Want me to generate a specific trade plan?"""

    else:
        return """I can help you understand your portfolio risks, tax implications, and recommendations.

Try asking me:
- "Why is NVDA flagged?"
- "Explain the wash sale conflict"
- "What are my tax opportunities?"
- "Compare the recommended scenarios"

I have full context on your portfolio and the latest analysis."""
