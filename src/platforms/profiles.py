from dataclasses import dataclass, field


@dataclass
class PlatformProfile:
    """Platform-specific content characteristics."""
    name: str
    display_name: str
    max_length: int
    style_keywords: list[str] = field(default_factory=list)
    structure_hints: list[str] = field(default_factory=list)
    tone: str = ""


PROFILES: dict[str, PlatformProfile] = {
    "xiaohongshu": PlatformProfile(
        name="xiaohongshu",
        display_name="小红书",
        max_length=1000,
        style_keywords=["种草", "分享", "安利", "绝绝子", "姐妹们"],
        structure_hints=["emoji节奏", "分段标题", "图文搭配提示"],
        tone="轻松活泼、闺蜜感",
    ),
    "wechat": PlatformProfile(
        name="wechat",
        display_name="微信公众号",
        max_length=5000,
        style_keywords=["深度", "洞察", "思考", "分析"],
        structure_hints=["深度观点", "结构化论证", "金句收尾"],
        tone="专业深度、有观点",
    ),
    "douyin": PlatformProfile(
        name="douyin",
        display_name="抖音",
        max_length=500,
        style_keywords=["爆款", "震惊", "没想到", "家人们"],
        structure_hints=["前3秒hook", "口语化", "节奏感强"],
        tone="口语化、节奏快、有冲击力",
    ),
}


def get_profile(platform: str) -> PlatformProfile:
    """Get platform profile by name."""
    if platform not in PROFILES:
        raise ValueError(f"Unknown platform: {platform}. Available: {list(PROFILES.keys())}")
    return PROFILES[platform]


def list_platforms() -> list[str]:
    """Return all available platform names."""
    return list(PROFILES.keys())
