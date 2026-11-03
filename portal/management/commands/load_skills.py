from django.core.management.base import BaseCommand

from portal.models import Skill

SKILLS = [
    ("Python", "Programming", "python3, py",
     "A programming language used for web development, data analysis and automation"),
    ("JavaScript", "Programming", "js, ecmascript",
     "A programming language that makes web pages interactive"),
    ("HTML and CSS", "Programming", "html, css, html5, css3",
     "The languages used to structure and style web pages"),
    ("Django", "Programming", "django framework",
     "A Python framework for building web applications"),
    ("SQL", "Database", "postgresql, mysql, sql server",
     "A language for storing, querying and managing data in databases"),
    ("Git", "Tools", "github, version control",
     "A tool for tracking changes in code and working in teams"),
    ("Data Analysis", "Analytics", "data analytics, analysis",
     "Cleaning and studying data to find patterns and answers"),
    ("Machine Learning", "Analytics", "ml, ai, artificial intelligence",
     "Building models that learn patterns from data"),
    ("Microsoft Excel", "Tools", "excel, spreadsheets",
     "Using spreadsheets to organise, calculate and present data"),
    ("Cloud Computing", "Infrastructure", "aws, azure, cloud",
     "Running applications and storing data on remote servers"),
    ("Networking", "Infrastructure", "computer networks, tcp/ip",
     "Setting up and maintaining connections between computers"),
    ("Cybersecurity", "Infrastructure", "information security, infosec",
     "Protecting systems and data from attacks"),
    ("UI/UX Design", "Design", "ui design, ux design, figma",
     "Designing interfaces that are easy and pleasant to use"),
    ("Digital Marketing", "Business", "seo, social media marketing",
     "Promoting products and services online"),
    ("Accounting", "Business", "bookkeeping, financial reporting",
     "Recording and reporting financial information"),
    ("Project Management", "Business", "agile, scrum, project planning",
     "Planning and delivering projects on time and within budget"),
    ("Customer Service", "Soft skill", "customer support, client care",
     "Helping customers and solving their problems"),
    ("Communication", "Soft skill", "verbal communication, presentation",
     "Sharing information clearly in speech and writing"),
    ("Teamwork", "Soft skill", "collaboration, team player",
     "Working well with others towards a shared goal"),
    ("Problem Solving", "Soft skill", "critical thinking, troubleshooting",
     "Finding practical solutions to difficult situations"),
]


class Command(BaseCommand):
    help = "Load the starter skill library into the database"

    def handle(self, *args, **options):
        created_count = 0
        updated_count = 0
        for name, category, aliases, definition in SKILLS:
            _, created = Skill.objects.update_or_create(
                name=name,
                defaults={
                    "category": category,
                    "aliases": aliases,
                    "definition": definition,
                },
            )
            if created:
                created_count += 1
            else:
                updated_count += 1
        self.stdout.write(
            self.style.SUCCESS(
                f"Skills loaded: {created_count} new, {updated_count} updated."
            )
        )