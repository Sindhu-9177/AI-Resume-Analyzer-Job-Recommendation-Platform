import re

def extract_skills(text):

    skills_list = [
        "python", "java", "javascript", "react",
        "flask", "django", "mysql", "sql",
        "html", "css"
    ]

    text = text.lower()

    found = []

    for skill in skills_list:
        if re.search(r"\b" + skill + r"\b", text):
            found.append(skill)

    return found