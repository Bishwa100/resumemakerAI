from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class Experience(BaseModel):
    job_title: str = Field(..., description="The title of the job held.")
    company: str = Field(..., description="The name of the company where the candidate worked.")
    start_date: Optional[str] = Field(None, description="Start date of the job.")
    end_date: Optional[str] = Field(None, description="End date of the job (or 'Present' if currently working).")
    description: Optional[str] = Field(None, description="Brief description of responsibilities and achievements.")


class Education(BaseModel):
    degree: str = Field(..., description="The degree obtained.")
    institution: str = Field(..., description="The name of the educational institution.")
    graduation_year: Optional[int] = Field(None, description="Year of graduation.")


class Skills(BaseModel):
    technical_skills: List[str] = Field(..., description="List of technical skills such as programming languages, tools, and frameworks.")
    soft_skills: List[str] = Field(..., description="List of soft skills such as communication, teamwork, and leadership.")
    endorsements: Optional[Dict[str, int]] = Field(None, description="Endorsements from LinkedIn for specific skills.")


class Projects(BaseModel):
    name: str = Field(..., description="Project name.")
    description: str = Field(..., description="Short summary of the project.")
    technologies_used: List[str] = Field(..., description="Technologies used in the project.")
    github_link: Optional[str] = Field(None, description="GitHub repository link if available.")


class GitHubProfile(BaseModel):
    username: str = Field(..., description="GitHub username.")
    repositories: List[Projects] = Field(..., description="List of public repositories and projects.")
    contributions: Dict[str, int] = Field(..., description="Number of commits, pull requests, and issues contributed.")


class JobPosting(BaseModel):
    title: str = Field(..., description="Job title in the posting.")
    company: str = Field(..., description="Company offering the job.")
    required_skills: List[str] = Field(..., description="List of required technical and soft skills.")
    experience_required: Optional[int] = Field(None, description="Minimum experience required in years.")
    job_description: Optional[str] = Field(None, description="Extracted text from the job description.")


class ResumeComparison(BaseModel):
    matching_skills: List[str] = Field(..., description="Skills that match between the resume and the job posting.")
    missing_skills: List[str] = Field(..., description="Skills required in the job posting but missing in the resume.")
    experience_match: str = Field(..., description="A summary of how well the candidate's experience aligns with the job posting.")
    improvement_suggestions: List[str] = Field(..., description="Suggestions to improve the resume for better alignment with the job posting.")


class CandidateProfile(BaseModel):
    name: str = Field(..., description="Candidate's full name.")
    email: Optional[str] = Field(None, description="Candidate's email address.")
    phone: Optional[str] = Field(None, description="Candidate's phone number.")
    linkedin_url: Optional[str] = Field(None, description="Candidate's LinkedIn profile URL.Which is also given as Input")
    github_url: Optional[str] = Field(None, description="Candidate's GitHub profile URL or github Username.")
    experience: List[Experience] = Field(..., description="List of work experiences.")
    education: List[Education] = Field(..., description="List of educational qualifications.")
    skills: Skills = Field(..., description="Technical and soft skills.")
    projects: List[Projects] = Field(..., description="List of projects.")
    github_profile: Optional[GitHubProfile] = Field(None, description="GitHub activity and contributions.")
    job_posting: Optional[JobPosting] = Field(None, description="Job posting details for comparison.")
    resume_comparison: Optional[ResumeComparison] = Field(None, description="Comparison report between resume and job requirements.")
    
    # Dynamic Extras
    extras: Optional[Dict[str, Any]] = Field(None, description="Additional optional fields like certifications, extracurricular activities, research papers, etc.")
