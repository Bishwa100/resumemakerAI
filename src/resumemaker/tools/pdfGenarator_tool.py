from typing import Type, Dict, Any
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import logging
from pathlib import Path
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, ListFlowable, ListItem
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

logger = logging.getLogger(__name__)

class PDFGeneratorInput(BaseModel):
    """Input schema for PDFGeneratorTool."""
    resume_content: Dict[str, Any] = Field(..., description="Dictionary containing all resume content sections")
    design_spec: Dict[str, Any] = Field(..., description="Dictionary with design specifications")
    image_data: Dict[str, Any] = Field(None, description="Optional dictionary with processed image information")

class PDFGeneratorTool(BaseTool):
    name: str = "PDFGenerator"
    description: str = "Generates ATS-friendly PDF resumes with professional design"
    args_schema: Type[BaseModel] = PDFGeneratorInput

    def _run(self, resume_content: Dict[str, Any], design_spec: Dict[str, Any], image_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate a PDF resume based on content, design specifications, and optional image
        """
        try:
            # Create output directory if it doesn't exist
            output_dir = Path("generated_resumes")
            output_dir.mkdir(exist_ok=True)
            
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = output_dir / f"resume_{timestamp}.pdf"
            
            # Register fonts if specified in design_spec
            self._register_fonts(design_spec.get("fonts", []))
            
            # Create the PDF document
            doc = SimpleDocTemplate(
                str(output_path),
                pagesize=letter,
                rightMargin=0.5*inch,
                leftMargin=0.5*inch,
                topMargin=0.5*inch,
                bottomMargin=0.5*inch
            )
            
            # Build resume elements
            elements = []
            styles = self._create_styles(design_spec)
            
            # Add header with name and contact info
            self._add_header(elements, resume_content, styles, image_data)
            
            # Add each section
            self._add_professional_summary(elements, resume_content, styles)
            self._add_skills_section(elements, resume_content, styles)
            self._add_experience_section(elements, resume_content, styles)
            self._add_education_section(elements, resume_content, styles)
            
            # Additional sections as needed
            if "certifications" in resume_content:
                self._add_certifications_section(elements, resume_content, styles)
            
            if "projects" in resume_content:
                self._add_projects_section(elements, resume_content, styles)
            
            # Build and save the PDF
            doc.build(elements)
            
            logger.info(f"Resume PDF generated successfully: {output_path}")
            return {
                "success": True,
                "output_path": str(output_path),
                "message": "Resume PDF generated successfully"
            }
            
        except Exception as e:
            logger.error(f"Error generating PDF resume: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to generate PDF resume: {str(e)}"
            }
    
    def _register_fonts(self, fonts):
        """Register custom fonts for use in the PDF"""
        try:
            for font in fonts:
                if "path" in font and "name" in font:
                    pdfmetrics.registerFont(TTFont(font["name"], font["path"]))
        except Exception as e:
            logger.warning(f"Could not register custom fonts: {str(e)}")
    
    def _create_styles(self, design_spec):
        """Create paragraph styles based on design specifications"""
        styles = getSampleStyleSheet()
        
        # Create custom styles based on design_spec
        custom_styles = {
            "Name": ParagraphStyle(
                "Name",
                parent=styles["Heading1"],
                fontSize=16,
                leading=20,
                textColor=colors.HexColor(design_spec.get("primary_color", "#000000"))
            ),
            "SectionHeader": ParagraphStyle(
                "SectionHeader",
                parent=styles["Heading2"],
                fontSize=12,
                leading=14,
                textColor=colors.HexColor(design_spec.get("primary_color", "#000000")),
                spaceAfter=6
            ),
            "Normal": ParagraphStyle(
                "Normal",
                parent=styles["Normal"],
                fontSize=10,
                leading=12
            ),
            "BulletPoint": ParagraphStyle(
                "BulletPoint",
                parent=styles["Normal"],
                fontSize=10,
                leading=12,
                leftIndent=20
            )
        }
        
        # Add custom styles to the styles dictionary
        for name, style in custom_styles.items():
            styles.add(style, name)
        
        return styles
    
    def _add_header(self, elements, resume_content, styles, image_data):
        """Add the resume header with name, contact info, and optional image"""
        if "personal_info" not in resume_content:
            return
        
        personal_info = resume_content["personal_info"]
        
        # Create a table for header layout
        data = []
        
        # Name and contact in the first column
        name_contact = []
        name_contact.append(Paragraph(personal_info.get("name", ""), styles["Name"]))
        
        # Contact details
        contact_text = []
        if "email" in personal_info:
            contact_text.append(personal_info["email"])
        if "phone" in personal_info:
            contact_text.append(personal_info["phone"])
        if "linkedin" in personal_info:
            contact_text.append(personal_info["linkedin"])
        if "github" in personal_info:
            contact_text.append("GitHub: " + personal_info["github"])
        if "location" in personal_info:
            contact_text.append(personal_info["location"])
            
        contact_paragraph = Paragraph(" | ".join(contact_text), styles["Normal"])
        name_contact.append(contact_paragraph)
        
        # Build the header table
        if image_data and "processed_path" in image_data and not "error" in image_data:
            # With image: two-column layout
            try:
                img = Image(image_data["processed_path"], width=1*inch, height=1*inch)
                data.append([name_contact, img])
                col_widths = [5*inch, 1*inch]
            except:
                # Fallback if image can't be loaded
                data.append([name_contact])
                col_widths = [6.5*inch]
        else:
            # Without image: single column
            data.append([name_contact])
            col_widths = [6.5*inch]
        
        # Create and style the table
        header_table = Table(data, colWidths=col_widths)
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT') if len(data[0]) > 1 else []
        ]))
        
        elements.append(header_table)
        elements.append(Spacer(1, 0.2*inch))
    
    def _add_professional_summary(self, elements, resume_content, styles):
        """Add the professional summary section"""
        if "summary" not in resume_content:
            return
            
        elements.append(Paragraph("PROFESSIONAL SUMMARY", styles["SectionHeader"]))
        elements.append(Paragraph(resume_content["summary"], styles["Normal"]))
        elements.append(Spacer(1, 0.2*inch))
    
    def _add_skills_section(self, elements, resume_content, styles):
        """Add the skills section"""
        if "skills" not in resume_content:
            return
            
        elements.append(Paragraph("SKILLS", styles["SectionHeader"]))
        
        # Group skills by category if available
        if isinstance(resume_content["skills"], dict):
            # Skills are categorized
            skills_table_data = []
            for category, skills_list in resume_content["skills"].items():
                if isinstance(skills_list, list):
                    skills_text = ", ".join(skills_list)
                else:
                    skills_text = skills_list
                skills_table_data.append([Paragraph(f"<b>{category}:</b>", styles["Normal"]), 
                                         Paragraph(skills_text, styles["Normal"])])
            
            # Create a table for the skills
            skills_table = Table(skills_table_data, colWidths=[1.5*inch, 5*inch])
            skills_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('RIGHTPADDING', (0, 0), (0, -1), 10)
            ]))
            elements.append(skills_table)
            
        elif isinstance(resume_content["skills"], list):
            # Skills are a simple list
            skills_text = ", ".join(resume_content["skills"])
            elements.append(Paragraph(skills_text, styles["Normal"]))
            
        elements.append(Spacer(1, 0.2*inch))
    
    def _add_experience_section(self, elements, resume_content, styles):
        """Add the work experience section"""
        if "experience" not in resume_content:
            return
            
        elements.append(Paragraph("PROFESSIONAL EXPERIENCE", styles["SectionHeader"]))
        
        for job in resume_content["experience"]:
            # Job title and company
            job_header = f"<b>{job.get('title', '')}</b>, {job.get('company', '')}"
            if "location" in job:
                job_header += f" | {job['location']}"
            elements.append(Paragraph(job_header, styles["Normal"]))
            
            # Dates
            date_text = f"{job.get('start_date', '')} - {job.get('end_date', 'Present')}"
            elements.append(Paragraph(date_text, styles["Normal"]))
            
            # Description bullets
            if "description" in job:
                bullet_list = []
                if isinstance(job["description"], list):
                    for bullet in job["description"]:
                        bullet_list.append(ListItem(Paragraph(bullet, styles["BulletPoint"])))
                else:
                    bullet_list.append(ListItem(Paragraph(job["description"], styles["BulletPoint"])))
                
                elements.append(ListFlowable(bullet_list, bulletType='bullet', start='•'))
            
            elements.append(Spacer(1, 0.1*inch))
        
        elements.append(Spacer(1, 0.1*inch))
    
    def _add_education_section(self, elements, resume_content, styles):
        """Add the education section"""
        if "education" not in resume_content:
            return
            
        elements.append(Paragraph("EDUCATION", styles["SectionHeader"]))
        
        for edu in resume_content["education"]:
            # Degree and institution
            edu_header = f"<b>{edu.get('degree', '')}</b>, {edu.get('institution', '')}"
            if "location" in edu:
                edu_header += f" | {edu['location']}"
            elements.append(Paragraph(edu_header, styles["Normal"]))
            
            # Dates
            if "graduation_date" in edu:
                elements.append(Paragraph(f"Graduated: {edu['graduation_date']}", styles["Normal"]))
            elif "start_date" in edu and "end_date" in edu:
                edu_dates = f"{edu['start_date']} - {edu['end_date']}"
                elements.append(Paragraph(edu_dates, styles["Normal"]))
            
            # Additional details
            if "gpa" in edu:
                elements.append(Paragraph(f"GPA: {edu['gpa']}", styles["Normal"]))
            
            if "highlights" in edu:
                bullet_list = []
                if isinstance(edu["highlights"], list):
                    for bullet in edu["highlights"]:
                        bullet_list.append(ListItem(Paragraph(bullet, styles["BulletPoint"])))
                else:
                    bullet_list.append(ListItem(Paragraph(edu["highlights"], styles["BulletPoint"])))
                
                elements.append(ListFlowable(bullet_list, bulletType='bullet', start='•'))
            
            elements.append(Spacer(1, 0.1*inch))
    
    def _add_certifications_section(self, elements, resume_content, styles):
        """Add certifications section"""
        elements.append(Paragraph("CERTIFICATIONS", styles["SectionHeader"]))
        
        for cert in resume_content["certifications"]:
            if isinstance(cert, dict):
                cert_text = f"<b>{cert.get('name', '')}</b>"
                if "issuer" in cert:
                    cert_text += f", {cert['issuer']}"
                if "date" in cert:
                    cert_text += f" ({cert['date']})"
                elements.append(Paragraph(cert_text, styles["Normal"]))
            else:
                elements.append(Paragraph(cert, styles["Normal"]))
            
        elements.append(Spacer(1, 0.2*inch))
    
    def _add_projects_section(self, elements, resume_content, styles):
        """Add projects section"""
        elements.append(Paragraph("PROJECTS", styles["SectionHeader"]))
        
        for project in resume_content["projects"]:
            # Project name and link
            project_header = f"<b>{project.get('name', '')}</b>"
            if "url" in project:
                project_header += f" | {project['url']}"
            elements.append(Paragraph(project_header, styles["Normal"]))
            
            # Dates if available
            if "date" in project:
                elements.append(Paragraph(project["date"], styles["Normal"]))
            
            # Description bullets
            if "description" in project:
                bullet_list = []
                if isinstance(project["description"], list):
                    for bullet in project["description"]:
                        bullet_list.append(ListItem(Paragraph(bullet, styles["BulletPoint"])))
                else:
                    bullet_list.append(ListItem(Paragraph(project["description"], styles["BulletPoint"])))
                
                elements.append(ListFlowable(bullet_list, bulletType='bullet', start='•'))
            
            # Technologies used
            if "technologies" in project:
                tech_text = "<i>Technologies:</i> "
                if isinstance(project["technologies"], list):
                    tech_text += ", ".join(project["technologies"])
                else:
                    tech_text += project["technologies"]
                elements.append(Paragraph(tech_text, styles["Normal"]))
            
            elements.append(Spacer(1, 0.1*inch))