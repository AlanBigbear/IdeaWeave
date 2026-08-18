from abc import ABC, abstractmethod


class CommentProvider(ABC):
    """Demo-stage comment source. Real Bilibili crawl can implement this later."""

    @abstractmethod
    def fetch(self, extra_text: str = "") -> list[str]:
        raise NotImplementedError


MOCK_COMMENTS = [
    "求完整路线和票价，别只拍好看的部分。",
    "开头 10 秒不知道在讲什么，建议直接抛冲突。",
    "想看真实排队和踩坑，不要只有精修镜头。",
    "适合周末两个人去吗？预算大概多少？",
    "封面信息太满，标题党了但内容还行。",
    "弹幕都在问合作品牌，希望说清楚是不是广告。",
    "后半段节奏掉了，体验过程可以再拆细一点。",
    "如果有「值不值得去」的结论会更好。",
]


class MockCommentProvider(CommentProvider):
    def fetch(self, extra_text: str = "") -> list[str]:
        pasted = [line.strip() for line in extra_text.splitlines() if line.strip()]
        return MOCK_COMMENTS + pasted


class PasteCommentProvider(CommentProvider):
    def fetch(self, extra_text: str = "") -> list[str]:
        return [line.strip() for line in extra_text.splitlines() if line.strip()]


def resolve_comments(use_mock: bool, extra_text: str) -> tuple[str, list[str]]:
    provider: CommentProvider = MockCommentProvider() if use_mock else PasteCommentProvider()
    comments = provider.fetch(extra_text)
    source = "mock+paste" if use_mock else "paste"
    return source, comments
