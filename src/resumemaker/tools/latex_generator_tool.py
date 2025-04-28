import os
import logging
import subprocess
from pathlib import Path
from typing import Any
from crewai.tools import BaseTool

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LaTeXGeneratorTool(BaseTool):
    name: str = "LaTeX Generator Tool"
    description: str = "Generates and compiles ATS-friendly LaTeX resumes into PDF format"
    
    base_dir: Path = Path.cwd()
    templates_dir: Path = Path.cwd() / "templates"
    latex_template_path: Path = Path.cwd() / "templates" / "resume_template.tex"

    def __init__(self):
        super().__init__()
        self.base_dir = Path(__file__).resolve().parent.parent.parent  # Adjust to resumemaker root
        self.templates_dir = self.base_dir / "templates"
        if not self.templates_dir.exists():
            self.templates_dir.mkdir(exist_ok=True)
        
        self.latex_template_path = self.templates_dir / "resume_template.tex"
        if not self.latex_template_path.exists():
            self._create_default_template()
    
    def _create_default_template(self):
        default_template = r"""
\documentclass[11pt,a4paper,sans]{moderncv}
\moderncvstyle{classic}
\moderncvcolor{black}
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
"""
        with open(self.latex_template_path, 'w') as f:
            f.write(default_template)
        logger.info(f"Created ATS-friendly LaTeX resume template at {self.latex_template_path}")
    
    def _generate_latex(self, template_variables, template_path=None, output_path=None):
        if not template_path:
            template_path = self.latex_template_path
        if not output_path:
            output_path = self.base_dir / "output" / "resume.tex"
        
        output_dir = Path(output_path).parent
        if not output_dir.exists():
            output_dir.mkdir(parents=True, exist_ok=True)
        
        with open(template_path, 'r') as f:
            template_content = f.read()
        
        try:
            for key, value in template_variables.items():
                placeholder = '{{{' + key + '}}}'
                template_content = template_content.replace(placeholder, str(value or ''))
            
            with open(output_path, 'w') as f:
                f.write(template_content)
            
            logger.info(f"Generated ATS-friendly LaTeX resume at {output_path}")
            return str(output_path)
        except Exception as e:
            logger.error(f"Error generating LaTeX resume: {str(e)}")
            raise
    
    def _compile_to_pdf(self, latex_path, output_dir=None):
        latex_path = Path(latex_path)
        if not output_dir:
            output_dir = latex_path.parent
        else:
            output_dir = Path(output_dir)
            if not output_dir.exists():
                output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            logger.info(f"Compiling LaTeX file {latex_path} to PDF")
            original_dir = os.getcwd()
            os.chdir(latex_path.parent)
            
            for _ in range(2):
                result = subprocess.run(
                    ['pdflatex', '-interaction=nonstopmode', latex_path.name],
                    capture_output=True, 
                    text=True
                )
                if result.returncode != 0:
                    logger.error(f"pdflatex error: {result.stderr}")
                    raise Exception(f"Failed to compile LaTeX: {result.stderr}")
            
            os.chdir(original_dir)
            pdf_path = latex_path.with_suffix('.pdf')
            if not pdf_path.exists():
                raise FileNotFoundError(f"PDF file not found at expected path: {pdf_path}")
            
            logger.info(f"Successfully compiled PDF at {pdf_path}")
            return str(pdf_path)
        except Exception as e:
            logger.error(f"Error compiling LaTeX to PDF: {str(e)}")
            raise
    
    def _run(self, action: str, **kwargs) -> str:
        if action == "generate_latex":
            return self._generate_latex(kwargs.get("template_variables", {}), 
                                      kwargs.get("template_path"), 
                                      kwargs.get("output_path"))
        elif action == "compile_to_pdf":
            return self._compile_to_pdf(kwargs.get("latex_path"), 
                                      kwargs.get("output_dir"))
        else:
            raise ValueError(f"Unsupported action: {action}. Use 'generate_latex' or 'compile_to_pdf'.")