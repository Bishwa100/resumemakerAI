from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators

from langchain_mistralai import ChatMistralAI
from crewai_tools import SerperDevTool, ScrapeWebsiteTool
import getpass
import os

if "MISTRAL_API_KEY" not in os.environ:
    os.environ["MISTRAL_API_KEY"] = getpass.getpass(os.environ["MISTRAL_API_KEY"])

llm = ChatMistralAI(
    model="mistral-medium-latest",
    temperature=0,
    max_retries=2,
)

@CrewBase
class DataExtraction:
    """Data Extraction"""
    agents_config = "config/data_extraction_agents.yaml"
    tasks_config = "config/data_extraction_tasks.yaml"

    # If you would lik to add tools to your crew, you can learn more about it here:
    # https://docs.crewai.com/concepts/agents#agent-tools
    
    @agent
    def data_extraction_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["data_extraction_agent"],
            llm= llm
        )
    @agent
    def data_extraction_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["data_extraction_agent"],
            llm= llm,
            verbose= 2,
            tools=[SerperDevTool(), ScrapeWebsiteTool()]
        )

    # To learn more about structured task outputs,
    # task dependencies, and task callbacks, check out the documentation:
    # https://docs.crewai.com/concepts/tasks#overview-of-a-task
    @task
    def write_poem(self) -> Task:
        return Task(
            config=self.tasks_config["write_poem"],
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Research Crew"""
        # To learn how to add knowledge sources to your crew, check out the documentation:
        # https://docs.crewai.com/concepts/knowledge#what-is-knowledge

        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
        )
