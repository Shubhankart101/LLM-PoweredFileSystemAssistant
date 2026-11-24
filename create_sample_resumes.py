"""
create_sample_resumes.py - Generates 8 diverse dummy resumes across PDF, DOCX, and TXT.

Creates the 'resumes/' directory and populates it with realistic candidate resumes:
- PDF: resume_john_doe.pdf, resume_alice_smith.pdf, resume_michael_brown.pdf
- DOCX: resume_bob_kumar.docx, resume_emily_chen.docx, resume_priya_sharma.docx
- TXT: resume_david_wilson.txt, resume_sarah_connor.txt
"""

from pathlib import Path

import docx
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

RESUMES_DIR = Path(__file__).resolve().parent / "resumes"
RESUMES_DIR.mkdir(parents=True, exist_ok=True)


RESUME_DATA = [
    {
        "filename": "resume_john_doe.pdf",
        "format": "pdf",
        "name": "John Doe",
        "title": "Senior Python Backend Engineer",
        "email": "john.doe@example.com | Phone: +1-555-0101 | Location: San Francisco, CA",
        "summary": (
            "Senior Backend Engineer with 7+ years of expertise in architecting scalable distributed systems "
            "using Python, FastAPI, and Django. Proven track record of reducing API latency by 45% and "
            "designing resilient microservices on AWS and Kubernetes."
        ),
        "skills": [
            "Programming Languages: Python (Advanced), SQL, Bash, Go",
            "Frameworks: FastAPI, Django, Flask, Celery, SQLAlchemy",
            "Databases & Caching: PostgreSQL, Redis, Elasticsearch",
            "Cloud & DevOps: AWS (EC2, ECS, S3, RDS), Docker, Kubernetes, GitHub Actions",
            "Architecture: Microservices, Event-Driven Architecture, RESTful APIs, gRPC",
        ],
        "experience": [
            "Senior Python Engineer | TechCorp Inc. (2021 - Present)\n"
            "- Led backend development of an enterprise SaaS platform "
            "processing 5M+ daily requests using Python and FastAPI.\n"
            "- Designed asynchronous task queue using Celery and Redis to handle batch data exports in background.\n"
            "- Spearheaded database migration from MySQL to PostgreSQL, optimizing complex indexing.",
            "Backend Developer | CloudScale Solutions (2018 - 2021)\n"
            "- Developed RESTful web services in Python and Django for an e-commerce order management system.\n"
            "- Implemented CI/CD pipelines using GitHub Actions and containerized microservices with Docker.",
        ],
        "education": "B.S. in Computer Science | University of California, Berkeley (2014 - 2018)",
    },
    {
        "filename": "resume_alice_smith.pdf",
        "format": "pdf",
        "name": "Alice Smith",
        "title": "Lead Data Scientist & ML Engineer",
        "email": "alice.smith@example.com | Phone: +1-555-0102 | Location: New York, NY",
        "summary": (
            "Lead Data Scientist with 6 years of experience building predictive models, NLP pipelines, "
            "and deep learning systems in Python. Passionate about turning complex datasets into high-impact "
            "business decisions and deploying production machine learning models."
        ),
        "skills": [
            "Programming: Python, R, SQL, C++",
            "Data Science & ML: PyTorch, TensorFlow, Scikit-Learn, Pandas, NumPy, SciPy",
            "NLP & Generative AI: HuggingFace Transformers, LangChain, OpenAI APIs, Vector Databases",
            "Big Data & MLOps: Apache Spark, MLflow, Docker, AWS SageMaker",
            "Visualization: Matplotlib, Seaborn, Tableau",
        ],
        "experience": [
            "Lead Data Scientist | FinAI Global (2021 - Present)\n"
            "- Designed fraud detection deep learning architecture in Python using PyTorch, saving $2.3M annually.\n"
            "- Mentored junior data scientists and established standardized Python ML development practices.\n"
            "- Integrated real-time inference endpoints on AWS SageMaker with sub-50ms latency.",
            "Data Scientist | Insight Analytics (2019 - 2021)\n"
            "- Engineered automated customer churn prediction pipelines using Python and Scikit-Learn.\n"
            "- Built interactive dashboards and ETL scripts processing 10TB+ telemetry data weekly.",
        ],
        "education": "M.S. in Data Science | Columbia University (2017 - 2019)",
    },
    {
        "filename": "resume_michael_brown.pdf",
        "format": "pdf",
        "name": "Michael Brown",
        "title": "AI Research & Systems Engineer",
        "email": "michael.brown@example.com | Phone: +1-555-0103 | Location: Seattle, WA",
        "summary": (
            "AI Engineer specializing in Large Language Models (LLMs), agentic workflows, and semantic retrieval. "
            "Hands-on experience implementing autonomous tool-calling systems and RAG pipelines with Python."
        ),
        "skills": [
            "Core: Python, PyTorch, C++, CUDA",
            "AI/LLM: LangChain, LangGraph, LlamaIndex, OpenAI Function Calling, HuggingFace",
            "Vector Stores: ChromaDB, Pinecone, FAISS, Qdrant",
            "Infrastructure: Docker, Ray, Kubernetes, Linux",
        ],
        "experience": [
            "AI Systems Engineer | NeuralStack (2022 - Present)\n"
            "- Built multi-agent autonomous coding assistants with structured Python tool execution.\n"
            "- Fine-tuned open-source LLMs (Llama-3, Mistral) on domain-specific enterprise datasets.",
            "Research Assistant | AI Institute (2020 - 2022)\n"
            "- Published peer-reviewed research on agent reasoning and retrieval augmented generation.\n"
            "- Benchmarked prompt caching and token optimization strategies across production LLM endpoints.",
        ],
        "education": "B.S. & M.S. in Computer Science | University of Washington (2016 - 2021)",
    },
    {
        "filename": "resume_bob_kumar.docx",
        "format": "docx",
        "name": "Bob Kumar",
        "title": "Full Stack Software Engineer",
        "email": "bob.kumar@example.com | Phone: +1-555-0104 | Location: Austin, TX",
        "summary": (
            "Versatile Full Stack Engineer with 5 years building modern responsive web apps and scalable backends. "
            "Proficient in React, TypeScript, Node.js, and Python backend services."
        ),
        "skills": [
            "Frontend: React, Next.js, TypeScript, Tailwind CSS, Redux Toolkit",
            "Backend: Node.js, Express, Python (FastAPI, Flask)",
            "Databases: MongoDB, PostgreSQL, Redis",
            "Tools: Git, Docker, Jest, Cypress, Vercel, AWS",
        ],
        "experience": [
            "Full Stack Developer | GrowthWave (2021 - Present)\n"
            "- Developed user-facing interactive dashboards using React and Next.js.\n"
            "- Created Python microservices to handle high-throughput analytical data aggregation.\n"
            "- Improved core web vitals and client rendering times by 35%.",
            "Software Developer | AgileSphere (2019 - 2021)\n"
            "- Built customer portal using Node.js, Express, and MongoDB.\n"
            "- Collaborated with cross-functional product teams to deliver 12 major feature sprints on time.",
        ],
        "education": "B.Tech in Information Technology | National Institute of Technology (2015 - 2019)",
    },
    {
        "filename": "resume_emily_chen.docx",
        "format": "docx",
        "name": "Emily Chen",
        "title": "Senior Technical Product Manager",
        "email": "emily.chen@example.com | Phone: +1-555-0105 | Location: Chicago, IL",
        "summary": (
            "Strategic Product Manager with 8+ years leading B2B enterprise software products from conception "
            "to scale. Expertise in customer discovery, roadmapping, agile methodologies, and data-driven prioritization."
        ),
        "skills": [
            "Product Management: Product Strategy, Roadmap Planning, User Story Mapping, OKRs",
            "Methodologies: Agile, Scrum, Kanban, Design Thinking",
            "Analytics & Tools: SQL, Jira, Confluence, Amplitude, Mixpanel, Figma",
            "Leadership: Stakeholder Management, Cross-functional alignment, Vendor negotiations",
        ],
        "experience": [
            "Senior Technical Product Manager | EnterpriseCloud (2020 - Present)\n"
            "- Managed enterprise collaboration platform with $18M ARR, increasing retention by 14%.\n"
            "- Directed roadmap across 3 distributed engineering squads comprising 24 engineers and designers.\n"
            "- Ran continuous user research interviews and synthesized data to drive quarterly priorities.",
            "Product Manager | AppVantage (2017 - 2020)\n"
            "- Launched mobile B2B workflow app resulting in 100K+ monthly active users within 6 months.\n"
            "- Authored PRDs, defined success metrics, and coordinated launch go-to-market strategies.",
        ],
        "education": "B.A. in Economics & Cognitive Science | Northwestern University (2013 - 2017)",
    },
    {
        "filename": "resume_priya_sharma.docx",
        "format": "docx",
        "name": "Priya Sharma",
        "title": "Staff Backend & Distributed Systems Engineer",
        "email": "priya.sharma@example.com | Phone: +1-555-0106 | Location: Boston, MA",
        "summary": (
            "Staff Software Engineer with 9 years of experience in distributed systems, high-volume transactions, "
            "and event streaming. Strong background in Java, Spring Boot, and Python automation."
        ),
        "skills": [
            "Languages: Java 17+, Python, SQL, C#",
            "Frameworks: Spring Boot, Spring Cloud, Hibernate, FastAPI",
            "Streaming & Messaging: Apache Kafka, RabbitMQ",
            "Databases: Oracle, PostgreSQL, Cassandra, Redis",
            "Cloud & DevOps: AWS, Kubernetes, Terraform, Prometheus, Grafana",
        ],
        "experience": [
            "Staff Backend Engineer | Apex Banking Core (2020 - Present)\n"
            "- Architected mission-critical payment settlement engine handling $500M daily settlement volume.\n"
            "- Designed Python automation harnesses for continuous fault injection and load testing.\n"
            "- Achieved 99.999% uptime across multi-region AWS cloud deployments.",
            "Senior Java Developer | GlobalFin Systems (2016 - 2020)\n"
            "- Modernized legacy monolithic financial core into decoupled Spring Boot microservices.\n"
            "- Implemented Kafka event streams for audit trails and real-time transaction reconciliation.",
        ],
        "education": "M.S. in Computer Science | Boston University (2014 - 2016)",
    },
    {
        "filename": "resume_david_wilson.txt",
        "format": "txt",
        "name": "David Wilson",
        "title": "DevOps & Cloud Infrastructure Engineer",
        "email": "david.wilson@example.com | Phone: +1-555-0107 | Location: Denver, CO",
        "summary": (
            "DevOps Engineer with 6 years building secure, scalable infrastructure on AWS and GCP. "
            "Extensive experience in Infrastructure as Code (Terraform), Kubernetes cluster management, "
            "and Python automation scripting."
        ),
        "skills": [
            "Cloud Providers: AWS, Google Cloud Platform (GCP)",
            "Containerization: Docker, Kubernetes, Helm, ArgoCD",
            "IaC & Config: Terraform, Ansible, CloudFormation",
            "Scripting & CI/CD: Python, Bash, GitHub Actions, GitLab CI, Jenkins",
            "Monitoring: Prometheus, Grafana, Datadog, ELK Stack",
        ],
        "experience": [
            "Senior DevOps Engineer | CloudPulse Technologies (2021 - Present)\n"
            "- Orchestrated multi-tenant Kubernetes clusters running 200+ containerized microservices.\n"
            "- Authored custom Python automation scripts for AWS resource cost governance, reducing cloud spend by 28%.\n"
            "- Enforced zero-trust network policies and automated security scanning in CI/CD pipeline.",
            "Cloud Operations Engineer | DataBasecamp (2018 - 2021)\n"
            "- Managed automated deployments using Terraform and Ansible across hybrid cloud environments.\n"
            "- Reduced mean time to recovery (MTTR) by 60% through proactive alerting in Datadog.",
        ],
        "education": "B.S. in Computer Information Systems | Colorado State University (2014 - 2018)",
    },
    {
        "filename": "resume_sarah_connor.txt",
        "format": "txt",
        "name": "Sarah Connor",
        "title": "Lead UI/UX & Frontend Engineer",
        "email": "sarah.connor@example.com | Phone: +1-555-0108 | Location: Los Angeles, CA",
        "summary": (
            "Frontend Engineer and Designer with 7 years crafting intuitive, accessible, and delightful digital "
            "experiences. Deep expertise in React, Next.js, design systems, and frontend performance."
        ),
        "skills": [
            "Frontend Core: JavaScript (ESNext), TypeScript, HTML5, CSS3/Sass",
            "Libraries: React, Next.js, Vue.js, Tailwind CSS, Radix UI, Storybook",
            "Design & Prototyping: Figma, Adobe XD, Design Systems, Accessibility (WCAG 2.1 AA)",
            "Testing & Tooling: Jest, React Testing Library, Vite, Webpack",
        ],
        "experience": [
            "Lead Frontend Engineer | PixelCraft Studio (2020 - Present)\n"
            "- Created an open-source design system adopted by 15 engineering squads across web and mobile.\n"
            "- Rewrote client dashboard in Next.js and TypeScript, slashing bundle size by 50%.\n"
            "- Spearheaded accessibility audits to achieve complete WCAG 2.1 AA compliance.",
            "Frontend Developer | CreativePulse (2017 - 2020)\n"
            "- Built interactive marketing websites with high-converting animations and responsive layouts.\n"
            "- Collaborated closely with product designers to prototype rapid proof-of-concepts.",
        ],
        "education": "B.F.A. in Digital Arts & Design | UCLA (2013 - 2017)",
    },
]


def build_pdf(resume: dict, dest: Path) -> None:
    """Generate a clean, professional PDF resume using ReportLab."""
    doc = SimpleDocTemplate(
        str(dest),
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=35,
        bottomMargin=35,
    )
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ResumeTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#1A365D"),
        spaceAfter=2,
    )
    subtitle_style = ParagraphStyle(
        "ResumeSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=15,
        textColor=colors.HexColor("#2B6CB0"),
        spaceAfter=4,
    )
    contact_style = ParagraphStyle(
        "ResumeContact",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#4A5568"),
        spaceAfter=12,
    )
    section_head_style = ParagraphStyle(
        "ResumeSection",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=15,
        textColor=colors.HexColor("#2D3748"),
        spaceBefore=8,
        spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "ResumeBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor("#2D3748"),
        spaceAfter=4,
    )

    story = [
        Paragraph(resume["name"], title_style),
        Paragraph(resume["title"], subtitle_style),
        Paragraph(resume["email"], contact_style),
        Spacer(1, 4),
        Paragraph("<b>PROFESSIONAL SUMMARY</b>", section_head_style),
        Paragraph(resume["summary"], body_style),
        Spacer(1, 4),
        Paragraph("<b>CORE TECHNICAL SKILLS</b>", section_head_style),
    ]

    for skill in resume["skills"]:
        story.append(Paragraph(f"• {skill}", body_style))

    story.append(Spacer(1, 4))
    story.append(Paragraph("<b>WORK EXPERIENCE</b>", section_head_style))

    for exp in resume["experience"]:
        lines = exp.split("\n")
        header = lines[0]
        story.append(Paragraph(f"<b>{header}</b>", body_style))
        for bullet in lines[1:]:
            story.append(Paragraph(bullet.strip(), body_style))
        story.append(Spacer(1, 2))

    story.append(Spacer(1, 4))
    story.append(Paragraph("<b>EDUCATION</b>", section_head_style))
    story.append(Paragraph(resume["education"], body_style))

    doc.build(story)


def build_docx(resume: dict, dest: Path) -> None:
    """Generate a clean DOCX resume using python-docx."""
    doc = docx.Document()

    # Title / Name
    h = doc.add_heading(resume["name"], level=0)
    h.paragraph_format.space_after = docx.shared.Pt(2)

    sub = doc.add_paragraph()
    r_sub = sub.add_run(resume["title"])
    r_sub.bold = True
    r_sub.font.size = docx.shared.Pt(13)
    r_sub.font.color.rgb = docx.shared.RGBColor(43, 108, 176)
    sub.paragraph_format.space_after = docx.shared.Pt(2)

    contact = doc.add_paragraph(resume["email"])
    contact.runs[0].font.size = docx.shared.Pt(9)
    contact.runs[0].font.color.rgb = docx.shared.RGBColor(100, 116, 139)
    contact.paragraph_format.space_after = docx.shared.Pt(10)

    # Professional Summary
    doc.add_heading("PROFESSIONAL SUMMARY", level=1)
    doc.add_paragraph(resume["summary"])

    # Core Technical Skills
    doc.add_heading("CORE TECHNICAL SKILLS", level=1)
    for skill in resume["skills"]:
        doc.add_paragraph(skill, style="List Bullet")

    # Work Experience
    doc.add_heading("WORK EXPERIENCE", level=1)
    for exp in resume["experience"]:
        lines = exp.split("\n")
        p_hdr = doc.add_paragraph()
        r_hdr = p_hdr.add_run(lines[0])
        r_hdr.bold = True
        for bullet in lines[1:]:
            doc.add_paragraph(bullet.lstrip("- "), style="List Bullet")

    # Education
    doc.add_heading("EDUCATION", level=1)
    doc.add_paragraph(resume["education"])

    doc.save(str(dest))


def build_txt(resume: dict, dest: Path) -> None:
    """Generate a clean structured TXT resume."""
    lines = [
        "=" * 70,
        f"{resume['name']} - {resume['title']}",
        f"{resume['email']}",
        "=" * 70,
        "",
        "PROFESSIONAL SUMMARY",
        "-" * 40,
        resume["summary"],
        "",
        "CORE TECHNICAL SKILLS",
        "-" * 40,
    ]
    for skill in resume["skills"]:
        lines.append(f"  * {skill}")

    lines.extend(
        [
            "",
            "WORK EXPERIENCE",
            "-" * 40,
        ]
    )
    for exp in resume["experience"]:
        lines.append(exp)
        lines.append("")

    lines.extend(
        [
            "EDUCATION",
            "-" * 40,
            resume["education"],
            "",
            "=" * 70,
        ]
    )

    dest.write_text("\n".join(lines), encoding="utf-8")


def main():
    print(f"Generating sample resumes in: {RESUMES_DIR}")
    for item in RESUME_DATA:
        dest = RESUMES_DIR / item["filename"]
        fmt = item["format"]
        if fmt == "pdf":
            build_pdf(item, dest)
            print(f"  [PDF]  Created {dest.name}")
        elif fmt == "docx":
            build_docx(item, dest)
            print(f"  [DOCX] Created {dest.name}")
        elif fmt == "txt":
            build_txt(item, dest)
            print(f"  [TXT]  Created {dest.name}")
    print(f"Successfully created {len(RESUME_DATA)} resume files.")


if __name__ == "__main__":
    main()
