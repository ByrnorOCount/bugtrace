from __future__ import annotations

from itertools import cycle


MOCK_CASES = [
    {
        "title": "Checkout fails after payment token refresh",
        "description": "Customers see a retry loop after their saved card token refreshes during checkout.",
        "stack_trace": "PaymentTokenExpired: token refresh completed after checkout session lock\n  at CheckoutService.authorize\n  at PaymentGatewayClient.charge",
        "severity": "high",
        "environment": "production-us-east",
        "test_name": "test_checkout_retries_token_refresh",
        "suite": "payments.checkout",
        "failure_signature": "PaymentTokenExpired during CheckoutService.authorize",
        "root_cause": "The checkout session reads an expired payment token before the refresh transaction commits.",
        "fix_hint": "Reload the payment credential after refresh and make checkout authorization wait for the token version.",
        "category": "payments",
    },
    {
        "title": "Login returns 500 for uppercase emails",
        "description": "Enterprise users cannot sign in when their identity provider sends uppercase email addresses.",
        "stack_trace": "IntegrityError: duplicate key value violates unique constraint users_email_key\n  at AuthRepository.upsert_user",
        "severity": "medium",
        "environment": "staging",
        "test_name": "test_sso_login_normalizes_email",
        "suite": "identity.sso",
        "failure_signature": "IntegrityError users_email_key in AuthRepository.upsert_user",
        "root_cause": "The SSO callback normalizes lookup emails but persists the original mixed-case address.",
        "fix_hint": "Normalize email before lookup and persistence, then add a migration for existing mixed-case records.",
        "category": "authentication",
    },
    {
        "title": "Dashboard chart times out on custom date range",
        "description": "Large customers report that the analytics dashboard spins forever for a 90 day range.",
        "stack_trace": "QueryTimeoutError: statement timeout\n  at AnalyticsRepository.fetchSeries\n  at UsageDashboard.render",
        "severity": "medium",
        "environment": "production-eu",
        "test_name": "test_usage_dashboard_date_range_uses_rollups",
        "suite": "analytics.dashboard",
        "failure_signature": "QueryTimeoutError in AnalyticsRepository.fetchSeries",
        "root_cause": "The dashboard falls back to raw event scans instead of using daily rollup tables for long ranges.",
        "fix_hint": "Route ranges over 31 days to the rollup query path and add an index on tenant_id/report_day.",
        "category": "analytics",
    },
    {
        "title": "CSV export drops rows containing emoji",
        "description": "Support exports are missing rows when ticket comments include multi-byte characters.",
        "stack_trace": "UnicodeEncodeError: 'latin-1' codec can't encode character\n  at CsvExportWriter.write_row",
        "severity": "low",
        "environment": "production",
        "test_name": "test_csv_export_writes_utf8",
        "suite": "support.exports",
        "failure_signature": "UnicodeEncodeError in CsvExportWriter.write_row",
        "root_cause": "The export writer uses a latin-1 default encoding inherited from the host environment.",
        "fix_hint": "Open export streams with explicit UTF-8 encoding and add coverage for multi-byte comment text.",
        "category": "exports",
    },
    {
        "title": "Webhook retries never stop after 410 response",
        "description": "Partner endpoints returning Gone continue receiving retries every few minutes.",
        "stack_trace": "RetryPolicyExceeded: terminal status not recognized\n  at WebhookDispatcher.scheduleRetry",
        "severity": "high",
        "environment": "production",
        "test_name": "test_webhook_410_disables_subscription",
        "suite": "integrations.webhooks",
        "failure_signature": "RetryPolicyExceeded terminal status not recognized",
        "root_cause": "HTTP 410 is not classified as a terminal subscription state in the retry policy.",
        "fix_hint": "Treat 410 as terminal, disable the subscription, and emit an audit event for the partner.",
        "category": "integrations",
    },
]


def synthetic_cases(count: int) -> list[dict[str, str]]:
    cases = []
    for index, base in zip(range(count), cycle(MOCK_CASES), strict=False):
        clone = dict(base)
        clone["title"] = f"{base['title']} #{index + 1}"
        clone["test_name"] = f"{base['test_name']}_{index + 1}"
        cases.append(clone)
    return cases


def mock_analysis(title: str, matches: list[dict]) -> dict:
    best = matches[0]["failure"] if matches else None
    category = best["category"] if best else "unknown"
    return {
        "category": category,
        "root_cause": best["root_cause"] if best else f"{title} needs manual triage.",
        "suggested_fix": best["fix_hint"] if best else "Collect logs, reproduce locally, and compare against recent deployments.",
        "confidence": 0.78 if best else 0.42,
        "status": "mock-analysis",
        "used_fallback": True,
        "reasoning_notes": [
            "Generated by deterministic fallback.",
            "The recommendation is based on the closest stored failure pattern.",
        ],
    }
