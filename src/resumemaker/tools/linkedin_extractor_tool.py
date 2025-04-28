import os
import time
import json
import logging
import tempfile
import base64
from typing import Type, Dict, Any, Optional, List
from pathlib import Path
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class LinkedInExtractorInput(BaseModel):
    """Input schema for LinkedInExtractorTool."""
    profile_url: str = Field(..., description="LinkedIn profile URL to extract data from")
    credentials_path: str = Field(None, description="Path to credentials JSON file with LinkedIn login info")
    screenshot: bool = Field(False, description="Whether to take a screenshot of the profile")
    output_path: str = Field(None, description="Path to save extracted data and screenshots")
    headless: bool = Field(True, description="Whether to run browser in headless mode")

class LinkedInExtractorTool(BaseTool):
    name: str = "LinkedInExtractor"
    description: str = "Extracts professional data from LinkedIn profiles using web automation"
    args_schema: Type[BaseModel] = LinkedInExtractorInput

    def __init__(self):
        super().__init__()
        self._driver = None
        self._is_logged_in = False
        
    def _run(self, profile_url: str, credentials_path: Optional[str] = None, 
             screenshot: bool = False, output_path: Optional[str] = None,
             headless: bool = True) -> Dict[str, Any]:
        """
        Extract data from a LinkedIn profile
        """
        try:
            # Import here to avoid selenium being a strict requirement
            try:
                from selenium import webdriver
                from selenium.webdriver.chrome.options import Options
                from selenium.webdriver.chrome.service import Service
                from selenium.webdriver.common.by import By
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                from selenium.common.exceptions import TimeoutException, NoSuchElementException
                from webdriver_manager.chrome import ChromeDriverManager
            except ImportError:
                return {
                    "success": False,
                    "error": "Selenium is not installed. Please install it with: pip install selenium webdriver-manager"
                }
            
            # Setup output directory
            if output_path:
                output_dir = Path(output_path)
                output_dir.mkdir(parents=True, exist_ok=True)
            else:
                output_dir = Path(tempfile.mkdtemp())
            
            # Setup Chrome options
            chrome_options = Options()
            if headless:
                chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-notifications")
            chrome_options.add_argument("--disable-infobars")
            chrome_options.add_argument("--disable-extensions")
            
            # Create a new Chrome driver if not already created
            if self._driver is None:
                service = Service(ChromeDriverManager().install())
                self._driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Login to LinkedIn if credentials are provided and not already logged in
            if credentials_path and not self._is_logged_in:
                self._login_to_linkedin(credentials_path)
            
            # Navigate to the profile
            logger.info(f"Navigating to LinkedIn profile: {profile_url}")
            self._driver.get(profile_url)
            
            # Wait for the page to load
            WebDriverWait(self._driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Scroll to load dynamic content
            self._scroll_page()
            
            # Take screenshot if requested
            screenshot_path = None
            if screenshot:
                screenshot_path = output_dir / f"linkedin_profile_{int(time.time())}.png"
                self._driver.save_screenshot(str(screenshot_path))
                logger.info(f"Saved screenshot to {screenshot_path}")
            
            # Extract the profile data
            profile_data = self._extract_profile_data()
            
            # Save extracted data
            data_path = output_dir / f"linkedin_data_{int(time.time())}.json"
            with open(data_path, 'w') as f:
                json.dump(profile_data, f, indent=2)
            
            # Add image in base64 format if screenshot was taken
            if screenshot_path:
                with open(screenshot_path, 'rb') as img_file:
                    profile_data['screenshot'] = base64.b64encode(img_file.read()).decode('utf-8')
            
            return {
                "success": True,
                "profile_data": profile_data,
                "data_path": str(data_path),
                "screenshot_path": str(screenshot_path) if screenshot_path else None
            }
            
        except Exception as e:
            logger.error(f"Error extracting LinkedIn data: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to extract LinkedIn data: {str(e)}"
            }
        finally:
            # Close the driver if it was created in this run
            if self._driver and headless:
                self._driver.quit()
                self._driver = None
                self._is_logged_in = False
    
    def _login_to_linkedin(self, credentials_path: str) -> None:
        """Login to LinkedIn with credentials from a JSON file"""
        try:
            # Load credentials
            with open(credentials_path, 'r') as f:
                credentials = json.load(f)
            
            email = credentials.get('email')
            password = credentials.get('password')
            
            if not email or not password:
                logger.error("Invalid credentials file format. Needs 'email' and 'password' fields.")
                return
            
            # Navigate to LinkedIn login page
            self._driver.get("https://www.linkedin.com/login")
            
            # Wait for the login form to load
            WebDriverWait(self._driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            
            # Enter email and password
            self._driver.find_element(By.ID, "username").send_keys(email)
            self._driver.find_element(By.ID, "password").send_keys(password)
            
            # Click login button
            self._driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
            
            # Wait for login to complete
            WebDriverWait(self._driver, 10).until(
                EC.presence_of_element_located((By.ID, "global-nav"))
            )
            
            self._is_logged_in = True
            logger.info("Successfully logged in to LinkedIn")
            
        except Exception as e:
            logger.error(f"Failed to login to LinkedIn: {str(e)}")
            self._is_logged_in = False
    
    def _scroll_page(self) -> None:
        """Scroll the page to load all dynamic content"""
        # Get scroll height
        last_height = self._driver.execute_script("return document.body.scrollHeight")
        
        while True:
            # Scroll down
            self._driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # Wait to load page
            time.sleep(2)
            
            # Calculate new scroll height and compare with last scroll height
            new_height = self._driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
    
    def _extract_profile_data(self) -> Dict[str, Any]:
        """Extract data from the LinkedIn profile page"""
        profile_data = {
            "personal_info": self._extract_personal_info(),
            "about": self._extract_about(),
            "experience": self._extract_experience(),
            "education": self._extract_education(),
            "skills": self._extract_skills(),
            "certifications": self._extract_certifications(),
            "recommendations": self._extract_recommendations(),
            "projects": self._extract_projects(),
            "languages": self._extract_languages(),
            "interests": self._extract_interests()
        }
        
        return profile_data
    
    def _extract_personal_info(self) -> Dict[str, Any]:
        """Extract personal information from the profile"""
        personal_info = {}
        
        try:
            # Extract name
            name_element = self._driver.find_element(By.CSS_SELECTOR, "h1.text-heading-xlarge")
            personal_info["name"] = name_element.text.strip()
        except NoSuchElementException:
            personal_info["name"] = ""
        
        try:
            # Extract headline
            headline_element = self._driver.find_element(By.CSS_SELECTOR, "div.text-body-medium")
            personal_info["headline"] = headline_element.text.strip()
        except NoSuchElementException:
            personal_info["headline"] = ""
        
        try:
            # Extract location
            location_element = self._driver.find_element(By.CSS_SELECTOR, "span.text-body-small.inline")
            personal_info["location"] = location_element.text.strip()
        except NoSuchElementException:
            personal_info["location"] = ""
        
        try:
            # Extract contact info
            contact_info = {}
            contact_section = self._driver.find_elements(By.CSS_SELECTOR, "section.pv-contact-info")
            
            if contact_section:
                # Click to open contact info modal
                contact_button = self._driver.find_element(By.CSS_SELECTOR, "a.ember-view.link-without-visited-state.cursor-pointer")
                contact_button.click()
                time.sleep(1)
                
                # Extract email
                try:
                    email_element = self._driver.find_element(By.CSS_SELECTOR, "section.ci-email a.pv-contact-info__contact-link")
                    contact_info["email"] = email_element.text.strip()
                except NoSuchElementException:
                    contact_info["email"] = ""
                
                # Extract phone
                try:
                    phone_element = self._driver.find_element(By.CSS_SELECTOR, "section.ci-phone span.t-14")
                    contact_info["phone"] = phone_element.text.strip()
                except NoSuchElementException:
                    contact_info["phone"] = ""
                
                # Close modal
                close_button = self._driver.find_element(By.CSS_SELECTOR, "button.artdeco-modal__dismiss")
                close_button.click()
            
            personal_info["contact_info"] = contact_info
            
        except Exception as e:
            logger.error(f"Error extracting contact info: {str(e)}")
            personal_info["contact_info"] = {}
        
        return personal_info
    
    def _extract_about(self) -> str:
        """Extract about section from the profile"""
        try:
            about_sections = self._driver.find_elements(By.CSS_SELECTOR, "section.pv-about-section")
            if about_sections:
                about_text = about_sections[0].find_element(By.CSS_SELECTOR, "div.pv-shared-text-with-see-more div.inline-show-more-text").text.strip()
                return about_text
        except Exception as e:
            logger.error(f"Error extracting about: {str(e)}")
        
        return ""
    
    def _extract_experience(self) -> List[Dict[str, Any]]:
        """Extract work experience from the profile"""
        experiences = []
        
        try:
            experience_section = self._driver.find_elements(By.CSS_SELECTOR, "section#experience-section")
            
            if experience_section:
                experience_items = experience_section[0].find_elements(By.CSS_SELECTOR, "li.pv-entity__position-group-pager")
                
                for item in experience_items:
                    experience = {}
                    
                    # Company name
                    try:
                        company_element = item.find_element(By.CSS_SELECTOR, "p.pv-entity__secondary-title")
                        experience["company"] = company_element.text.strip()
                    except NoSuchElementException:
                        try:
                            company_element = item.find_element(By.CSS_SELECTOR, "h3.t-16")
                            experience["company"] = company_element.text.strip()
                        except NoSuchElementException:
                            experience["company"] = ""
                    
                    # Job title
                    try:
                        title_element = item.find_element(By.CSS_SELECTOR, "h3.t-16")
                        experience["title"] = title_element.text.strip()
                    except NoSuchElementException:
                        experience["title"] = ""
                    
                    # Duration
                    try:
                        date_range_element = item.find_element(By.CSS_SELECTOR, "h4.pv-entity__date-range span:not(.visually-hidden)")
                        experience["date_range"] = date_range_element.text.strip()
                    except NoSuchElementException:
                        experience["date_range"] = ""
                    
                    # Location
                    try:
                        location_element = item.find_element(By.CSS_SELECTOR, "h4.pv-entity__location span:not(.visually-hidden)")
                        experience["location"] = location_element.text.strip()
                    except NoSuchElementException:
                        experience["location"] = ""
                    
                    # Description
                    try:
                        description_element = item.find_element(By.CSS_SELECTOR, "div.pv-entity__description")
                        experience["description"] = description_element.text.strip()
                    except NoSuchElementException:
                        experience["description"] = ""
                    
                    experiences.append(experience)
        except Exception as e:
            logger.error(f"Error extracting experience: {str(e)}")
        
        return experiences
    
    def _extract_education(self) -> List[Dict[str, Any]]:
        """Extract education from the profile"""
        education_list = []
        
        try:
            education_section = self._driver.find_elements(By.CSS_SELECTOR, "section#education-section")
            
            if education_section:
                education_items = education_section[0].find_elements(By.CSS_SELECTOR, "li.pv-education-entity")
                
                for item in education_items:
                    education = {}
                    
                    # School name
                    try:
                        school_element = item.find_element(By.CSS_SELECTOR, "h3.pv-entity__school-name")
                        education["school"] = school_element.text.strip()
                    except NoSuchElementException:
                        education["school"] = ""
                    
                    # Degree
                    try:
                        degree_element = item.find_element(By.CSS_SELECTOR, "p.pv-entity__degree-name span.pv-entity__comma-item")
                        education["degree"] = degree_element.text.strip()
                    except NoSuchElementException:
                        education["degree"] = ""
                    
                    # Field of study
                    try:
                        field_element = item.find_element(By.CSS_SELECTOR, "p.pv-entity__fos span.pv-entity__comma-item")
                        education["field_of_study"] = field_element.text.strip()
                    except NoSuchElementException:
                        education["field_of_study"] = ""
                    
                    # Date range
                    try:
                        date_element = item.find_element(By.CSS_SELECTOR, "p.pv-entity__dates span.pv-entity__date-range span:not(.visually-hidden)")
                        education["date_range"] = date_element.text.strip()
                    except NoSuchElementException:
                        education["date_range"] = ""
                    
                    education_list.append(education)
        except Exception as e:
            logger.error(f"Error extracting education: {str(e)}")
        
        return education_list
    
    def _extract_skills(self) -> List[str]:
        """Extract skills from the profile"""
        skills = []
        
        try:
            # Try to expand skills section if it's present
            skills_button = self._driver.find_elements(By.CSS_SELECTOR, "button.pv-skills-section__additional-skills")
            if skills_button:
                skills_button[0].click()
                time.sleep(1)
            
            skills_section = self._driver.find_elements(By.CSS_SELECTOR, "section.pv-skill-categories-section")
            
            if skills_section:
                skill_elements = skills_section[0].find_elements(By.CSS_SELECTOR, "span.pv-skill-category-entity__name-text")
                skills = [skill.text.strip() for skill in skill_elements]
        except Exception as e:
            logger.error(f"Error extracting skills: {str(e)}")
        
        return skills
    
    def _extract_certifications(self) -> List[Dict[str, Any]]:
        """Extract certifications from the profile"""
        certifications = []
        
        try:
            cert_section = self._driver.find_elements(By.CSS_SELECTOR, "section#certifications-section")
            
            if cert_section:
                cert_items = cert_section[0].find_elements(By.CSS_SELECTOR, "li.pv-certification-entity")
                
                for item in cert_items:
                    cert = {}
                    
                    # Name
                    try:
                        name_element = item.find_element(By.CSS_SELECTOR, "h3.t-16")
                        cert["name"] = name_element.text.strip()
                    except NoSuchElementException:
                        cert["name"] = ""
                    
                    # Issuing authority
                    try:
                        issuer_element = item.find_element(By.CSS_SELECTOR, "p.t-14.t-normal span:not(.visually-hidden)")
                        cert["issuer"] = issuer_element.text.strip()
                    except NoSuchElementException:
                        cert["issuer"] = ""
                    
                    # Issue date
                    try:
                        date_element = item.find_element(By.CSS_SELECTOR, "p.pv-entity__dates span.pv-entity__date-range span:not(.visually-hidden)")
                        cert["date"] = date_element.text.strip()
                    except NoSuchElementException:
                        cert["date"] = ""
                    
                    certifications.append(cert)
        except Exception as e:
            logger.error(f"Error extracting certifications: {str(e)}")
        
        return certifications
    
    def _extract_recommendations(self) -> List[Dict[str, Any]]:
        """Extract recommendations from the profile"""
        recommendations = []
        
        try:
            rec_section = self._driver.find_elements(By.CSS_SELECTOR, "section#recommendations-section")
            
            if rec_section:
                rec_items = rec_section[0].find_elements(By.CSS_SELECTOR, "li.pv-recommendation-entity")
                
                for item in rec_items:
                    rec = {}
                    
                    # Recommender
                    try:
                        name_element = item.find_element(By.CSS_SELECTOR, "h3.t-16")
                        rec["recommender"] = name_element.text.strip()
                    except NoSuchElementException:
                        rec["recommender"] = ""
                    
                    # Relationship
                    try:
                        relationship_element = item.find_element(By.CSS_SELECTOR, "p.t-14")
                        rec["relationship"] = relationship_element.text.strip()
                    except NoSuchElementException:
                        rec["relationship"] = ""
                    
                    # Content
                    try:
                        content_element = item.find_element(By.CSS_SELECTOR, "div.pv-recommendation-entity__text")
                        rec["content"] = content_element.text.strip()
                    except NoSuchElementException:
                        rec["content"] = ""
                    
                    recommendations.append(rec)
        except Exception as e:
            logger.error(f"Error extracting recommendations: {str(e)}")
        
        return recommendations
    
    def _extract_projects(self) -> List[Dict[str, Any]]:
        """Extract projects from the profile"""
        projects = []
        
        try:
            project_section = self._driver.find_elements(By.CSS_SELECTOR, "section.pv-accomplishments-block.projects")
            
            if project_section:
                # Try to expand projects section
                expand_button = project_section[0].find_elements(By.CSS_SELECTOR, "button.pv-accomplishments-block__expand")
                if expand_button:
                    expand_button[0].click()
                    time.sleep(1)
                
                project_items = project_section[0].find_elements(By.CSS_SELECTOR, "li.pv-accomplishment-entity")
                
                for item in project_items:
                    project = {}
                    
                    # Title
                    try:
                        title_element = item.find_element(By.CSS_SELECTOR, "h4.pv-accomplishment-entity__title")
                        project["title"] = title_element.text.replace("Project name", "").strip()
                    except NoSuchElementException:
                        project["title"] = ""
                    
                    # Description
                    try:
                        description_element = item.find_element(By.CSS_SELECTOR, "p.pv-accomplishment-entity__description")
                        project["description"] = description_element.text.strip()
                    except NoSuchElementException:
                        project["description"] = ""
                    
                    projects.append(project)
        except Exception as e:
            logger.error(f"Error extracting projects: {str(e)}")
        
        return projects
    
    def _extract_languages(self) -> List[Dict[str, str]]:
        """Extract languages from the profile"""
        languages = []
        
        try:
            lang_section = self._driver.find_elements(By.CSS_SELECTOR, "section.pv-accomplishments-block.languages")
            
            if lang_section:
                # Try to expand languages section
                expand_button = lang_section[0].find_elements(By.CSS_SELECTOR, "button.pv-accomplishments-block__expand")
                if expand_button:
                    expand_button[0].click()
                    time.sleep(1)
                
                lang_items = lang_section[0].find_elements(By.CSS_SELECTOR, "li.pv-accomplishment-entity")
                
                for item in lang_items:
                    language = {}
                    
                    # Language name
                    try:
                        lang_text = item.text.strip()
                        parts = lang_text.split('\n')
                        
                        if len(parts) >= 1:
                            language["name"] = parts[0].strip()
                        
                        if len(parts) >= 2:
                            language["proficiency"] = parts[1].strip()
                        else:
                            language["proficiency"] = ""
                    except Exception:
                        language["name"] = item.text.strip()
                        language["proficiency"] = ""
                    
                    languages.append(language)
        except Exception as e:
            logger.error(f"Error extracting languages: {str(e)}")
        
        return languages
    
    def _extract_interests(self) -> List[str]:
        """Extract interests from the profile"""
        interests = []
        
        try:
            interests_section = self._driver.find_elements(By.CSS_SELECTOR, "section.pv-interests-section")
            
            if interests_section:
                interest_items = interests_section[0].find_elements(By.CSS_SELECTOR, "li.pv-interest-entity")
                
                for item in interest_items:
                    try:
                        interest_name = item.find_element(By.CSS_SELECTOR, "span.pv-entity__summary-title-text").text.strip()
                        interests.append(interest_name)
                    except NoSuchElementException:
                        continue
        except Exception as e:
            logger.error(f"Error extracting interests: {str(e)}")
        
        return interests
    
    def __del__(self):
        """Clean up resources"""
        if self._driver:
            self._driver.quit() 