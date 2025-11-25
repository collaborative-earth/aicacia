from ragas.testset.persona import Persona

# Define commonly used Personas in ecological restoration projects

researcher = Persona(
    name="Ecological Researcher",
    role_description=(
        """
        Investigates ecological processes, biodiversity drivers, and landscape-level interactions.
        Often questions data quality, scale effects, statistical validity, and model assumptions.
        Scientific terminolgy, high domain knowledge, methodological and experimental intent.
        """
    )
)

manager = Persona(
    name="Ecological Restoration Manager",
    role_description=(
        """
        Oversees planning, budgeting, and coordination of restoration projects. 
        Speaks in medium-length, slightly complex sentences focusing on trade-offs, 
        predictability, site prioritization, and resource allocation. 
        Uses practical terminology (e.g., 'project design', 'survival outcomes', 
        'site conditions', 'constraints', 'reliable recovery') and frames questions 
        around decision-making rather than mechanisms.
        """
    )
)

policy_maker = Persona(
    name="Environmental Policy Maker",
    role_description=(
        "Develops policies, guidelines, and regulations to support sustainable ecosystem restoration "
        "and biodiversity conservation at local, regional, or national scales."
    )
)

volunteer = Persona(
    name="Community Restoration Volunteer",
    role_description=(
        """
        Participates in hands-on restoration events. Uses informal, simple vocabulary 
        and short questions. Focuses on doing things correctly in the field (planting, 
        watering, basic maintenance). Avoids technical terms and instead asks about 
        visible signs, practical steps, or common mistakes.
        """
    )
)

technician = Persona(
    name="Quantitative Restoration Technician",
    role_description=(
        """
        Oversees planning and coordination of restoration projects. Speaks in moderately 
        complex sentences and frames questions around timelines, predictability, 
        trade-offs, and project-level decisions (where, when, how to allocate effort). 
        Avoids technical measurements but uses management-oriented terms like 
        'planning', 'expected outcomes', 'site conditions', and 'resource constraints'.
        """
    )
)