# Currency-exchange


## Application details

This application is designed to get currency exchange rate data from the European Central Bank and store it in AWS DynamoDB. 
And we can get difference between the rates of currency for the current and previous day via API.


## Instructions to setup

- Make sure you have AWS CLI installed and setup with profile named `exchange-rates-profile` and default region `us-east-1`
- If you do not have AWS CLI installed the follow the following AWS CLI Configuration Guide.
### AWS CLI Configuration Guide

This guide provides step-by-step instructions to configure the AWS Command Line Interface (CLI) on your local machine.

#### Prerequisites

- Ensure you have Python 3.9 or higher installed. You can download Python from the [official website](https://www.python.org/downloads/).
- Install `pip`, the Python package installer. It usually comes bundled with Python, but you can also install it separately if needed.


You can install AWS CLI using `pip`. Open your terminal and run the following command:

```sh
pip install awscli
```
If you are using **macOS:**

**Install using Homebrew:** Open Terminal and run the following command Homebrew will download and install the AWS CLI.

```sh
brew install awscli
```

To verify the installation, run following command

```sh
aws --version
```
Once AWS CLI is installed, you need to configure it with your AWS credentials and default settings and profile required for this application. Run the following command in your terminal.

```sh
aws --profile exchange-rates-profile
```
You will be prompted to enter the following information:

- **AWS Access Key ID:** ```<Your access key ID>```
- **AWS Secret Access Key:** ```<Your secret access key>```
- **Default region name:** ```us-east-1```
- **Default output format:** ```json``` The format in which you want the AWS CLI to return your output (e.g., json, text, table).

You can obtain your AWS Access Key ID and Secret Access Key from the [AWS Management Console](https://console.aws.amazon.com/iam/home?#/security_credential) under the "Access keys" section.

### Installing code repo and requirements
Once done with AWS CLI, now you need to clone the code repo and install requirements. 

**Clone the Repository**
```bash
git clone https://github.com/hassamhassan/currency-exchange.git
cd currency-exchange
```
**Install Requirements**

```bash
pip install -r requirements.txt
```
install other minor dependency for executing bash script.

Run the following command
```sh
brew install jq
```


## Run Test Cases

For Pytest test cases run the following command from project root directory i-e `currency-exchange`

```shell
pytest -vv
```

## Deployment
This script orchestrates the full deployment process.
```bash
sh scripts/deployment.sh
```

## REST API Endpoint Details
GET /delta: Returns JSON with current rates and delta to the previous rates.
### Request
```bash
curl -X GET https://<API-ID>.execute-api.us-east-1.amazonaws.com/dev/delta
```

### Example Response
```json
{
  "present_rates": {
    "NZD": 12.2,
    "USD": 3.77
  },
  "delta": {
    "NZD": 0.3,
    "USD": -1.3
  }
}
```



