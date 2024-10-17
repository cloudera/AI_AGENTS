from textwrap import dedent
from typing import Dict

from crewai import Task, Agent
from pydantic import BaseModel, Field, field_validator

from aiagents.config import Initialize


class Tasks:
    def __init__(self, configuration: Initialize, agents: Dict[str, Agent]) -> None:
        # self.splitter_task = Task(
        #     description=dedent(
        #         """
        #         Find all the swagger files present in the target swagger directory and then split each swagger file.
        #         * If the folder called 'generated' is already present, consider this task as complete, and take no 
        #         further actions.
        #         * If the generated folder is not present, run the swagger splitter tool.
                
        #         Make no assumptions whatsoever.
        #         """
        #     ),
        #     expected_output="A concise answer stating the exact location of all the generated swagger metadata files.",
        #     agent=agents["swagger_splitter_agent"],
        # )

        class metadata_summaries(BaseModel):
            summaries: dict[str, str]

        self.metadata_summarizer_task = Task(
            description=dedent(
                f"""
                Trigger the 'summary_generator' tool. This tool will automatically pick up the necessary swagger files
                from the {configuration.generated_folder_path}, and generate a summary for each of them. It outputs a structured
                k:v pair json, where the key is the location of the summarized swagger file, and the value is 
                the generated summary.

                If the metadata summary has already been generated, consider this task as complete, and take no 
                further actions.

                Make no assumptions whatsoever.
                """
            ),
            expected_output="A concise answer stating the exact location of the final generated metadata summary file.",
            agent=agents["metadata_summarizer_agent"],
            output_json=metadata_summaries,
            output_file=f"{configuration.generated_folder_path}/metadata_summaries",
            # context=[self.splitter_task],
        )

        self.initial_human_input_task = Task(
            description=dedent(
                """
                Ask the human what action they would like to perform using the swaggers they have provided.
                """
            ),
            expected_output=dedent(
                """
                A clear answer stating the user action EXACTLY as they have mentioned within quotes, 
                and please don't change or miss a single word they have provided.
                """
            ),
            agent=agents["human_input_agent"],
        )

        class taskMatcherDecision(BaseModel):
            """
            This class is used to store the decision made by the task matcher agent. It has several fields:
            - file_name: The file name of the appropriate swagger metadata file chosen.
            - file_location: The path or location of the appropriate swagger metadata file chosen.
            - task: The task at hand for which the swagger file was chosen.
            - reason: The reasoning behind why the task matcher agent has decided to use this particular swagger metadata file.
            - description: The description of this class used to identify the output
            """

            file_name: str
            file_location: str
            task: str
            reason: str
            description: str = Field("This output contains the appropriate swagger metadata file to use for the task at hand", frozen=True)

            @field_validator('description')
            def set_fixed_method(cls, v):
                return "This output contains the appropriate swagger metadata file to use for the task at hand"

        self.task_matching_task = Task(
            description=dedent(
                """
                Complete the following steps:
                1. Fetch Metadata Summary:
                    1. Use the 'file read tool' to retrieve the metadata summary file. Ensure the contents are fully loaded before proceeding.
                2. Identify the Relevant Swagger File:
                    1. Review the metadata file, which consists of key-value pairs where each key is the path of a Swagger file and each value is a summary.
                    2. Based on the context provided by the human input task, analyze the summaries to determine which Swagger file aligns best with the task requirements.
                3. Infer the Best Swagger File:
                    1. Critical step: If the summaries are unclear or do not directly indicate the appropriate Swagger file, make a logical assumption based on the descriptions and your understanding of the task.
                    2. Prioritize selecting the Swagger file that most closely matches the user's query and the context of the task.
                4. Confirm with the User (Optional):
                    1. If multiple API options are available, or if you are uncertain about your choice, use the 'get_human_input' tool to confirm your decision with the user.
                    2. Provide a clear explanation of why you selected this particular Swagger API.
                    3. If only one option exists or you are highly confident, you can skip this step and proceed directly.
                5. Return Swagger Metadata Location:
                    1. Once the appropriate Swagger file is identified, format the result in the exact structure required by the 'taskMatcherDecision' class.
                    2. Include the description: "This output contains the appropriate swagger metadata file to use for the task at hand."
                    3. Finish execution.
                """
            ),
            expected_output="A concise answer stating the exact location of the appropriate swagger metadata file, "
            """as well as the reason why it is the one that has been chosen. The output should be of the structure 
            of the taskMatcherDecision class. It has several fields:
                - file_name: The file name of the appropriate swagger metadata file chosen.
                - file_location: The path or location of the appropriate swagger metadata file chosen.
                - task: The task at hand for which the swagger file was chosen.
                - reason: The reasoning behind why the task matcher agent has decided to use this particular swagger metadata file.
                - description: The description of this class which will be used to identify the output = 'This output contains 
                the appropriate swagger metadata file to use for the task at hand'
            """,
            output_json=taskMatcherDecision,
            agent=agents["task_matching_agent"],
            context=[self.metadata_summarizer_task, self.initial_human_input_task],
        )

        self.validator_task = Task(
            description=dedent(
                """
                Follow the below steps:
                1. Understand the Original Query:
                    1. Carefully review the original query that was passed to the agent requesting validation. Pay close attention to its nuances, ensuring you grasp the user’s intent and expectations.
                2. Evaluate the Agent's Proposed Answer:
                    1. Analyze the response provided by the agent seeking validation. Understand the exact outcome that will be produced based on its actions.
                3. Assess the Outcome:
                    1. Based on your understanding of both the original query and the proposed answer, determine whether the agent's actions will satisfactorily fulfill the user's request. Consider potential gaps or mismatches.
                4. Provide a Conclusion:
                    1. Clearly state whether the agent's proposed solution will result in successful task completion.
                    2. Justify your conclusion with a concise explanation, detailing why the actions are or are not aligned with the original query.
                    3. Communicate your decision to the calling agent so it can proceed with the rest of its tasks accordingly.
                """
            ),
            expected_output=dedent(
                """
                Output the conclusion and reasoning as to whether or not the action of the agent will result in the 
                original query posed to the agent to be addressed
                """
            ),
            agent=agents["validator_agent"],
            context=[self.metadata_summarizer_task],
        )

        class managerDecision(BaseModel):
            """
            This class is used to store the decision made by the manager agent. It has several fields:
            - endpoint: The endpoint that the manager agent has decided needs to be used.
            - method: The HTTP method that the manager agent has decided needs to be used.
            - file: The location of the split metadata file associated with the endpoint..
            - user_query: The original user query verbatim.
            - reasoning: The reasoning behind why the manager agent has decided to use this particular endpoint and method .
            """

            endpoint: str
            method: str
            file: str
            user_query: str
            reasoning: str

        self.manager_task = Task(
            description=dedent(
                """
                Follow the following steps:
                1. Read the Metadata File:
                    1. Use the 'file read tool' to retrieve the contents of the metadata file. The file location should be extracted from the 'task matcher' task’s context.
                2. Select Endpoint and HTTP Method:
                    1. Analyze the contents of the metadata file to determine the most appropriate API endpoint and HTTP method.
                    2. Match the user’s query to the endpoint descriptions by comparing the similarity between the user’s intent and the endpoint’s functionality.
                3. Justify Your Choice:
                    1. Present the selected endpoint and HTTP method along with a well-reasoned justification to the 'validator agent'. Ensure your explanation aligns with the user’s original query to demonstrate how it satisfies their request.
                4. Respond to Validator Feedback:
                    1. If the 'validator agent' provides suggestions for improvement, revise your selection as needed based on the feedback.
                    2. Seek validation again after making adjustments.
                5. Output Approved Data:
                    1. Once the 'validator agent' confirms your endpoint and method choice, return the following:
                        1. The file field associated with the approved endpoint.
                        2. The original user query in verbatim form.
                """
            ),
            expected_output=dedent(
                """
                The output should be of the structure of the managerDecision class. It has several fields:
                    - endpoint: The endpoint that the manager agent has decided needs to be used.
                    - method: The HTTP method that the manager agent has decided needs to be used.
                    - file: The location of the split metadata file associated with the endpoint..
                    - query: The original user query verbatim.
                    - reasoning: The reasoning behind why the manager agent has decided to use this particular endpoint and method .
                """
            ),
            output_json=managerDecision,
            context=[
                self.task_matching_task,
                self.initial_human_input_task,
                self.validator_task,
            ],
            agent=agents["manager_agent"],
        )

        self.api_calling_task = Task(
            description=dedent(
                """
                Complete the following steps to make the API call, using the context obtained from the manager_task:
                1. Identify the API Call:
                    1. Using the context from the 'manager_task', locate the Swagger metadata file to identify the API endpoint required by the user. The full path for the API call file can be constructed by combining the manager task details with the '{configuration.generated_folder_path}'.
                2. Determine Parameters:
                    1. Review the Swagger file to extract both required and optional parameters for the API call.
                    2. Provide the user with a well-formatted list of these parameters:
                        1. Required parameters: Specify which parameters are mandatory for the call to succeed and give a brief description of each.
                        2. Optional parameters: List optional parameters with a short description, indicating they are not necessary for the basic functionality but can provide extra control.
                3. Request Missing Information:
                    1. If any required parameters are missing, ask the user to provide the necessary values. Be polite yet clear when prompting for required parameters.
                    2. If the user omits optional parameters, proceed without them unless instructed otherwise.
                4. Fetch Additional Information (if needed):
                    1. If the user’s request requires more information (such as unavailable details or references), communicate with the 'API Selector' for further clarification or additional API calls.
                    2. Relay any retrieved information back to the user in a structured, easy-to-read format.
                5. Build and Confirm Payload:
                    1. Construct the final payload for the API call, including the required and optional parameters. Display the constructed payload to the user, ensuring they review and confirm it before proceeding.
                6. Execute the API Call:
                    1. Trigger the 'api_caller' tool to execute the API call with the payload. Handle any errors that arise:
                        1. Handle Errors: If an error occurs, attempt to diagnose and resolve it yourself. If user input or clarification is necessary, ask for it.
                7. Return Results:
                    1. Once the API call is successful, return the output to the user. If needed, summarize the result in a clear and concise manner for easy understanding.
                8. Completion & Further Instructions:
                    1. After delivering the outcome, prompt the user with the following message: “Please reload the crew if you have any further queries.”
                    2. Conclude the task execution unless further actions are required by the user.
                """
            ),
            expected_output=dedent(
                """
                Output the result of the API call talking about the action that has been taken in a concise manner.
                """
            ),
            agent=agents["api_caller_agent"],
            context=[self.initial_human_input_task, self.manager_task],
        )
