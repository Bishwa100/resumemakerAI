import os
import logging
import re
from typing import Type, Dict, Any, List
from pathlib import Path
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from resumemaker.tools.custom_tool import PDFAnalyzerTool

logger = logging.getLogger(__name__)

class ResumeAnalyzerInput(BaseModel):
    """Input schema for ResumeAnalyzerTool."""
    resume_path: str = Field(..., description="Path to the resume file (PDF)")
    job_description: str = Field(None, description="Optional job description to compare against")

class ResumeAnalyzerTool(BaseTool):
    name: str = "ResumeAnalyzer"
    description: str = "Analyzes resumes for ATS compatibility and provides improvement suggestions"
    args_schema: Type[BaseModel] = ResumeAnalyzerInput

    def __init__(self):
        super().__init__()
        self.pdf_analyzer = PDFAnalyzerTool()
        
    def _run(self, resume_path: str, job_description: str = None) -> Dict[str, Any]:
        """
        Analyze a resume for ATS compatibility and provide improvement suggestions
        """
        try:
            # Extract text from PDF
            resume_text = self.pdf_analyzer._run(resume_path)
            
            # Run basic ATS compatibility checks
            ats_issues = self._check_ats_compatibility(resume_text)
            
            # Calculate keyword match if job description is provided
            keyword_match = None
            if job_description:
                keyword_match = self._calculate_keyword_match(resume_text, job_description)
            
            # Generate actionable suggestions
            suggestions = self._generate_suggestions(ats_issues, keyword_match)
            
            return {
                "success": True,
                "ats_compatibility_score": self._calculate_ats_score(ats_issues),
                "issues": ats_issues,
                "keyword_match": keyword_match,
                "suggestions": suggestions
            }
            
        except Exception as e:
            logger.error(f"Error analyzing resume: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to analyze resume: {str(e)}"
            }
    
    def _check_ats_compatibility(self, resume_text: str) -> Dict[str, Any]:
        """Check for common ATS compatibility issues"""
        issues = {}
        
        # Check for complex formatting
        if self._has_complex_formatting(resume_text):
            issues["complex_formatting"] = "Detected potential complex formatting that may cause issues with ATS"
        
        # Check for tables
        if self._has_tables(resume_text):
            issues["tables"] = "Detected potential tables which can confuse ATS systems"
        
        # Check for headers/footers
        if self._has_headers_footers(resume_text):
            issues["headers_footers"] = "Detected potential headers/footers which might be ignored by ATS"
        
        # Check for appropriate section headings
        issues["missing_sections"] = self._check_missing_sections(resume_text)
        
        # Check for contact information
        if not self._has_contact_info(resume_text):
            issues["contact_info"] = "Contact information might be missing or not clearly formatted"
        
        return issues
    
    def _has_complex_formatting(self, text: str) -> bool:
        """Detect potential complex formatting"""
        # This is a basic heuristic - in reality, we'd need to analyze the PDF structure
        unusual_chars = re.findall(r'[^\w\s@\.,;:/()\-\'"&+]', text)
        return len(unusual_chars) > 10
    
    def _has_tables(self, text: str) -> bool:
        """Detect potential tables"""
        # Look for patterns that might indicate tables, like multiple lines with similar structure
        lines = text.split('\n')
        space_patterns = []
        for line in lines:
            if len(line.strip()) > 0:
                # Create a pattern of spaces in the line
                pattern = ''.join(['S' if c.isspace() else 'C' for c in line])
                space_patterns.append(pattern)
        
        # Count repeating patterns
        pattern_counts = {}
        for pattern in space_patterns:
            if len(pattern) > 10:  # Only consider substantive lines
                pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
        
        # If we have multiple lines with the same spacing pattern, it might be a table
        return any(count >= 3 for count in pattern_counts.values())
    
    def _has_headers_footers(self, text: str) -> bool:
        """Check for potential headers/footers"""
        lines = text.split('\n')
        if len(lines) < 10:
            return False
            
        # Check for repeating patterns at the top or bottom of pages
        # This is a simplified check
        first_lines = [lines[0], lines[1]]
        last_lines = [lines[-1], lines[-2]]
        
        potential_header = any(line.strip() and len(line.strip()) < 50 for line in first_lines)
        potential_footer = any(line.strip() and len(line.strip()) < 50 for line in last_lines)
        
        return potential_header or potential_footer
    
    def _check_missing_sections(self, text: str) -> List[str]:
        """Check for essential resume sections"""
        essential_sections = [
            "experience", "employment", "work",
            "education", "qualifications", "skills",
            "summary", "profile", "objective"
        ]
        
        missing_sections = []
        text_lower = text.lower()
        
        found_sections = set()
        for section in essential_sections:
            section_patterns = [
                f"{section}:", 
                f"{section.upper()}", 
                f"{section.title()}"
            ]
            if any(pattern in text_lower for pattern in section_patterns):
                category = self._categorize_section(section)
                found_sections.add(category)
        
        if "experience" not in found_sections:
            missing_sections.append("work experience")
        if "education" not in found_sections:
            missing_sections.append("education")
        if "skills" not in found_sections:
            missing_sections.append("skills")
        if "summary" not in found_sections:
            missing_sections.append("summary or objective")
            
        return missing_sections
    
    def _categorize_section(self, section: str) -> str:
        """Map specific section names to general categories"""
        if section in ["experience", "employment", "work"]:
            return "experience"
        elif section in ["education", "qualifications"]:
            return "education"
        elif section == "skills":
            return "skills"
        elif section in ["summary", "profile", "objective"]:
            return "summary"
        return section
    
    def _has_contact_info(self, text: str) -> bool:
        """Check if basic contact info is present"""
        # Look for email
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        has_email = bool(re.search(email_pattern, text))
        
        # Look for phone number
        phone_pattern = r'[\+\(]?[1-9][0-9 \-\(\)\.]{8,}[0-9]'
        has_phone = bool(re.search(phone_pattern, text))
        
        return has_email and has_phone
    
    def _calculate_ats_score(self, issues: Dict[str, Any]) -> int:
        """Calculate an ATS compatibility score from 0-100"""
        base_score = 100
        
        # Deduct points for each issue type
        if "complex_formatting" in issues:
            base_score -= 15
        if "tables" in issues:
            base_score -= 20
        if "headers_footers" in issues:
            base_score -= 10
        
        # Deduct points for missing sections
        missing_sections = issues.get("missing_sections", [])
        base_score -= len(missing_sections) * 10
        
        # Deduct for contact info issues
        if "contact_info" in issues:
            base_score -= 15
            
        return max(0, base_score)
    
    def _calculate_keyword_match(self, resume_text: str, job_description: str) -> Dict[str, Any]:
        """Calculate keyword match between resume and job description"""
        # Normalize text
        resume_text = resume_text.lower()
        job_description = job_description.lower()
        
        # Extract potential keywords from job description
        # This is a simple approach - a more sophisticated implementation would use NLP
        potential_keywords = self._extract_keywords(job_description)
        
        # Check which keywords are present in the resume
        matches = []
        missing = []
        
        for keyword in potential_keywords:
            if keyword in resume_text:
                matches.append(keyword)
            else:
                missing.append(keyword)
        
        match_percentage = len(matches) / len(potential_keywords) * 100 if potential_keywords else 0
        
        return {
            "match_percentage": round(match_percentage, 1),
            "matches": matches,
            "missing": missing
        }
    
    def _extract_keywords(self, job_description: str) -> List[str]:
        """Extract potential keywords from job description"""
        # Remove common words
        common_words = set([
            "the", "and", "a", "an", "in", "on", "at", "to", "for", "with", 
            "by", "of", "is", "are", "be", "will", "have", "has", "had", "this",
            "that", "these", "those", "we", "you", "they", "it", "he", "she",
            "from", "as", "or", "not", "but", "all", "our", "your", "their", "its"
        ])
        
        # Split text into words
        words = re.findall(r'\b[a-zA-Z][a-zA-Z-]{2,}\b', job_description)
        
        # Filter out common words and convert to lowercase
        keywords = [word.lower() for word in words if word.lower() not in common_words]
        
        # Count keyword frequency
        keyword_counts = {}
        for keyword in keywords:
            keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
        
        # Get the most frequent keywords
        sorted_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)
        top_keywords = [keyword for keyword, count in sorted_keywords[:20]]
        
        return top_keywords
    
    def _generate_suggestions(self, ats_issues: Dict[str, Any], keyword_match: Dict[str, Any] = None) -> List[str]:
        """Generate actionable suggestions for resume improvement"""
        suggestions = []
        
        # Suggestions based on ATS issues
        if "complex_formatting" in ats_issues:
            suggestions.append("Simplify formatting - use standard sections with clear headings")
            
        if "tables" in ats_issues:
            suggestions.append("Remove tables - use bullet points instead")
            
        if "headers_footers" in ats_issues:
            suggestions.append("Remove headers and footers - place contact info in the main body")
            
        missing_sections = ats_issues.get("missing_sections", [])
        for section in missing_sections:
            suggestions.append(f"Add a {section} section with clearly labeled heading")
            
        if "contact_info" in ats_issues:
            suggestions.append("Ensure contact information (email and phone) is clearly visible at the top")
            
        # Suggestions based on keyword match
        if keyword_match:
            # If keyword match is low, suggest adding missing keywords
            if keyword_match["match_percentage"] < 70:
                missing_keywords = keyword_match.get("missing", [])
                top_missing = missing_keywords[:5]  # Limit to top 5 missing keywords
                if top_missing:
                    suggestions.append(f"Add these relevant keywords from the job description: {', '.join(top_missing)}")
            
        return suggestions 