from pathlib import Path
from os.path import join
from os import environ
from aiagents.custom_threading import threads

from dotenv import load_dotenv, find_dotenv

from langchain_openai import AzureChatOpenAI, ChatOpenAI
import panel as pn


class Initialize:

    diagrams = {
        "full": "0_fulll.jpg",
        "Human Input Agent": "1_human_inputt.jpg",
        "get_human_input": "get_human_input.jpg",
        "Input Matcher": "2_task_matcherr.jpg",
        # "Swagger API Description Summarizer": "3_metadata_summariser.jpg",
        # "swagger_splitter": "4_swagger_splitter.jpg",
        "API Selector Agent": "3_api_selectorr.jpg",
        "Decision Validator Agent": "4_decision_validatorr.jpg",
        # "API Caller Agent": "7_api_caller.jpg",
        "api_caller": "api_tool.jpg",
    }

    def __init__(self):
        current_file_path = Path(__file__).resolve()
        project_root = str(current_file_path.parents[2])

        environ["PROJECT_ROOT"] = project_root

        self.project_root = environ.get("PROJECT_ROOT")
        self.app_port = int(environ.get("CDSW_APP_PORT", "8080"))

        self.swagger_files_directory = environ.get(
            "SWAGGER_FILES_DIRECTORY", f"{self.project_root}/swagger_files"
        )
        self.generated_folder_path = join(self.swagger_files_directory, "generated")
        self.metadata_summaries_path = join(
            self.generated_folder_path, "summaries", "metadata_summaries"
        )
        self.openai_provider = "AZURE_OPENAI"
        self.selected_swagger_file = ""
        self.user_input = None
        self.first_run = pn.Param.param
        self.current_agent = "" 
        self.new_file_name = ""

        self.sidebar: pn.Column = None
        self.metadata_summarization_status = pn.widgets.TextInput(value="")
        self.processing_file = False
        self.empty_inputs = True
        self.chat_interface: pn.chat.ChatInterface = None
        self.spinner: pn.indicators.LoadingSpinner = None
        self.initialization_spinner: pn.indicators.LoadingSpinner = None
        self.reload_button: pn.widgets.Button = None

        self.customInteractionCallbacks = []
        self.customInitializationCallbacks = []
        self.diagram_path = f"{self.project_root}/assets/images"
        self.active_diagram = pn.widgets.TextInput(
            value=f"{self.diagram_path}/{self.diagrams['full']}"
        )
        self.avatar_images = {
            "Human Input Agent": f"{self.diagram_path}/human_input_agent.svg",
            "API Selector Agent": f"{self.diagram_path}/api_selector_agent.jpg",
            "Decision Validator Agent": f"{self.diagram_path}/decision_validator_agent.jpg",
            # "API Caller Agent": f"{self.diagram_path}/api_caller_agent.jpg",
            "Input Matcher": f"{self.diagram_path}/task_matcher_agent.jpg",
            # "Swagger API Description Summarizer": f"{self.diagram_path}/metadata_summarizer_agent.jpg",
            # "swagger_splitter": f"{self.diagram_path}/swagger_splitter_agent.jpg",
        }
        self.chat_styles={
            "font-size": "0.87rem",
            "background-color": "#f9fefe",
            "min-height": "2.5rem"
        }
        self.initialization_crew_thread: threads.thread_with_trace = None
        self.crew_thread: threads.thread_with_trace = None
        self.upload_button: pn.widgets.Button = None

    def update_configuration(self):
        load_dotenv(find_dotenv(), override=True)

        print("openai provider:", self.openai_provider)
    
        self.llm = AzureChatOpenAI(azure_deployment=environ.get(
            "AZURE_OPENAI_DEPLOYMENT", "cml"
        )) if self.openai_provider == "AZURE_OPENAI" else ChatOpenAI()
        self.llm.temperature = float(environ.get("LLM_TEMPERATURE", 0.1))
        print("LLM temperature: ", self.llm.temperature)

    def update_config_upload(self):
        load_dotenv(find_dotenv(), override=True)

        print("openai provider:", self.openai_provider)
    
        self.llm = AzureChatOpenAI(azure_deployment=environ.get(
            "AZURE_OPENAI_DEPLOYMENT", "cml"
        )) if self.openai_provider == "AZURE_OPENAI" else ChatOpenAI()
        self.llm.temperature = float(environ.get("LLM_TEMPERATURE", 0.1))
        print("LLM temperature: ", self.llm.temperature)


global configuration
configuration = Initialize()
