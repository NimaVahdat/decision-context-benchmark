from bench.scenarios.models import SeedTrace

_SPACER_COS = [
    "notion.so",
    "retool.com",
    "finstack.io",
    "cloudlane.dev",
    "datavault.io",
    "shopfront.co",
    "meridian.bio",
    "learnnext.ai",
    "resend.com",
    "notion.so",
    "retool.com",
    "finstack.io",
    "cloudlane.dev",
    "datavault.io",
    "shopfront.co",
    "meridian.bio",
    "learnnext.ai",
    "resend.com",
    "notion.so",
    "retool.com",
]

_SUPPORT_SPACER_ISSUES = [
    "api timeout",
    "login failure",
    "sync error",
    "export issue",
    "billing question",
    "access denied",
    "slow performance",
    "data missing",
    "integration error",
    "password reset",
    "report failure",
    "webhook not firing",
    "dashboard error",
    "csv import failed",
    "notification issue",
]


def spacer(company: str) -> SeedTrace:
    return SeedTrace(
        skill="eval-analyst",
        company=company,
        message_content=f"Analyze {company}",
        parent_index=None,
    )


def support_spacer(company: str, issue_index: int = 0) -> SeedTrace:
    issue = _SUPPORT_SPACER_ISSUES[issue_index % len(_SUPPORT_SPACER_ISSUES)]
    return SeedTrace(
        skill="eval-support",
        company=company,
        message_content=f"Handle support ticket for {company}: {issue}",
        parent_index=None,
    )
