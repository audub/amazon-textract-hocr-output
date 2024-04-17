# Amazon Textract to hOCR
Convert your Amazon Textract results to hOCR output. 

Forked from 
aws-samples/amazon-textract-hocr-output

### Usage Instructions

The code necessary for transforming Amazon Textract text extraction results to hOCR output is located in code/hocrOuput.py.

To make the code work you will need to install the following packages via pip:
- [Yattag](https://www.yattag.org/download-install) package (used for HTML generation)
- [Textract-Caller](https://github.com/aws-samples/amazon-textract-textractor/tree/master/caller) to make calls to Amazon Textract

Create a virtual environment and install requirements: 

```
pip install -r requirements.txt
```

Run the script:

```
python3 ../code/hocrOuput.py <path>.jpg
```

or to process many, do something like: 

```
find ~/Downloads/files/ -type f -name "*.jpg" | xargs -P 4 -I {} python3 ../code/hocrOuput.py {}
```

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.

