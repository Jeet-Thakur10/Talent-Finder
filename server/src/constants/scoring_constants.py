from collections.abc import Iterable

SKILL_SYNONYMS: dict[str, tuple[str, ...]] = {
    "python": ("python", "python3"),
    "fastapi": ("fastapi",),
    "django": ("django",),
    "flask": ("flask",),
    "sql": ("sql", "postgresql", "postgres", "mysql", "database"),
    "aws": ("aws", "amazon web services"),
    "docker": ("docker", "containers", "containerization"),
    "kubernetes": ("kubernetes", "k8s"),
    "react": ("react", "reactjs", "react.js"),
    "typescript": ("typescript", "ts"),
    "javascript": ("javascript", "js", "ecmascript"),
    "node.js": ("node", "nodejs", "node.js"),
    "java": ("java", "spring", "spring boot"),
    "c#": ("c#", ".net", "dotnet", "asp.net"),
    "microservices": ("microservices", "distributed systems"),
    "rest apis": ("rest", "rest api", "restful api", "api development"),
    "ci/cd": ("ci/cd", "cicd", "continuous integration"),
    "git": ("git", "github", "gitlab"),
    "machine learning": (
        "machine learning",
        "ml",
        "predictive models",
    ),
    "nlp": ("nlp", "natural language processing"),
}

ROLE_SYNONYMS: dict[str, tuple[str, ...]] = {
    "backend engineer": (
        "backend engineer",
        "backend developer",
        "python developer",
        "software engineer",
        "api engineer",
    ),
    "frontend engineer": (
        "frontend engineer",
        "frontend developer",
        "react developer",
        "ui engineer",
    ),
    "full stack engineer": (
        "full stack engineer",
        "full stack developer",
        "software developer",
    ),
    "data scientist": (
        "data scientist",
        "machine learning engineer",
        "ml engineer",
    ),
    "product designer": (
        "product designer",
        "ux designer",
        "ui/ux designer",
    ),
}

DEGREE_LEVELS: dict[str, int] = {
    "high school": 1,
    "diploma": 2,
    "associate": 3,
    "bachelor": 4,
    "bachelor of technology": 4,
    "bachelor of engineering": 4,
    "btech": 4,
    "b.tech": 4,
    "be": 4,
    "b.e": 4,
    "bs": 4,
    "bsc": 4,
    "master": 5,
    "mba": 5,
    "master of technology": 5,
    "master of science": 5,
    "mtech": 5,
    "m.tech": 5,
    "ms": 5,
    "msc": 5,
    "doctorate": 6,
    "phd": 6,
    "ph.d": 6,
}

DEGREE_LEVEL_ALIASES: dict[str, tuple[str, ...]] = {
    "high school": ("high school",),
    "diploma": ("diploma",),
    "associate": ("associate",),
    "bachelor": (
        "bachelor",
        "bachelor of technology",
        "bachelor of engineering",
        "btech",
        "b.tech",
        "be",
        "b.e",
        "bs",
        "bsc",
    ),
    "master": (
        "master",
        "master of technology",
        "master of science",
        "mtech",
        "m.tech",
        "ms",
        "msc",
    ),
    "mba": ("mba",),
    "doctorate": ("doctorate", "phd", "ph.d"),
}

EDUCATION_SYNONYMS: dict[str, tuple[str, ...]] = {
    "computer science": (
        "computer science",
        "cse",
        "software engineering",
        "information technology",
        "it",
    ),
    "electronics": (
        "electronics",
        "ece",
        "electrical engineering",
    ),
    "business": (
        "business",
        "mba",
        "business administration",
    ),
}

ROLE_DOMAIN_KEYWORDS: dict[str, tuple[str, ...]] = {
    "backend": ("python", "fastapi", "django", "api", "postgres", "sql"),
    "frontend": ("react", "typescript", "javascript", "css", "ui"),
    "data": ("machine learning", "nlp", "analytics", "data"),
    "cloud": ("aws", "docker", "kubernetes", "devops"),
}

EXPERIENCE_SECTION_HEADINGS = {
    "experience",
    "work experience",
    "professional experience",
    "employment history",
}

SKILLS_SECTION_HEADINGS = {
    "skills",
    "technical skills",
    "core skills",
    "core competencies",
}

EDUCATION_SECTION_HEADINGS = {
    "education",
    "academic background",
    "qualifications",
}

SUMMARY_SECTION_HEADINGS = {
    "summary",
    "professional summary",
    "profile",
    "about",
}


def flatten_aliases(values: Iterable[tuple[str, ...]]) -> tuple[str, ...]:
    flattened: list[str] = []

    for aliases in values:
        flattened.extend(aliases)

    return tuple(flattened)
