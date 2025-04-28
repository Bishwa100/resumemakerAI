import re
import logging
from typing import Type, Dict, Any, List
from collections import Counter
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class JobKeywordExtractorInput(BaseModel):
    """Input schema for JobKeywordExtractorTool."""
    job_description: str = Field(..., description="Job description text to analyze")
    resume_text: str = Field(None, description="Optional resume text to compare against")
    max_keywords: int = Field(30, description="Maximum number of keywords to extract")
    include_scores: bool = Field(True, description="Whether to include keyword scores in the output")

class JobKeywordExtractorTool(BaseTool):
    name: str = "JobKeywordExtractor"
    description: str = "Extracts key skills and requirements from job descriptions for ATS optimization"
    args_schema: Type[BaseModel] = JobKeywordExtractorInput

    # Common words to exclude from keyword analysis
    COMMON_WORDS = {
        "the", "and", "a", "an", "in", "on", "at", "to", "for", "with", 
        "by", "of", "is", "are", "be", "will", "have", "has", "had", "this",
        "that", "these", "those", "we", "you", "they", "it", "he", "she",
        "from", "as", "or", "not", "but", "all", "our", "your", "their", 
        "its", "can", "may", "about", "who", "when", "where", "which", "what",
        "how", "why", "any", "some", "such", "time", "same", "than", "then",
        "now", "every", "each", "only", "very", "just", "should", "would"
    }
    
    # Technical skill categories and related terms
    SKILL_CATEGORIES = {
        "programming_languages": [
            "python", "java", "javascript", "typescript", "c\\+\\+", "c#", "ruby", "php", 
            "scala", "kotlin", "go", "golang", "rust", "swift", "r", "perl", "shell"
        ],
        "web_development": [
            "html", "css", "react", "angular", "vue", "node", "express", "django", 
            "flask", "spring", "asp\\.net", "ruby on rails", "jquery", "bootstrap"
        ],
        "data_science": [
            "machine learning", "deep learning", "ai", "artificial intelligence", 
            "data mining", "nlp", "natural language processing", "computer vision",
            "neural networks", "pytorch", "tensorflow", "keras", "scikit-learn"
        ],
        "databases": [
            "sql", "mysql", "postgresql", "mongodb", "nosql", "redis", "oracle", 
            "dynamodb", "cassandra", "firebase", "elasticsearch"
        ],
        "cloud": [
            "aws", "azure", "gcp", "google cloud", "cloud computing", "serverless",
            "lambda", "ec2", "s3", "rds", "kubernetes", "docker", "container"
        ],
        "devops": [
            "ci/cd", "jenkins", "gitlab", "github actions", "automation", "terraform",
            "ansible", "puppet", "chef", "monitoring", "logging", "devops"
        ],
        "tools": [
            "git", "svn", "jira", "confluence", "slack", "figma", "sketch",
            "adobe", "photoshop", "illustrator", "xd", "intellij", "vscode"
        ]
    }
    
    # Skills that might be written in different ways
    SKILL_SYNONYMS = {
        "js": "javascript",
        "ts": "typescript",
        "py": "python",
        "react.js": "react",
        "reactjs": "react",
        "vue.js": "vue",
        "vuejs": "vue",
        "node.js": "node",
        "nodejs": "node",
        "postgres": "postgresql",
        "k8s": "kubernetes",
        "cicd": "ci/cd",
        "continuous integration": "ci/cd",
        "continuous deployment": "ci/cd",
    }
    
    def _run(self, job_description: str, resume_text: str = None, max_keywords: int = 30, include_scores: bool = True) -> Dict[str, Any]:
        """
        Extract key skills and requirements from a job description
        """
        try:
            # Normalize text
            job_description = job_description.lower()
            
            # Extract different types of keywords
            technical_skills = self._extract_technical_skills(job_description)
            soft_skills = self._extract_soft_skills(job_description)
            requirements = self._extract_requirements(job_description)
            domain_keywords = self._extract_domain_keywords(job_description)
            
            # Combine all keywords
            all_keywords = {
                **technical_skills,
                **soft_skills,
                **requirements,
                **domain_keywords
            }
            
            # Sort keywords by score
            sorted_keywords = sorted(all_keywords.items(), key=lambda x: x[1], reverse=True)
            top_keywords = sorted_keywords[:max_keywords]
            
            # Prepare results in different formats
            categorized_keywords = {
                "technical_skills": {k: v for k, v in technical_skills.items() if v >= 2},
                "soft_skills": {k: v for k, v in soft_skills.items() if v >= 2},
                "requirements": {k: v for k, v in requirements.items() if v >= 2},
                "domain_keywords": {k: v for k, v in domain_keywords.items() if v >= 2}
            }
            
            flat_keywords = [k for k, _ in top_keywords]
            
            # Compare with resume if provided
            resume_match = None
            if resume_text:
                resume_match = self._compare_with_resume(all_keywords, resume_text.lower())
            
            result = {
                "success": True,
                "top_keywords": flat_keywords,
                "categorized_keywords": categorized_keywords,
            }
            
            if include_scores:
                result["keyword_scores"] = {k: v for k, v in top_keywords}
                
            if resume_match:
                result["resume_match"] = resume_match
                
            return result
            
        except Exception as e:
            logger.error(f"Error extracting job keywords: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to extract keywords: {str(e)}"
            }
    
    def _extract_technical_skills(self, text: str) -> Dict[str, int]:
        """Extract technical skills from job description"""
        skills = {}
        
        # Check for skills in each category
        for category, category_skills in self.SKILL_CATEGORIES.items():
            for skill in category_skills:
                # Look for the skill as a standalone word
                pattern = r'\b{}\b'.format(skill)
                matches = re.findall(pattern, text)
                if matches:
                    # Higher score for technical skills
                    skills[skill] = len(matches) * 2
        
        # Check for synonyms
        for synonym, canonical in self.SKILL_SYNONYMS.items():
            pattern = r'\b{}\b'.format(synonym)
            matches = re.findall(pattern, text)
            if matches and canonical in skills:
                skills[canonical] += len(matches) * 2
            elif matches:
                skills[canonical] = len(matches) * 2
                
        return skills
    
    def _extract_soft_skills(self, text: str) -> Dict[str, int]:
        """Extract soft skills from job description"""
        soft_skills = [
            "communication", "teamwork", "leadership", "problem solving", 
            "critical thinking", "time management", "adaptability", "creativity",
            "collaboration", "organization", "interpersonal", "presentation",
            "writing", "analytical", "detail oriented", "multitasking", "proactive"
        ]
        
        skills = {}
        for skill in soft_skills:
            pattern = r'\b{}\b'.format(skill)
            matches = re.findall(pattern, text)
            if matches:
                skills[skill] = len(matches)
                
        return skills
    
    def _extract_requirements(self, text: str) -> Dict[str, int]:
        """Extract requirement patterns from job description"""
        requirements = {}
        
        # Experience patterns
        experience_patterns = [
            r'(\d+)[\+]?\s+years',
            r'(\d+)[\+]?\s+year',
            r'(\d+)-(\d+)\s+years',
            r'minimum\s+of\s+(\d+)',
            r'at\s+least\s+(\d+)'
        ]
        
        for pattern in experience_patterns:
            matches = re.findall(pattern, text)
            if matches:
                if isinstance(matches[0], tuple):
                    # Range like "3-5 years"
                    requirements["experience"] = 3  # High importance
                else:
                    # Single value like "3+ years"
                    requirements["experience"] = 3
        
        # Education patterns
        education_keywords = [
            "bachelor", "master", "phd", "degree", "bs", "ms", "ba", "ma",
            "computer science", "engineering", "business", "mba"
        ]
        
        for keyword in education_keywords:
            pattern = r'\b{}\b'.format(keyword)
            matches = re.findall(pattern, text)
            if matches:
                if "education" in requirements:
                    requirements["education"] += len(matches)
                else:
                    requirements["education"] = len(matches)
        
        # Certification patterns
        cert_patterns = [
            r'certification',
            r'certified',
            r'certificate',
            r'license'
        ]
        
        for pattern in cert_patterns:
            matches = re.findall(pattern, text)
            if matches:
                if "certification" in requirements:
                    requirements["certification"] += len(matches)
                else:
                    requirements["certification"] = len(matches)
                    
        return requirements
    
    def _extract_domain_keywords(self, text: str) -> Dict[str, int]:
        """Extract domain-specific keywords"""
        # Clean and tokenize text
        text = re.sub(r'[^\w\s]', ' ', text)
        words = text.split()
        
        # Filter out common words and short words
        filtered_words = [word for word in words if word not in self.COMMON_WORDS and len(word) > 3]
        
        # Count word frequency
        word_counts = Counter(filtered_words)
        
        # Keep only words that appear at least twice
        domain_keywords = {word: count for word, count in word_counts.items() if count >= 2}
        
        return domain_keywords
    
    def _compare_with_resume(self, job_keywords: Dict[str, int], resume_text: str) -> Dict[str, Any]:
        """Compare job keywords with resume text"""
        present_keywords = []
        missing_keywords = []
        
        total_score = 0
        max_score = 0
        
        for keyword, score in job_keywords.items():
            max_score += score
            if re.search(r'\b{}\b'.format(keyword), resume_text):
                present_keywords.append(keyword)
                total_score += score
            else:
                missing_keywords.append(keyword)
        
        # Sort missing keywords by importance (score)
        missing_keywords_with_scores = [(k, job_keywords[k]) for k in missing_keywords]
        sorted_missing = sorted(missing_keywords_with_scores, key=lambda x: x[1], reverse=True)
        important_missing = [k for k, _ in sorted_missing[:10]]  # Top 10 missing keywords
        
        # Calculate match percentage
        match_percentage = (total_score / max_score * 100) if max_score > 0 else 0
        
        return {
            "match_percentage": round(match_percentage, 1),
            "present_keywords": present_keywords,
            "missing_keywords": important_missing,
            "total_keywords": len(job_keywords),
            "total_matches": len(present_keywords)
        } 