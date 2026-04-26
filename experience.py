import re


def extract_experience(text):
    """
    Scans resume text for mentions of years of experience.
    Returns the highest number found (most relevant signal).
    """
    matches = re.findall(r"(\d+)\s*\+?\s*(years?|yrs?)[\s\w]{0,20}experience", text.lower())
    if matches:
        return max(int(m[0]) for m in matches)

    # Fallback: any standalone year mention
    fallback = re.findall(r"(\d+)\s*(years?|yrs?)", text.lower())
    if fallback:
        return max(int(m[0]) for m in fallback)

    return 0