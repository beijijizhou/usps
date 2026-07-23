import streamlit as st


SECTION_ALIASES = {
    "factory_credentials": [
        "factory_credentials",
        "factoryCredentials",
        "factorycredentials",
        "Factorycredentials",
        "FactoryCredentials",
    ],
    "qa_credentials": [
        "qa_credentials",
        "qaCredentials",
        "qacredentials",
        "Qacredentials",
        "QaCredentials",
    ],
}


def normalize_key(value):
    return str(value or "").replace(" ", "").strip().lower()


def get_selected_platform(default="3D热转印"):
    return str(st.session_state.get("selected_platform", default)).strip()


def get_secret_section(section_name):
    for alias in SECTION_ALIASES.get(section_name, [section_name]):
        if alias in st.secrets:
            return st.secrets[alias], alias
    return None, None


def get_platform_credentials(section_name, platform_name=None):
    platform = str(platform_name or get_selected_platform()).strip()
    section, matched_section_name = get_secret_section(section_name)
    if section is None:
        aliases = ", ".join(SECTION_ALIASES.get(section_name, [section_name]))
        return None, f"找不到配置区块：{section_name}。已尝试：{aliases}"

    if platform in section:
        return section[platform], None

    normalized_platform = normalize_key(platform)
    available_platforms = list(section.keys())
    for available_platform in available_platforms:
        if normalize_key(available_platform) == normalized_platform:
            return section[available_platform], None

    return None, (
        f"{matched_section_name} 中找不到平台：{platform}。"
        f"当前可用平台：{', '.join(map(str, available_platforms)) or '无'}"
    )
