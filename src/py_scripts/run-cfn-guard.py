import sys
import re
import subprocess
from subprocess import PIPE
from junit_xml import TestSuite, TestCase
import logging
from logging.config import dictConfig
from os import listdir
from os.path import isfile, join
from os import walk
import os

cfn_guard_binary_path = "./cloudformation-guard/bin/cfn-guard"
template_path = "./src/templates"
rule_set_path = "./src/cfn-guard/rule-sets"


def get_cfn_guard_command_template():
    """
    Returns the command template that invokes CloudFormation guard

    Parameters
    ----------
    None

    Raises
    ------
    None

    Returns
    -------
    cfn_guard_command_template : str
        The command template that defines how CloudFormation guard is used.

    See Also
    --------
    Official Docs: https://github.com/aws-cloudformation/cloudformation-guard
    CloudFormation Guard Rulegen as a Lambda: https://github.com/aws-cloudformation/cloudformation-guard/blob/master/cfn-guard-rulegen-lambda/README.md

    Examples
    --------
    >>> get_cfn_guard_command_template()
    '{cfn_guard_binary_path} check -v -r {rule_set_path} -t {template_path}'

    """
    return "{cfn_guard_binary_path} check -v -r {rule_set_path} -t {template_path}"


def validate_cloudformation_template(
    template_path, rule_set_path, cfn_guard_binary_path
):
    """
    Validates the given CloudFormation template using the ruleset provided. 

    Parameters
    ----------
    template_path : str
        Relative or absolute file path to the target AWS CloudFormation template.
    rule_set_path : str
        Relative or absolute file path to the ruleset against which the AWS CloudFormation template will be examined.
    cfn_guard_binary_path : str

    Raises
    ------
    None

    Returns
    -------
    STDOUT of the CloudFormation Guard command that is invoked using the subprocess module.

    See Also
    --------
    subprocess: https://docs.python.org/3/library/subprocess.html

    Examples
    --------
    >>> validate_cloudformation_template("./src/templates/example.json", "./src/cfn-guard/rulesets/baseline.ruleset", "./cloudformation-guard/bin/cfn-guard")
    """
    command = get_cfn_guard_command_template().format(
        template_path=template_path,
        rule_set_path=rule_set_path,
        cfn_guard_binary_path=cfn_guard_binary_path,
    )
    cfn_guard_command_output = subprocess.run(command.split(" "), stdout=PIPE)
    if cfn_guard_command_output.returncode == 0:
        print("Evaluation complete; no findings to report.")
    else:
        print("Evaluations complete; findings obtained.")
    return cfn_guard_command_output


def get_file_list_in_directory(directory_path):
    """
    Retrieves all the files in a given directory. Note: This function does not retrieve nested files/directories. 

    Parameters
    ----------
    directory_path : str
        Relative or absolute path to the directory whose files need to be retrieved.

    Raises
    ------
    None

    Returns
    -------
    List of file paths that are present in the given directory.

    Examples
    --------
    >>> get_file_list_in_directory("/tmp")
    ['/tmp/test.txt', '/tmp/cfn.yaml']
    """
    return [
        join(directory_path, f)
        for f in listdir(directory_path)
        if isfile(join(directory_path, f))
    ]


def validate_cloudformation_templates(
    directory_path, rule_sets_path, cfn_guard_binary_path
):
    """
    Validates all AWS CloudFormation templates present in a given directory against all the rulesets provided using CloudFormation Guard.

    Parameters
    ----------
    directory_path : str
        Absolute or relative path to the directory that contains the AWS CloudFormation templates.
    rule_sets_path : str
        Absolute or relative path to the directory that contains all the CloudFormation Guard rulesets.
    cfn_guard_binary_path : str
        Absolute or relative path to the CloudFormation Guard binary.

    Raises
    ------
    None

    Returns
    -------
    List of evaluations from the `validate_cloudformation_template` function.

    Examples
    --------
    >>> validate_cloudformation_templates("/tmp/cfn_folder", "/tmp/ruleset", "/cloudformation-guard/bin/cfn-guard")
    """
    cfn_guard_output = []
    for cloudformation_template in get_file_list_in_directory(directory_path):
        for rule_set in get_file_list_in_directory(rule_sets_path):
            cfn_guard_output.append(
                {
                    "Output": validate_cloudformation_template(
                        cloudformation_template, rule_set, cfn_guard_binary_path
                    ),
                    "Template": cloudformation_template,
                    "RuleSet": rule_set,
                }
            )
    return cfn_guard_output


def generate_test_case(command_output, cloudformation_template_file_path, rule_set):
    """
    Creates a test case for each evaluation of CloudFormation Guard.

    Parameters
    ----------
    command_output : obj of subprocess.CompletedProcess
        Object of the subprocess.CompletedProcess class
    cloudformation_template_file_path : 
        Absolute or relative path to the CloudFormation template that was evaluated.
    rule_set : 
        Absolute or relative path to the CloudFormation Guard ruleset that was used for evaluation.

    Raises
    ------
    None

    Returns
    -------
    Object of TestCase

    """
    if command_output.returncode == 0:
        return TestCase(
            rule_set,
            cloudformation_template_file_path,
            1,
            "Successfully evaluated all resources",
            "",
        )
    else:
        for line in command_output.stdout.decode().split("\n"):
            if "failed" in line:
                resource_name = (
                    line.split("failed because")[0]
                    .replace(" ", "")
                    .replace("[", "")
                    .replace("]", "")
                )
                result = line.split("failed because")[1]
                tc = TestCase(rule_set, resource_name, 0, "", "")
                tc.add_failure_info(result)
                return tc


def generate_test_report(cfn_guard_output_list):
    """
    Generates a test report that contains the collection of test cases generated for each CloudFormation Guard execution and writes it to a file: "output.xml".

    Parameters
    ----------
    cfn_guard_output_list : list
        List of evaluations from the `validate_cloudformation_template` function.

    Returns
    -------
    None
    """
    test_cases = []
    for output in cfn_guard_output_list:
        test_cases.append(
            generate_test_case(output["Output"], output["Template"], output["RuleSet"])
        )
    test_suite = TestSuite("clouformation-guard tests", test_cases)
    print(TestSuite.to_xml_string([test_suite]))
    with open("output.xml", "w") as f:
        TestSuite.to_file(f, [test_suite], prettyprint=False)
    return None


if __name__ == "__main__":
    cfn_guard_output_list = validate_cloudformation_templates(
        template_path, rule_set_path, cfn_guard_binary_path
    )
    generate_test_report(cfn_guard_output_list)
