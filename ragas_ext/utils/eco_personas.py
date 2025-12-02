from ragas.testset.persona import Persona

# Define commonly used Personas in ecological restoration projects

researcher = Persona(
    name="Ecological Researcher",
    role_description=(
        "Asks academic, mechanism-driven questions; evidence-focused, hypothesis-oriented, analytical."
    )
)

manager = Persona(
    name="Ecological Restoration Manager",
    role_description=(
        "Asks planning and prioritization questions; medium complexity, considers trade-offs and scale."
    )
)

policy_maker = Persona(
    name="Environmental Policy Maker",
    role_description=(
        "Develops policies, guidelines, and regulations to support sustainable ecosystem restoration and biodiversity conservation at local, regional, or national scales."
    )
)

volunteer = Persona(
    name="Community Restoration Volunteer",
    role_description=(
        "Asks simple, practical, observable questions about restoration outcomes; conversational, no technical specific terms."
    )
)

technician = Persona(
    name="Quantitative Restoration Technician",
    role_description=(
        "Asks precise, measurement-focused questions; includes quantitative terms, thresholds, and protocols."
    )
)