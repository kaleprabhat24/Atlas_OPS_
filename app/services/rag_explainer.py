"""
RAG Explainer Service for ATLAS-OPS.

Takes SHAP feature contributions + gateway error logs and uses a LangChain
LLM chain to generate a human-readable failure explanation for the merchant.

Falls back to a template-based explanation if OPENAI_API_KEY is not configured.
"""
from typing import Any

from app.core.config import get_settings
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)


# ── Template fallback (used when no API key is configured) ───────────────────
_FALLBACK_TEMPLATE = """
Payment Failure Analysis
========================
Transaction failed via **{gateway}** with HTTP {http_status}.

**Top Contributing Factors:**
{top_factors}

**Error Context:**
- Latency: {latency_ms}ms
- Retry Attempts: {retries}
- Timeout: {timeout}
- Connection Drop: {conn_drop}
- DNS Failure: {dns_fail}

**Recommendation:** {recommendation}
""".strip()

_RECOMMENDATIONS = {
    "timeout": "The gateway timed out. Consider retrying with exponential back-off or switching to an alternative gateway.",
    "connection_drop": "The connection was dropped mid-flight. This may indicate a network instability issue. Retry or switch to a backup gateway.",
    "dns_failure": "DNS resolution failed for the gateway endpoint. Contact your infrastructure team to verify DNS configuration.",
    "high_latency": "Gateway response times are elevated. Consider routing to a lower-latency gateway.",
    "generic": "The payment could not be processed. Please retry. If the issue persists, contact support.",
}


def _build_template_explanation(
    shap_values: dict[str, float],
    gateway_error: dict[str, Any],
    gateway: str,
) -> str:
    """Generate a template-based explanation without an LLM."""
    top = sorted(shap_values.items(), key=lambda x: abs(x[1]), reverse=True)[:3]
    top_factors_str = "\n".join(
        f"  - **{f}**: SHAP = {v:+.4f}" for f, v in top
    )

    # Determine best recommendation
    rec_key = "generic"
    if gateway_error.get("timeout_flag"):
        rec_key = "timeout"
    elif gateway_error.get("connection_drop_flag"):
        rec_key = "connection_drop"
    elif gateway_error.get("dns_failure_flag"):
        rec_key = "dns_failure"
    elif gateway_error.get("gateway_latency_ms", 0) > 2000:
        rec_key = "high_latency"

    return _FALLBACK_TEMPLATE.format(
        gateway=gateway.upper(),
        http_status=gateway_error.get("http_status_code", "N/A"),
        top_factors=top_factors_str,
        latency_ms=gateway_error.get("gateway_latency_ms", 0),
        retries=gateway_error.get("retry_attempts", 0),
        timeout="Yes" if gateway_error.get("timeout_flag") else "No",
        conn_drop="Yes" if gateway_error.get("connection_drop_flag") else "No",
        dns_fail="Yes" if gateway_error.get("dns_failure_flag") else "No",
        recommendation=_RECOMMENDATIONS[rec_key],
    )


async def _build_llm_explanation(
    shap_values: dict[str, float],
    gateway_error: dict[str, Any],
    gateway: str,
    transaction_id: str,
) -> str:
    """Call OpenAI via LangChain to produce a merchant-friendly explanation."""
    try:
        from langchain_openai import ChatOpenAI
        from langchain.schema import HumanMessage, SystemMessage

        # Format SHAP context
        top = sorted(shap_values.items(), key=lambda x: abs(x[1]), reverse=True)[:5]
        shap_context = "\n".join(
            f"  - {f}: {v:+.4f}" for f, v in top
        )

        system_prompt = (
            "You are an expert payment operations analyst. "
            "Your job is to explain payment failures to merchants in clear, "
            "non-technical language. Be concise (≤3 paragraphs), actionable, "
            "and empathetic. Always end with a concrete recommendation."
        )

        user_prompt = f"""
A payment transaction (ID: {transaction_id}) failed via the {gateway.upper()} gateway.

Gateway Error Context:
- HTTP Status: {gateway_error.get('http_status_code', 'N/A')}
- Latency: {gateway_error.get('gateway_latency_ms', 0)}ms
- Retry Attempts: {gateway_error.get('retry_attempts', 0)}
- Timeout: {gateway_error.get('timeout_flag', False)}
- Connection Drop: {gateway_error.get('connection_drop_flag', False)}
- DNS Failure: {gateway_error.get('dns_failure_flag', False)}

Top ML Feature Contributions (SHAP values — positive = increases failure risk):
{shap_context}

Please write a clear explanation for the merchant explaining why this payment failed
and what they should do next.
""".strip()

        llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0.3,
            max_tokens=400,
        )

        messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
        response = await llm.ainvoke(messages)
        return response.content

    except Exception as exc:
        logger.warning("rag_llm_failed", error=str(exc), fallback="template")
        return _build_template_explanation(shap_values, gateway_error, gateway)


class RAGExplainerService:

    @staticmethod
    async def explain(
        transaction_id: str,
        shap_values: dict[str, float],
        gateway_error: dict[str, Any],
        gateway: str = "unknown",
    ) -> str:
        """
        Generate a human-readable failure explanation.

        Uses LLM if OPENAI_API_KEY is configured, falls back to template.

        Returns:
            explanation_text (str)
        """
        if settings.openai_api_key and settings.openai_api_key.startswith("sk-"):
            explanation = await _build_llm_explanation(
                shap_values, gateway_error, gateway, transaction_id
            )
        else:
            logger.info("rag_using_template_fallback", reason="no_api_key")
            explanation = _build_template_explanation(shap_values, gateway_error, gateway)

        logger.info(
            "rag_explanation_generated",
            transaction_id=transaction_id,
            gateway=gateway,
            chars=len(explanation),
        )
        return explanation
