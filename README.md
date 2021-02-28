# LatestLayerVersion AWS CloudFormation macro

This AWS CloudFormation lambda-powered [macro](cfn-macros) is invoked by CloudFormation when deploying your templates. It returns the ARN of the latest AWS LayerVersion available, based on a `LayerVersion` name or `LayerVersion` ARN.

## Getting Started

### Example of use

You can invoke the `LatestLayerVersion` macro using `Fn::Transform`, as follows:

```yaml
MyLambdaFunction:
  Type: AWS::Serverless::Function
  Properties:
    FunctionName: MyLambdaFunction
    ...
    Layers:
      - Fn::Transform:
          Name: LatestLayerVersion
          Parameters:
            LayerName: MyLambdaLayer
    MemorySize: 128
    Timeout: 300
```

Assuming that `MyLambdaLayer` has 5 versions, as it is deployed, your CloudFormation template will be templated as follows:

```yaml
MyLambdaFunction:
  Type: AWS::Serverless::Function
  Properties:
    FunctionName: MyLambdaFunction
    ...
    Layers:
      - arn:aws:lambda:<aws_region>:<aws_account_id>:layer:MyLambdaLayer:5
    MemorySize: 128
    Timeout: 300
```

### Macro parameters

When using `Fn::Transform`, you can/must pass any of the following parameters:

| Parameter name | Type | Required | Description |
| -------------- | -----| -------- | ----------- |
| LayerName      | String or List (will be concatenated) | True | The name or Amazon Resource Name (ARN) of the layer. <br/> It can be any for the following formats: <br/> - Name: `MyLambdaLayer` <br/> - ARN: `arn:aws:lambda:us-west-2:111122223333:layer/MyLambdaLayer` <br/> - LayerVersionARN: `arn:aws:lambda:us-west-2:111122223333:layer/MyLambdaLayer:1` <br/>  |
| CompatibleRuntime | String or List (will be concatenated) | False | A runtime identifier. For example, `go1.x`. |


## Installation

### Software prerequisites

- **AWS CLI** (1.17.14+);
- **Python** (3.8.2+);
  - **boto3** (1.16.8+);
- **SAM CLI** (0.47.0+).

### CloudFormation configuration

#### Required capabilities

- `CAPABILITY_NAMED_IAM`:
  This stack template(s) include resources that affect permissions in your AWS account (e.g. creating new AWS Identity and IAM users). You must explicitly acknowledge this by specifying this capability.

#### Template parameters

| Parameter name | Type | Default | AllowedValues | Description |
| -------------- | -----| ------- | ------------- | ----------- |
| MacroName      | String | LatestLayerVersion |              | The name of the macro. The name of the macro must be unique across all macros in the account. This property is passed directly to the `Name` property of an `AWS::CloudFormation::Macro` resource. |
| KmsKeyArn      | String | NONE | If set, must match a KMS Key ARN. Example: `arn:aws:kms:us-west-2:111122223333:key/1234abcd-12ab-34cd-56ef-1234567890ab` | If set, will be used to encrypt the AWS Lambda log group. |

#### Deploying the application

This assumes your AWS CLI environment is properly configured.


- From the project root directory, run the AWS SAM CLI to build and deploy the Cloudformation application. It is recommended to use the `--guided` option in order to configure the application deployment, including template parameters:

  ```sh
  sam build
  sam deploy --guided --capabilities "CAPABILITY_NAMED_IAM"
  ```

- You will be prompt with a selection menu, generating a configuration recap as follows:

  ```sh
  Deploying with following values
  ===============================
  Stack name                   : macro-layer-latest-version
  Region                       : eu-west-1
  Confirm changeset            : True
  Deployment s3 bucket         : <your_cfn_deployment_bucket>
  Capabilities                 : ["CAPABILITY_NAMED_IAM"]
  Parameter overrides          : {"MacroName": "LatestLayerVersion", "KmsKeyArn": "NONE"}
  Signing Profiles             : {}
  ```

- Deploy the application to your AWS account by confirming the Cloudformation changeset.

[cfn-macros]: https://docs.aws.amazon.com/AWSCloudFormation/latest/
