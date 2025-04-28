import os
import logging
import json
import shutil
from typing import Type, Dict, Any, List
from pathlib import Path
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class TemplateManagerInput(BaseModel):
    """Input schema for TemplateManagerTool."""
    action: str = Field(..., description="Action to perform: list, get, create, save, or delete")
    template_name: str = Field(None, description="Name of the template to work with")
    template_content: Dict[str, Any] = Field(None, description="Template content when creating or saving a template")
    template_type: str = Field("latex", description="Template type: latex or html")

class TemplateManagerTool(BaseTool):
    name: str = "TemplateManager"
    description: str = "Manages resume templates for different styles and formats"
    args_schema: Type[BaseModel] = TemplateManagerInput

    def __init__(self):
        super().__init__()
        self.base_dir = Path(__file__).resolve().parent.parent.parent  # root of the project
        self.templates_dir = self.base_dir / "templates"
        
        # Create templates directory if it doesn't exist
        if not self.templates_dir.exists():
            self.templates_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories for different template types
        for template_type in ["latex", "html"]:
            type_dir = self.templates_dir / template_type
            if not type_dir.exists():
                type_dir.mkdir(parents=True, exist_ok=True)
                
        # Create default templates if needed
        self._create_default_templates()
    
    def _run(self, action: str, template_name: str = None, template_content: Dict[str, Any] = None, template_type: str = "latex") -> Dict[str, Any]:
        """
        Manage resume templates
        """
        try:
            # Validate template_type
            if template_type not in ["latex", "html"]:
                return {
                    "success": False,
                    "error": f"Invalid template type: {template_type}. Must be 'latex' or 'html'."
                }
            
            # Actions that don't require template_name
            if action == "list":
                return self._list_templates(template_type)
            
            # Actions that require template_name
            if not template_name:
                return {
                    "success": False,
                    "error": "Template name is required for this action"
                }
                
            if action == "get":
                return self._get_template(template_name, template_type)
            elif action == "create":
                if not template_content:
                    return {
                        "success": False,
                        "error": "Template content is required for create action"
                    }
                return self._create_template(template_name, template_content, template_type)
            elif action == "save":
                if not template_content:
                    return {
                        "success": False,
                        "error": "Template content is required for save action"
                    }
                return self._save_template(template_name, template_content, template_type)
            elif action == "delete":
                return self._delete_template(template_name, template_type)
            else:
                return {
                    "success": False,
                    "error": f"Invalid action: {action}. Must be one of: list, get, create, save, delete"
                }
                
        except Exception as e:
            logger.error(f"Error in template manager: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to perform template operation: {str(e)}"
            }
    
    def _list_templates(self, template_type: str) -> Dict[str, Any]:
        """List all available templates of a specific type"""
        template_dir = self.templates_dir / template_type
        templates = []
        
        try:
            for template_file in template_dir.glob("*.json"):
                template_name = template_file.stem
                # Try to load the template to get its metadata
                try:
                    with open(template_file, 'r') as f:
                        template_data = json.load(f)
                        templates.append({
                            "name": template_name,
                            "description": template_data.get("description", "No description"),
                            "type": template_type,
                            "last_modified": template_file.stat().st_mtime
                        })
                except:
                    # If we can't load the JSON, still include the template but with less info
                    templates.append({
                        "name": template_name,
                        "type": template_type,
                        "last_modified": template_file.stat().st_mtime
                    })
            
            return {
                "success": True,
                "templates": templates
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error listing templates: {str(e)}"
            }
    
    def _get_template(self, template_name: str, template_type: str) -> Dict[str, Any]:
        """Get a specific template by name and type"""
        template_file = self.templates_dir / template_type / f"{template_name}.json"
        
        if not template_file.exists():
            return {
                "success": False,
                "error": f"Template not found: {template_name} ({template_type})"
            }
        
        try:
            with open(template_file, 'r') as f:
                template_data = json.load(f)
            
            return {
                "success": True,
                "template": template_data
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error reading template: {str(e)}"
            }
    
    def _create_template(self, template_name: str, template_content: Dict[str, Any], template_type: str) -> Dict[str, Any]:
        """Create a new template"""
        template_file = self.templates_dir / template_type / f"{template_name}.json"
        
        if template_file.exists():
            return {
                "success": False,
                "error": f"Template already exists: {template_name} ({template_type})"
            }
        
        try:
            # Ensure template has a description
            if "description" not in template_content:
                template_content["description"] = f"Custom {template_type} template"
            
            with open(template_file, 'w') as f:
                json.dump(template_content, f, indent=2)
            
            return {
                "success": True,
                "message": f"Template created: {template_name} ({template_type})",
                "path": str(template_file)
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error creating template: {str(e)}"
            }
    
    def _save_template(self, template_name: str, template_content: Dict[str, Any], template_type: str) -> Dict[str, Any]:
        """Save changes to an existing template or create a new one"""
        template_file = self.templates_dir / template_type / f"{template_name}.json"
        
        try:
            # Ensure template has a description
            if "description" not in template_content:
                template_content["description"] = f"Custom {template_type} template"
            
            # Create a backup if the file exists
            if template_file.exists():
                backup_file = template_file.with_suffix('.json.bak')
                shutil.copy2(template_file, backup_file)
            
            with open(template_file, 'w') as f:
                json.dump(template_content, f, indent=2)
            
            return {
                "success": True,
                "message": f"Template saved: {template_name} ({template_type})",
                "path": str(template_file)
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error saving template: {str(e)}"
            }
    
    def _delete_template(self, template_name: str, template_type: str) -> Dict[str, Any]:
        """Delete a template"""
        template_file = self.templates_dir / template_type / f"{template_name}.json"
        
        if not template_file.exists():
            return {
                "success": False,
                "error": f"Template not found: {template_name} ({template_type})"
            }
        
        try:
            # Create a backup before deleting
            backup_file = template_file.with_suffix('.json.bak')
            shutil.copy2(template_file, backup_file)
            
            # Delete the template
            template_file.unlink()
            
            return {
                "success": True,
                "message": f"Template deleted: {template_name} ({template_type})",
                "backup": str(backup_file)
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error deleting template: {str(e)}"
            }
    
    def _create_default_templates(self):
        """Create default templates if they don't exist"""
        # Default LaTeX template
        latex_default = {
            "description": "Classic ATS-friendly LaTeX template",
            "content": r"""
\documentclass[11pt,a4paper,sans]{moderncv}
\moderncvstyle{classic}
\moderncvcolor{blue}
\usepackage[utf8]{inputenc}
\usepackage[scale=0.85]{geometry}
\name{{{first_name}}}{{{last_name}}}
\title{{{job_title}}}
\phone{{{phone}}}
\email{{{email}}}
\social[linkedin]{{{linkedin_url}}}
\begin{document}
\makecvtitle
\section{Summary}
{{{summary}}}
\section{Skills}
{{{skills}}}
\section{Experience}
{{{experience}}}
\section{Education}
{{{education}}}
\section{Projects}
{{{projects}}}
\section{Certifications}
{{{certifications}}}
\end{document}
""",
            "sections": [
                "first_name", "last_name", "job_title", "phone", "email", "linkedin_url",
                "summary", "skills", "experience", "education", "projects", "certifications"
            ]
        }
        
        # Modern LaTeX template
        latex_modern = {
            "description": "Modern ATS-friendly LaTeX template",
            "content": r"""
\documentclass[11pt,a4paper,sans]{moderncv}
\moderncvstyle{banking}
\moderncvcolor{black}
\usepackage[utf8]{inputenc}
\usepackage[scale=0.85]{geometry}
\name{{{first_name}}}{{{last_name}}}
\title{{{job_title}}}
\phone{{{phone}}}
\email{{{email}}}
\social[linkedin]{{{linkedin_url}}}
\social[github]{{{github_url}}}
\begin{document}
\makecvtitle
\section{Professional Summary}
{{{summary}}}
\section{Technical Skills}
{{{skills}}}
\section{Professional Experience}
{{{experience}}}
\section{Education}
{{{education}}}
\section{Projects}
{{{projects}}}
\section{Certifications}
{{{certifications}}}
\end{document}
""",
            "sections": [
                "first_name", "last_name", "job_title", "phone", "email", 
                "linkedin_url", "github_url", "summary", "skills", "experience", 
                "education", "projects", "certifications"
            ]
        }
        
        # Default HTML template
        html_default = {
            "description": "Simple ATS-friendly HTML template",
            "content": """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{first_name}} {{last_name}} - Resume</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        h1 { text-align: center; }
        .header { text-align: center; margin-bottom: 20px; }
        .section { margin-bottom: 20px; }
        h2 { border-bottom: 1px solid #333; padding-bottom: 5px; }
        .contact { text-align: center; }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{first_name}} {{last_name}}</h1>
        <p class="contact">
            {{phone}} | {{email}} | <a href="https://linkedin.com/in/{{linkedin_url}}">LinkedIn</a>
        </p>
    </div>
    
    <div class="section">
        <h2>Summary</h2>
        <p>{{summary}}</p>
    </div>
    
    <div class="section">
        <h2>Skills</h2>
        <p>{{skills}}</p>
    </div>
    
    <div class="section">
        <h2>Experience</h2>
        {{experience}}
    </div>
    
    <div class="section">
        <h2>Education</h2>
        {{education}}
    </div>
    
    <div class="section">
        <h2>Projects</h2>
        {{projects}}
    </div>
    
    <div class="section">
        <h2>Certifications</h2>
        {{certifications}}
    </div>
</body>
</html>
""",
            "sections": [
                "first_name", "last_name", "phone", "email", "linkedin_url",
                "summary", "skills", "experience", "education", "projects", "certifications"
            ]
        }
        
        # Create default templates if they don't exist
        default_templates = {
            "classic": (latex_default, "latex"),
            "modern": (latex_modern, "latex"),
            "simple": (html_default, "html")
        }
        
        for name, (template, template_type) in default_templates.items():
            template_file = self.templates_dir / template_type / f"{name}.json"
            if not template_file.exists():
                with open(template_file, 'w') as f:
                    json.dump(template, f, indent=2)
                logger.info(f"Created default template: {name} ({template_type})") 